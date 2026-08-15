"""Queries for group members."""

from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.errors import DuplicateMemberNameError, MemberHasActivityError, MemberNotFoundError
from app.models.expense import Expense, ExpenseShare
from app.models.group import Group
from app.models.member import Member
from app.models.settlement import Settlement


def create(db: Session, *, group: Group, name: str) -> Member:
    """Add a member to a group, rejecting a name already used in that group.

    The database enforces exact uniqueness; the check below additionally rejects
    names that differ only by case, which people read as the same person
    (GUIDE FR-8).
    """
    if _name_taken(db, group_id=group.id, name=name):
        raise DuplicateMemberNameError(f"Group {group.id} already has a member named '{name}'")

    member = Member(group_id=group.id, name=name)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def list_for_group(db: Session, group_id: int) -> Sequence[Member]:
    """Return the members of a group in the order they were added."""
    statement = select(Member).where(Member.group_id == group_id).order_by(Member.id)
    return db.scalars(statement).all()


def get_in_group_or_404(db: Session, *, group_id: int, member_id: int) -> Member:
    """Return a member of this group, or raise the error that becomes HTTP 404."""
    statement = select(Member).where(Member.id == member_id, Member.group_id == group_id)
    member = db.scalars(statement).first()
    if member is None:
        raise MemberNotFoundError(f"Member {member_id} does not exist in group {group_id}")
    return member


def member_ids(db: Session, group_id: int) -> set[int]:
    """Return the ids of every member of a group, for membership checks."""
    return set(db.scalars(select(Member.id).where(Member.group_id == group_id)).all())


def has_financial_activity(db: Session, member_id: int) -> bool:
    """Report whether any expense or settlement still refers to this member."""
    paid_expense = select(Expense.id).where(Expense.paid_by_id == member_id)
    owes_share = select(ExpenseShare.id).where(ExpenseShare.member_id == member_id)
    settlement = select(Settlement.id).where(
        or_(Settlement.from_member_id == member_id, Settlement.to_member_id == member_id)
    )
    for statement in (paid_expense, owes_share, settlement):
        if db.scalars(statement.limit(1)).first() is not None:
            return True
    return False


def delete(db: Session, member: Member) -> None:
    """Remove a member who has no financial history (GUIDE FR-11).

    Members involved in expenses or settlements are kept: deleting them would
    silently change everybody else's balance.
    """
    if has_financial_activity(db, member.id):
        raise MemberHasActivityError(
            f"Member {member.id} is referenced by an expense or settlement and cannot be removed"
        )
    db.delete(member)
    db.commit()


def _name_taken(db: Session, *, group_id: int, name: str) -> bool:
    statement = select(Member.id).where(
        Member.group_id == group_id,
        func.lower(Member.name) == name.lower(),
    )
    return db.scalars(statement).first() is not None
