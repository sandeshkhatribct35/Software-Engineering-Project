"""Expense and ExpenseShare ORM models.

An expense records what was spent and who paid; its shares record how much of
that cost each participant carries. The two are always written together, so the
shares of an expense are deleted with it.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import EXPENSE_DESCRIPTION_MAX_LENGTH
from app.models.base import MONEY_TYPE, Base, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.member import Member

SPLIT_TYPE_MAX_LENGTH = 10


class Expense(CreatedAtMixin, Base):
    """A single shared cost paid by one member on behalf of several."""

    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expense_amount_positive"),
        CheckConstraint("split_type IN ('EQUAL', 'EXACT')", name="ck_expense_split_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(EXPENSE_DESCRIPTION_MAX_LENGTH),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(MONEY_TYPE, nullable=False)
    # RESTRICT: a member who has paid for something cannot be deleted (GUIDE FR-11).
    paid_by_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    split_type: Mapped[str] = mapped_column(String(SPLIT_TYPE_MAX_LENGTH), nullable=False)

    group: Mapped["Group"] = relationship(back_populates="expenses")
    paid_by: Mapped["Member"] = relationship(foreign_keys=[paid_by_id])
    shares: Mapped[list["ExpenseShare"]] = relationship(
        back_populates="expense",
        cascade="all, delete-orphan",
        order_by="ExpenseShare.member_id",
    )


class ExpenseShare(Base):
    """The portion of one expense owed by one member."""

    __tablename__ = "expense_shares"
    __table_args__ = (
        UniqueConstraint("expense_id", "member_id", name="uq_share_expense_member"),
        CheckConstraint("share_amount >= 0", name="ck_share_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    share_amount: Mapped[Decimal] = mapped_column(MONEY_TYPE, nullable=False)

    expense: Mapped["Expense"] = relationship(back_populates="shares")
    member: Mapped["Member"] = relationship(foreign_keys=[member_id])
