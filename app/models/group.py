"""Group ORM model — the container every other record belongs to."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import (
    CURRENCY_CODE_LENGTH,
    DEFAULT_CURRENCY,
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
)
from app.models.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.expense import Expense
    from app.models.member import Member
    from app.models.settlement import Settlement


class Group(CreatedAtMixin, Base):
    """A set of people who share expenses in a single currency."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(GROUP_NAME_MAX_LENGTH), nullable=False)
    description: Mapped[str | None] = mapped_column(String(GROUP_DESCRIPTION_MAX_LENGTH))
    currency: Mapped[str] = mapped_column(
        String(CURRENCY_CODE_LENGTH),
        nullable=False,
        server_default=DEFAULT_CURRENCY,
    )

    # Deleting a group removes everything recorded inside it (GUIDE FR-6).
    members: Mapped[list["Member"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="Member.id",
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    settlements: Mapped[list["Settlement"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
