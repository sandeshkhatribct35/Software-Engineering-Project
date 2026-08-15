"""Response contracts for balances, settlement plans and group summaries."""

from pydantic import BaseModel, Field

from app.schemas.common import MoneyOut


class MemberBalance(BaseModel):
    """A member's net position in the group.

    Positive means the group owes the member; negative means the member owes the
    group. The balances of a group always sum to zero (GUIDE FR-23).
    """

    member_id: int = Field(description="Member the balance belongs to.")
    member_name: str = Field(description="Name of the member.")
    balance: MoneyOut = Field(description="Net amount owed to (+) or by (-) the member.")


class GroupBalances(BaseModel):
    """Net balances for every member of a group."""

    group_id: int = Field(description="Group the balances belong to.")
    currency: str = Field(description="Currency the amounts are expressed in.")
    balances: list[MemberBalance] = Field(description="One entry per member, including zeroes.")


class Transfer(BaseModel):
    """A single payment proposed by the settlement planner."""

    from_member_id: int = Field(description="Member who should pay.")
    from_member_name: str = Field(description="Name of the paying member.")
    to_member_id: int = Field(description="Member who should be paid.")
    to_member_name: str = Field(description="Name of the receiving member.")
    amount: MoneyOut = Field(description="Amount to transfer.")


class SettlementPlan(BaseModel):
    """The minimal set of payments that clears every debt in the group."""

    group_id: int = Field(description="Group the plan was computed for.")
    currency: str = Field(description="Currency the amounts are expressed in.")
    transfers: list[Transfer] = Field(description="Payments to make; empty when settled.")
    transfer_count: int = Field(description="Number of payments in the plan.")


class MemberSummary(BaseModel):
    """Totals for one member within the group summary."""

    member_id: int = Field(description="Member the totals belong to.")
    member_name: str = Field(description="Name of the member.")
    total_paid: MoneyOut = Field(description="Total the member has paid for the group.")
    total_owed: MoneyOut = Field(description="Total share of expenses the member carries.")
    balance: MoneyOut = Field(description="Net position after settlements.")


class GroupSummary(BaseModel):
    """Aggregate view of a group's spending."""

    group_id: int = Field(description="Group being summarised.")
    group_name: str = Field(description="Display name of the group.")
    currency: str = Field(description="Currency the amounts are expressed in.")
    member_count: int = Field(description="Number of members in the group.")
    expense_count: int = Field(description="Number of expenses recorded.")
    total_spend: MoneyOut = Field(description="Sum of every expense in the group.")
    members: list[MemberSummary] = Field(description="Per-member totals.")
