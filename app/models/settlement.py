"""Settlement ORM model — a payment made to clear a debt between two members."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import MONEY_PRECISION, SETTLEMENT_NOTE_MAX_LENGTH
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.member import Member

MONEY_TYPE = Numeric(12, MONEY_PRECISION)


class Settlement(Base):
    """Money actually handed over from one member to another."""

    __tablename__ = "settlements"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_settlement_amount_positive"),
        CheckConstraint(
            "from_member_id <> to_member_id",
            name="ck_settlement_distinct_members",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    to_member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(MONEY_TYPE, nullable=False)
    note: Mapped[str | None] = mapped_column(String(SETTLEMENT_NOTE_MAX_LENGTH))
    settled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    group: Mapped["Group"] = relationship(back_populates="settlements")
    from_member: Mapped["Member"] = relationship(foreign_keys=[from_member_id])
    to_member: Mapped["Member"] = relationship(foreign_keys=[to_member_id])
