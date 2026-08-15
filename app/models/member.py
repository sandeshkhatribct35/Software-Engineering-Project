"""Member ORM model — one person inside one group."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import MEMBER_NAME_MAX_LENGTH
from app.models.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.group import Group


class Member(CreatedAtMixin, Base):
    """A participant in a group.

    Names are unique within a group but may repeat across groups (GUIDE FR-9).
    """

    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("group_id", "name", name="uq_member_group_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(MEMBER_NAME_MAX_LENGTH), nullable=False)

    group: Mapped["Group"] = relationship(back_populates="members")
