"""Group endpoints."""

from http import HTTPStatus

from fastapi import APIRouter

from app.constants import API_PREFIX
from app.models.group import Group
from app.repositories import groups as groups_repo
from app.routers import DbSession, error_responses
from app.schemas.group import GroupCreate, GroupDetail, GroupRead, GroupUpdate

router = APIRouter(prefix=f"{API_PREFIX}/groups", tags=["groups"])


@router.post(
    "",
    response_model=GroupRead,
    status_code=HTTPStatus.CREATED,
    summary="Create a group",
    description="Creates an expense-sharing group. Members are added separately.",
    responses=error_responses(HTTPStatus.UNPROCESSABLE_ENTITY),
)
def create_group(payload: GroupCreate, db: DbSession) -> Group:
    """Create a group from the validated payload."""
    return groups_repo.create(
        db,
        name=payload.name,
        description=payload.description,
        currency=payload.currency,
    )


@router.get(
    "",
    response_model=list[GroupRead],
    summary="List groups",
    description="Returns every group, most recently created first.",
)
def list_groups(db: DbSession) -> list[Group]:
    """Return all groups."""
    return list(groups_repo.list_all(db))


@router.get(
    "/{group_id}",
    response_model=GroupDetail,
    summary="Get a group",
    description="Returns one group together with the members currently in it.",
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def get_group(group_id: int, db: DbSession) -> Group:
    """Return a single group with its members."""
    return groups_repo.get_or_404(db, group_id)


@router.patch(
    "/{group_id}",
    response_model=GroupRead,
    summary="Update a group",
    description="Updates the name and/or description. Omitted fields are left unchanged.",
    responses=error_responses(HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY),
)
def update_group(group_id: int, payload: GroupUpdate, db: DbSession) -> Group:
    """Apply a partial update to a group."""
    group = groups_repo.get_or_404(db, group_id)
    return groups_repo.update(db, group, payload.model_dump(exclude_unset=True))


@router.delete(
    "/{group_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Delete a group",
    description="Deletes the group with all of its members, expenses and settlements.",
    responses=error_responses(HTTPStatus.NOT_FOUND),
)
def delete_group(group_id: int, db: DbSession) -> None:
    """Delete a group and everything recorded inside it."""
    groups_repo.delete(db, groups_repo.get_or_404(db, group_id))
