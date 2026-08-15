"""Request and response contracts for members."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import MemberName


class MemberCreate(BaseModel):
    """Payload for adding a person to a group."""

    name: MemberName


class MemberRead(BaseModel):
    """A member as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique member identifier.")
    group_id: int = Field(description="Group the member belongs to.")
    name: str = Field(description="Name of the person.")
    created_at: datetime = Field(description="When the member was added.")
