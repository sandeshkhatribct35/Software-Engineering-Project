"""Aggregate queries behind balances, settlement plans and group summaries.

The four totals that make up a balance are computed by four grouped SQL
statements, not by looping over members in Python. The number of queries is
therefore constant no matter how large the group grows (GUIDE NFR-11).
"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.constants import ZERO_MONEY
from app.models.expense import Expense, ExpenseShare
from app.models.member import Member
from app.models.settlement import Settlement
from app.services.balances import MemberTotals


def member_totals(db: Session, group_id: int) -> list[MemberTotals]:
    """Return the aggregated amounts for every member of a group, ordered by id."""
    paid = _totals_by_member(
        db,
        select(Expense.paid_by_id, func.sum(Expense.amount))
        .where(Expense.group_id == group_id)
        .group_by(Expense.paid_by_id),
    )
    owed = _totals_by_member(
        db,
        select(ExpenseShare.member_id, func.sum(ExpenseShare.share_amount))
        .join(Expense, Expense.id == ExpenseShare.expense_id)
        .where(Expense.group_id == group_id)
        .group_by(ExpenseShare.member_id),
    )
    settled_paid = _totals_by_member(
        db,
        select(Settlement.from_member_id, func.sum(Settlement.amount))
        .where(Settlement.group_id == group_id)
        .group_by(Settlement.from_member_id),
    )
    settled_received = _totals_by_member(
        db,
        select(Settlement.to_member_id, func.sum(Settlement.amount))
        .where(Settlement.group_id == group_id)
        .group_by(Settlement.to_member_id),
    )

    return [
        MemberTotals(
            member_id=member_id,
            total_paid=paid.get(member_id, ZERO_MONEY),
            total_owed=owed.get(member_id, ZERO_MONEY),
            settlements_paid=settled_paid.get(member_id, ZERO_MONEY),
            settlements_received=settled_received.get(member_id, ZERO_MONEY),
        )
        for member_id in _member_ids_in_order(db, group_id)
    ]


def _member_ids_in_order(db: Session, group_id: int) -> Sequence[int]:
    statement = select(Member.id).where(Member.group_id == group_id).order_by(Member.id)
    return db.scalars(statement).all()


def _totals_by_member(db: Session, statement: Select[tuple[int, Decimal]]) -> dict[int, Decimal]:
    """Run a grouped SUM query and return it keyed by member id."""
    return dict(db.execute(statement).all())
