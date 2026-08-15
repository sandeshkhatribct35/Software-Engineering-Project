"""Member endpoints, nested under their group."""

from http import HTTPStatus

from fastapi import APIRouter

from app.constants import API_PREFIX
from app.models.member import Member
from app.repositories import groups as groups_repo
from app.repositories import members as members_repo
from app.routers import DbSession, error_responses
from app.schemas.member import MemberCreate, MemberRead

router = APIRouter(prefix=f"{API_PREFIX}/groups", tags=["members"])


@router.post(
    "/{group_id}/members",
    response_model=MemberRead,
    status_code=HTTPStatus.CREATED,
    summary="Add a member",
    description=(
        "Adds a person to the group. Names must be unique within the group, "
        "compared without regard to case; the same name may be used in other groups."
    ),
    responses=error_responses(
        HTTPStatus.NOT_FOUND,
        HTTPStatus.CONFLICT,
        HTTPStatus.UNPROCESSABLE_ENTITY,
    ),
)
def add_member(group_id: int, payload: MemberCreate, db: DbSession) -> Member:
    """Add a member to an existing group."""
    group = groups_repo.get_or_404(db, group_id)
    return members_repo.create(db, group=group, name=payload.name)


@router.get(
    "/{group_id}/members",
    response_model=list[MemberRead],
    summary="List members",
    description="Returns the members of a group in the order they were added.",
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def list_members(group_id: int, db: DbSession) -> list[Member]:
    """Return every member of a group."""
    group = groups_repo.get_or_404(db, group_id)
    return list(members_repo.list_for_group(db, group.id))


@router.delete(
    "/{group_id}/members/{member_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Remove a member",
    description=(
        "Removes a member who has no financial history. A member who has paid for "
        "or shared an expense, or taken part in a settlement, cannot be removed "
        "because doing so would change everybody else's balance."
    ),
    responses=error_responses(HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT),
)
def remove_member(group_id: int, member_id: int, db: DbSession) -> None:
    """Delete a member who is not referenced by any financial record."""
    groups_repo.get_or_404(db, group_id)
    member = members_repo.get_in_group_or_404(db, group_id=group_id, member_id=member_id)
    members_repo.delete(db, member)
