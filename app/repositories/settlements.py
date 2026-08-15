"""Queries for settlements — payments that clear debts between members."""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.settlement import Settlement


def create(
    db: Session,
    *,
    group: Group,
    from_member_id: int,
    to_member_id: int,
    amount: Decimal,
    note: str | None,
) -> Settlement:
    """Record a payment made from one member of the group to another."""
    settlement = Settlement(
        group_id=group.id,
        from_member_id=from_member_id,
        to_member_id=to_member_id,
        amount=amount,
        note=note,
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


def list_for_group(db: Session, group_id: int) -> Sequence[Settlement]:
    """Return a group's recorded payments, newest first (GUIDE FR-30)."""
    statement = (
        select(Settlement)
        .where(Settlement.group_id == group_id)
        .order_by(Settlement.settled_at.desc(), Settlement.id.desc())
    )
    return db.scalars(statement).all()
