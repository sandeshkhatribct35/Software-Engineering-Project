"""Request and response contracts for settlements."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import MoneyOut, SettlementAmount, SettlementNote


class SettlementCreate(BaseModel):
    """Payload for recording a payment between two members."""

    from_member_id: int = Field(description="Member who paid the money.")
    to_member_id: int = Field(description="Member who received the money.")
    amount: SettlementAmount
    note: SettlementNote = None


class SettlementRead(BaseModel):
    """A recorded payment as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique settlement identifier.")
    group_id: int = Field(description="Group the payment belongs to.")
    from_member_id: int = Field(description="Member who paid.")
    to_member_id: int = Field(description="Member who was paid.")
    amount: MoneyOut = Field(description="Amount transferred.")
    note: str | None = Field(description="Optional note describing the payment.")
    settled_at: datetime = Field(description="When the payment was recorded.")
