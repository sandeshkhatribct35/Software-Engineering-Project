"""Queries for groups."""

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import GroupNotFoundError
from app.models.group import Group

# Only these fields may be changed by a PATCH request; anything else in the
# payload is ignored rather than blindly assigned to the model.
UPDATABLE_FIELDS = frozenset({"name", "description"})


def create(db: Session, *, name: str, description: str | None, currency: str) -> Group:
    """Insert a new group and return it with its generated id."""
    group = Group(name=name, description=description, currency=currency)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def list_all(db: Session) -> Sequence[Group]:
    """Return every group, most recently created first (GUIDE FR-3)."""
    statement = select(Group).order_by(Group.created_at.desc(), Group.id.desc())
    return db.scalars(statement).all()


def get_or_404(db: Session, group_id: int) -> Group:
    """Return a group or raise the domain error that becomes HTTP 404."""
    group = db.get(Group, group_id)
    if group is None:
        raise GroupNotFoundError(f"Group {group_id} does not exist")
    return group


def update(db: Session, group: Group, changes: Mapping[str, Any]) -> Group:
    """Apply only the fields the caller actually supplied (GUIDE FR-5)."""
    for field, value in changes.items():
        if field in UPDATABLE_FIELDS:
            setattr(group, field, value)
    db.commit()
    db.refresh(group)
    return group


def delete(db: Session, group: Group) -> None:
    """Delete a group and everything recorded inside it (GUIDE FR-6)."""
    db.delete(group)
    db.commit()
