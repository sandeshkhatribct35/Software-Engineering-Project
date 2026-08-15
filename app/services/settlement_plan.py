"""Settlement planning.

Given the net balances of a group, produce the payments that clear them.

The planner repeatedly matches the member who owes the most with the member who
is owed the most, transferring the smaller of the two amounts. Each transfer
zeroes at least one member, so a group of ``n`` members needs at most ``n - 1``
transfers — far fewer than settling every individual debt (GUIDE FR-25..FR-27).

The greedy approach is not guaranteed to find the theoretical minimum number of
transfers (that problem is NP-hard), but it is optimal in the common cases, runs
in ``O(n log n)``, and is easy to explain to the people who have to make the
payments. That trade-off is deliberate.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from app.constants import ZERO_MONEY
from app.services.money import quantize


@dataclass(frozen=True)
class Transfer:
    """One payment: who pays, who receives, how much."""

    from_member_id: int
    to_member_id: int
    amount: Decimal


def suggest_settlements(balances: Mapping[int, Decimal]) -> list[Transfer]:
    """Return the payments that bring every balance in the group to zero.

    Members are ordered by amount owed (largest first) and then by member id, so
    identical balances always produce an identical plan (FR-27).
    """
    debtors = _ordered_by_size({m: -b for m, b in balances.items() if b < ZERO_MONEY})
    creditors = _ordered_by_size({m: b for m, b in balances.items() if b > ZERO_MONEY})

    transfers: list[Transfer] = []
    debtor_index = 0
    creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor_id, owed = debtors[debtor_index]
        creditor_id, due = creditors[creditor_index]

        amount = min(owed, due)
        transfers.append(Transfer(debtor_id, creditor_id, quantize(amount)))

        debtors[debtor_index] = (debtor_id, owed - amount)
        creditors[creditor_index] = (creditor_id, due - amount)

        if debtors[debtor_index][1] == ZERO_MONEY:
            debtor_index += 1
        if creditors[creditor_index][1] == ZERO_MONEY:
            creditor_index += 1

    return transfers


def _ordered_by_size(amounts: Mapping[int, Decimal]) -> list[tuple[int, Decimal]]:
    """Sort members by descending amount, breaking ties by ascending member id."""
    return sorted(amounts.items(), key=lambda entry: (-entry[1], entry[0]))
