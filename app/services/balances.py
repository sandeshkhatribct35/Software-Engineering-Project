"""Net balance computation.

The repository layer aggregates the four totals below with SQL; this module
turns them into the balance each member actually holds (GUIDE §11.3, FR-22).
Splitting the work this way keeps the arithmetic free of database access, so
every balance rule can be tested directly.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from app.constants import ZERO_MONEY
from app.services.money import quantize


@dataclass(frozen=True)
class MemberTotals:
    """Everything that moves a single member's balance."""

    member_id: int
    total_paid: Decimal = ZERO_MONEY
    total_owed: Decimal = ZERO_MONEY
    settlements_paid: Decimal = ZERO_MONEY
    settlements_received: Decimal = ZERO_MONEY


def balance_of(totals: MemberTotals) -> Decimal:
    """Return one member's net position.

    Positive means the group owes the member; negative means the member owes the
    group. Paying a settlement moves a debtor towards zero, which is why
    settlements paid count in the member's favour.
    """
    return quantize(
        totals.total_paid
        - totals.total_owed
        + totals.settlements_paid
        - totals.settlements_received
    )


def compute_balances(totals: Sequence[MemberTotals]) -> dict[int, Decimal]:
    """Return the balance of every member, keyed by member id."""
    return {member.member_id: balance_of(member) for member in totals}


def balances_are_settled(balances: Mapping[int, Decimal]) -> bool:
    """Return True when nobody in the group owes anybody anything."""
    return all(balance == ZERO_MONEY for balance in balances.values())
