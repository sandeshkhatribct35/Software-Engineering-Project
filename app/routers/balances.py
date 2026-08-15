"""Balance, settlement-plan and summary endpoints.

These endpoints read aggregates from the repository layer and hand them to the
pure services; no arithmetic happens in this module.
"""

from http import HTTPStatus

from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.constants import API_PREFIX
from app.repositories import balances as balances_repo
from app.repositories import expenses as expenses_repo
from app.repositories import groups as groups_repo
from app.repositories import members as members_repo
from app.routers import DbSession, error_responses
from app.schemas.balance import (
    GroupBalances,
    GroupSummary,
    MemberBalance,
    MemberSummary,
    SettlementPlan,
    Transfer,
)
from app.services import settlement_plan
from app.services.balances import compute_balances
from app.services.money import total

router = APIRouter(prefix=f"{API_PREFIX}/groups", tags=["balances"])


@router.get(
    "/{group_id}/balances",
    response_model=GroupBalances,
    summary="Get member balances",
    description=(
        "Returns each member's net position: what they have paid, minus what they "
        "owe, adjusted by settlements already made. Positive means the group owes "
        "the member. The balances of a group always sum to zero."
    ),
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def get_balances(group_id: int, db: DbSession) -> GroupBalances:
    """Return the net balance of every member of the group."""
    group = groups_repo.get_or_404(db, group_id)
    names = _member_names(db, group.id)
    balances = compute_balances(balances_repo.member_totals(db, group.id))
    return GroupBalances(
        group_id=group.id,
        currency=group.currency,
        balances=[
            MemberBalance(member_id=member_id, member_name=names[member_id], balance=balance)
            for member_id, balance in balances.items()
        ],
    )


@router.get(
    "/{group_id}/settlement-plan",
    response_model=SettlementPlan,
    summary="Get the settlement plan",
    description=(
        "Returns the payments that clear every debt in the group, matching the "
        "largest debtor with the largest creditor. A group of n members needs at "
        "most n-1 payments; a settled group returns an empty plan."
    ),
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def get_settlement_plan(group_id: int, db: DbSession) -> SettlementPlan:
    """Return the minimal set of transfers that settles the group."""
    group = groups_repo.get_or_404(db, group_id)
    names = _member_names(db, group.id)
    balances = compute_balances(balances_repo.member_totals(db, group.id))
    transfers = settlement_plan.suggest_settlements(balances)
    return SettlementPlan(
        group_id=group.id,
        currency=group.currency,
        transfers=[
            Transfer(
                from_member_id=transfer.from_member_id,
                from_member_name=names[transfer.from_member_id],
                to_member_id=transfer.to_member_id,
                to_member_name=names[transfer.to_member_id],
                amount=transfer.amount,
            )
            for transfer in transfers
        ],
        transfer_count=len(transfers),
    )


@router.get(
    "/{group_id}/summary",
    response_model=GroupSummary,
    summary="Get a group summary",
    description="Returns totals for the group and for each member within it.",
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def get_summary(group_id: int, db: DbSession) -> GroupSummary:
    """Return aggregate spending information for the group."""
    group = groups_repo.get_or_404(db, group_id)
    names = _member_names(db, group.id)
    totals = balances_repo.member_totals(db, group.id)
    balances = compute_balances(totals)
    return GroupSummary(
        group_id=group.id,
        group_name=group.name,
        currency=group.currency,
        member_count=len(names),
        expense_count=expenses_repo.count_for_group(db, group.id),
        total_spend=total(member.total_paid for member in totals),
        members=[
            MemberSummary(
                member_id=member.member_id,
                member_name=names[member.member_id],
                total_paid=member.total_paid,
                total_owed=member.total_owed,
                balance=balances[member.member_id],
            )
            for member in totals
        ],
    )


def _member_names(db: Session, group_id: int) -> dict[int, str]:
    """Return the name of every member of the group, keyed by member id."""
    return {member.id: member.name for member in members_repo.list_for_group(db, group_id)}
