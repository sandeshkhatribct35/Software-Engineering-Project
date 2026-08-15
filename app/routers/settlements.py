"""Settlement endpoints — recording payments that clear debts."""

from http import HTTPStatus

from fastapi import APIRouter

from app.constants import API_PREFIX
from app.errors import MemberNotInGroupError, SameMemberSettlementError
from app.models.settlement import Settlement
from app.repositories import groups as groups_repo
from app.repositories import members as members_repo
from app.repositories import settlements as settlements_repo
from app.routers import DbSession, error_responses
from app.schemas.settlement import SettlementCreate, SettlementRead

router = APIRouter(prefix=f"{API_PREFIX}/groups", tags=["settlements"])


@router.post(
    "/{group_id}/settlements",
    response_model=SettlementRead,
    status_code=HTTPStatus.CREATED,
    summary="Record a settlement",
    description=(
        "Records money actually handed from one member to another. The payment is "
        "reflected in the group's balances straight away."
    ),
    responses=error_responses(HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY),
)
def record_settlement(group_id: int, payload: SettlementCreate, db: DbSession) -> Settlement:
    """Validate both members belong to the group, then store the payment."""
    group = groups_repo.get_or_404(db, group_id)

    if payload.from_member_id == payload.to_member_id:
        raise SameMemberSettlementError("A member cannot settle a debt with themselves")

    group_member_ids = members_repo.member_ids(db, group.id)
    for member_id in (payload.from_member_id, payload.to_member_id):
        if member_id not in group_member_ids:
            raise MemberNotInGroupError(f"Member {member_id} does not belong to group {group_id}")

    return settlements_repo.create(
        db,
        group=group,
        from_member_id=payload.from_member_id,
        to_member_id=payload.to_member_id,
        amount=payload.amount,
        note=payload.note,
    )


@router.get(
    "/{group_id}/settlements",
    response_model=list[SettlementRead],
    summary="List settlements",
    description="Returns the payments recorded for the group, newest first.",
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def list_settlements(group_id: int, db: DbSession) -> list[Settlement]:
    """Return every payment recorded in the group."""
    group = groups_repo.get_or_404(db, group_id)
    return list(settlements_repo.list_for_group(db, group.id))
