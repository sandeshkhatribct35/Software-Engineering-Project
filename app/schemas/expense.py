"""Request and response contracts for expenses and their shares."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.constants import SplitType
from app.schemas.common import ExpenseAmount, ExpenseDescription, MoneyOut, ShareAmount


class ExpenseShareInput(BaseModel):
    """One participant's exact share of an expense."""

    member_id: int = Field(description="Member who owes this portion.")
    share_amount: ShareAmount


class ExpenseCreate(BaseModel):
    """Payload for recording an expense.

    The two split strategies take different inputs, and supplying both is a
    contradiction rather than a convenience:

    * ``EQUAL`` expects ``participant_ids``; the API divides the amount.
    * ``EXACT`` expects ``shares``; the participants are the members listed there.
    """

    description: ExpenseDescription
    amount: ExpenseAmount
    paid_by_id: int = Field(description="Member who actually paid the money.")
    split_type: SplitType = Field(description="How the cost is divided.")
    participant_ids: list[int] | None = Field(
        default=None,
        description="Members sharing the cost. Required for an EQUAL split.",
        examples=[[1, 2, 3]],
    )
    shares: list[ExpenseShareInput] | None = Field(
        default=None,
        description="Exact amount owed per member. Required for an EXACT split.",
    )

    @model_validator(mode="after")
    def check_split_payload(self) -> "ExpenseCreate":
        """Ensure the payload matches the chosen split strategy."""
        if self.split_type is SplitType.EQUAL:
            if self.shares is not None:
                raise ValueError("shares must be omitted for an EQUAL split")
            if self.participant_ids is None:
                raise ValueError("participant_ids is required for an EQUAL split")
        else:
            if self.participant_ids is not None:
                raise ValueError("participant_ids must be omitted for an EXACT split")
            if self.shares is None:
                raise ValueError("shares is required for an EXACT split")
        return self


class ExpenseShareRead(BaseModel):
    """One participant's share as returned by the API."""

    member_id: int = Field(description="Member who owes this portion.")
    member_name: str = Field(description="Name of that member.")
    share_amount: MoneyOut = Field(description="Amount owed by the member.")


class ExpenseRead(BaseModel):
    """An expense together with the full breakdown of who owes what."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique expense identifier.")
    group_id: int = Field(description="Group the expense belongs to.")
    description: str = Field(description="What the money was spent on.")
    amount: MoneyOut = Field(description="Total amount of the expense.")
    paid_by_id: int = Field(description="Member who paid.")
    paid_by_name: str = Field(description="Name of the member who paid.")
    split_type: SplitType = Field(description="How the cost was divided.")
    created_at: datetime = Field(description="When the expense was recorded.")
    shares: list[ExpenseShareRead] = Field(description="Per-member breakdown of the cost.")
