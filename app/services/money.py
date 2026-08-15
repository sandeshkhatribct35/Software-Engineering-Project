"""Fixed-point money helpers.

Every rounding decision in the application happens in this module. Keeping it in
one place is what makes the rounding policy auditable and prevents two parts of
the code from disagreeing about a half-paisa (GUIDE NFR-2, C-7).

Amounts are converted to integer *minor units* (paisa/cents) for any arithmetic
that must divide, because integer division cannot silently lose value.
"""

from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

from app.constants import MONEY_QUANTUM, ZERO_MONEY

MINOR_UNITS_PER_MAJOR = 100


def quantize(amount: Decimal) -> Decimal:
    """Round an amount to two decimal places, halves going away from zero."""
    return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def total(amounts: Iterable[Decimal]) -> Decimal:
    """Sum monetary amounts, returning 0.00 for an empty collection."""
    return quantize(sum(amounts, ZERO_MONEY))


def to_minor_units(amount: Decimal) -> int:
    """Convert an amount to whole minor units (1.23 -> 123)."""
    return int(quantize(amount) * MINOR_UNITS_PER_MAJOR)


def from_minor_units(units: int) -> Decimal:
    """Convert whole minor units back to an amount (123 -> 1.23)."""
    return quantize(Decimal(units) / MINOR_UNITS_PER_MAJOR)
