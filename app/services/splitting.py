"""Expense splitting.

Two strategies are supported. Both guarantee the same invariant: the shares of
an expense sum to exactly the expense amount, so the system never loses or
invents money (GUIDE FR-17, FR-18).

These functions validate their own inputs rather than trusting the caller: they
are the last line of defence before shares are written to the database.
"""

from collections.abc import Sequence
from decimal import Decimal

from app.errors import (
    DuplicateParticipantError,
    NegativeShareError,
    NoParticipantsError,
    SharesDoNotSumError,
)
from app.services.money import from_minor_units, quantize, to_minor_units, total

# A caller-supplied share: the member who owes it and how much they owe.
ShareEntry = tuple[int, Decimal]


def split_equally(amount: Decimal, participant_ids: Sequence[int]) -> dict[int, Decimal]:
    """Divide an amount evenly between participants.

    The amount rarely divides evenly (1000.00 between three people does not), so
    the division is done in minor units and the indivisible remainder is handed
    out one unit at a time in ascending member-id order. That keeps the result
    exact and reproducible: the same input always produces the same split.
    """
    _reject_empty(participant_ids)
    _reject_duplicates(participant_ids)

    total_units = to_minor_units(amount)
    base_units, remainder_units = divmod(total_units, len(participant_ids))

    shares: dict[int, Decimal] = {}
    for position, member_id in enumerate(sorted(participant_ids)):
        extra_unit = 1 if position < remainder_units else 0
        shares[member_id] = from_minor_units(base_units + extra_unit)
    return shares


def validate_exact_shares(amount: Decimal, entries: Sequence[ShareEntry]) -> dict[int, Decimal]:
    """Accept caller-supplied shares only if they add up to the expense amount.

    A share of zero is legitimate (a member who was present but owes nothing);
    a negative share is not, and shares that miss the total by even one paisa
    are rejected rather than silently adjusted.
    """
    member_ids = [member_id for member_id, _ in entries]
    _reject_empty(member_ids)
    _reject_duplicates(member_ids)

    for member_id, share_amount in entries:
        if share_amount < 0:
            raise NegativeShareError(f"Share for member {member_id} is negative")

    shares_total = total(share for _, share in entries)
    expected_total = quantize(amount)
    if shares_total != expected_total:
        raise SharesDoNotSumError(
            f"Shares total {shares_total} but the expense amount is {expected_total}"
        )

    return dict(entries)


def _reject_empty(participant_ids: Sequence[int]) -> None:
    if not participant_ids:
        raise NoParticipantsError("An expense must be shared by at least one member")


def _reject_duplicates(participant_ids: Sequence[int]) -> None:
    if len(set(participant_ids)) != len(participant_ids):
        raise DuplicateParticipantError("A member may appear only once in an expense")
