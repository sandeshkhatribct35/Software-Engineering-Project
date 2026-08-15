"""Queries for expenses and their shares."""

from collections.abc import Mapping, Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.constants import SplitType
from app.errors import ExpenseNotFoundError
from app.models.expense import Expense, ExpenseShare
from app.models.group import Group


def create(
    db: Session,
    *,
    group: Group,
    description: str,
    amount: Decimal,
    paid_by_id: int,
    split_type: SplitType,
    shares: Mapping[int, Decimal],
) -> Expense:
    """Write an expense and its shares in a single transaction.

    The shares are attached to the expense before the flush, so either both the
    expense and its full breakdown are stored, or neither is.
    """
    expense = Expense(
        group_id=group.id,
        description=description,
        amount=amount,
        paid_by_id=paid_by_id,
        split_type=split_type.value,
        shares=[
            ExpenseShare(member_id=member_id, share_amount=share_amount)
            for member_id, share_amount in sorted(shares.items())
        ],
    )
    db.add(expense)
    db.commit()
    return get_or_404(db, expense.id)


def list_for_group(db: Session, group_id: int, *, limit: int, offset: int) -> Sequence[Expense]:
    """Return a page of a group's expenses, newest first (GUIDE FR-19)."""
    statement = (
        select(Expense)
        .where(Expense.group_id == group_id)
        .order_by(Expense.created_at.desc(), Expense.id.desc())
        .limit(limit)
        .offset(offset)
        .options(*_eager_loads())
    )
    return db.scalars(statement).all()


def get_or_404(db: Session, expense_id: int) -> Expense:
    """Return an expense with its shares, or raise the error that becomes 404."""
    statement = select(Expense).where(Expense.id == expense_id).options(*_eager_loads())
    expense = db.scalars(statement).first()
    if expense is None:
        raise ExpenseNotFoundError(f"Expense {expense_id} does not exist")
    return expense


def count_for_group(db: Session, group_id: int) -> int:
    """Return how many expenses a group has recorded."""
    statement = select(func.count(Expense.id)).where(Expense.group_id == group_id)
    return db.scalar(statement) or 0


def delete(db: Session, expense: Expense) -> None:
    """Delete an expense; its shares are removed with it (GUIDE FR-21)."""
    db.delete(expense)
    db.commit()


def _eager_loads() -> tuple[ExecutableOption, ...]:
    """Load payer and share owners up front so listings issue no N+1 queries."""
    return (
        selectinload(Expense.paid_by),
        selectinload(Expense.shares).selectinload(ExpenseShare.member),
    )
