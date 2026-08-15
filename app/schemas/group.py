"""Request and response contracts for groups."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.constants import DEFAULT_CURRENCY
from app.schemas.common import CurrencyCode, GroupDescription, GroupName
from app.schemas.member import MemberRead


class GroupCreate(BaseModel):
    """Payload for creating a group."""

    name: GroupName
    description: GroupDescription = None
    currency: CurrencyCode = DEFAULT_CURRENCY


class GroupUpdate(BaseModel):
    """Partial update payload.

    Fields left out of the request body are not modified, which is why every
    field is optional and the router applies only those explicitly supplied.
    """

    name: GroupName | None = None
    description: GroupDescription = None


class GroupRead(BaseModel):
    """A group as returned by list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique group identifier.")
    name: str = Field(description="Display name of the group.")
    description: str | None = Field(description="Optional note describing the group.")
    currency: str = Field(description="Currency the group records amounts in.")
    created_at: datetime = Field(description="When the group was created.")


class GroupDetail(GroupRead):
    """A group together with its members."""

    members: list[MemberRead] = Field(description="Members currently in the group.")
