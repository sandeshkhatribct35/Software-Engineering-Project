"""Expense endpoints.

This module owns one piece of real decision-making: turning a create request
into a set of per-member shares. Membership is checked here because it needs the
database; the arithmetic itself is delegated to the pure splitting service.
"""

from collections.abc import Iterable
from decimal import Decimal
from http import HTTPStatus

from fastapi import APIRouter, Query

from app.constants import API_PREFIX, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, SplitType
from app.errors import ParticipantNotInGroupError, PayerNotInGroupError
from app.models.expense import Expense
from app.repositories import expenses as expenses_repo
from app.repositories import groups as groups_repo
from app.repositories import members as members_repo
from app.routers import DbSession, error_responses
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseShareRead
from app.services.splitting import split_equally, validate_exact_shares

router = APIRouter(prefix=API_PREFIX, tags=["expenses"])


@router.post(
    "/groups/{group_id}/expenses",
    response_model=ExpenseRead,
    status_code=HTTPStatus.CREATED,
    summary="Record an expense",
    description=(
        "Records a shared expense. An EQUAL split divides the amount between the "
        "listed participants, giving the indivisible remainder to the lowest member "
        "ids first. An EXACT split takes the amount owed by each member and is "
        "rejected unless those amounts add up to the expense total."
    ),
    responses=error_responses(HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY),
)
def create_expense(group_id: int, payload: ExpenseCreate, db: DbSession) -> ExpenseRead:
    """Validate the participants, split the amount and store the expense."""
    group = groups_repo.get_or_404(db, group_id)
    group_member_ids = members_repo.member_ids(db, group.id)

    if payload.paid_by_id not in group_member_ids:
        raise PayerNotInGroupError(
            f"Member {payload.paid_by_id} does not belong to group {group_id}"
        )

    shares = _resolve_shares(payload, group_member_ids)

    expense = expenses_repo.create(
        db,
        group=group,
        description=payload.description,
        amount=payload.amount,
        paid_by_id=payload.paid_by_id,
        split_type=payload.split_type,
        shares=shares,
    )
    return _to_expense_read(expense)


@router.get(
    "/groups/{group_id}/expenses",
    response_model=list[ExpenseRead],
    summary="List expenses",
    description="Returns a page of the group's expenses, newest first.",
    responses=error_responses(HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY),
)
def list_expenses(
    group_id: int,
    db: DbSession,
    limit: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Maximum number of expenses to return.",
    ),
    offset: int = Query(default=0, ge=0, description="Number of expenses to skip."),
) -> list[ExpenseRead]:
    """Return one page of a group's expenses."""
    group = groups_repo.get_or_404(db, group_id)
    expenses = expenses_repo.list_for_group(db, group.id, limit=limit, offset=offset)
    return [_to_expense_read(expense) for expense in expenses]


@router.get(
    "/expenses/{expense_id}",
    response_model=ExpenseRead,
    summary="Get an expense",
    description="Returns a single expense with the full breakdown of who owes what.",
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def get_expense(expense_id: int, db: DbSession) -> ExpenseRead:
    """Return one expense and its shares."""
    return _to_expense_read(expenses_repo.get_or_404(db, expense_id))


@router.delete(
    "/expenses/{expense_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Delete an expense",
    description="Deletes an expense and its shares; balances change immediately.",
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def delete_expense(expense_id: int, db: DbSession) -> None:
    """Delete an expense together with its shares."""
    expenses_repo.delete(db, expenses_repo.get_or_404(db, expense_id))


def _resolve_shares(payload: ExpenseCreate, group_member_ids: set[int]) -> dict[int, Decimal]:
    """Produce the amount owed by each participant for either split strategy."""
    if payload.split_type is SplitType.EQUAL:
        participant_ids = payload.participant_ids or []
        _require_all_in_group(participant_ids, group_member_ids)
        return split_equally(payload.amount, participant_ids)

    entries = [(share.member_id, share.share_amount) for share in payload.shares or []]
    _require_all_in_group([member_id for member_id, _ in entries], group_member_ids)
    return validate_exact_shares(payload.amount, entries)


def _require_all_in_group(member_ids: Iterable[int], group_member_ids: set[int]) -> None:
    """Reject participants who are not members of the group (GUIDE FR-16)."""
    for member_id in member_ids:
        if member_id not in group_member_ids:
            raise ParticipantNotInGroupError(f"Member {member_id} does not belong to this group")


def _to_expense_read(expense: Expense) -> ExpenseRead:
    """Flatten the ORM object into the response contract, adding member names."""
    return ExpenseRead(
        id=expense.id,
        group_id=expense.group_id,
        description=expense.description,
        amount=expense.amount,
        paid_by_id=expense.paid_by_id,
        paid_by_name=expense.paid_by.name,
        split_type=SplitType(expense.split_type),
        created_at=expense.created_at,
        shares=[
            ExpenseShareRead(
                member_id=share.member_id,
                member_name=share.member.name,
                share_amount=share.share_amount,
            )
            for share in expense.shares
        ],
    )
