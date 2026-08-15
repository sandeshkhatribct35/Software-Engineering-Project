"""Unit tests for the fixed-point money helpers."""

from decimal import Decimal

import pytest

from app.services.money import from_minor_units, quantize, to_minor_units, total


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10", "10.00"),
        ("10.1", "10.10"),
        ("10.005", "10.01"),  # halves round away from zero
        ("10.004", "10.00"),
        ("-10.005", "-10.01"),
        ("0.333333", "0.33"),
    ],
)
def test_quantize_rounds_half_up_to_two_decimals(raw: str, expected: str) -> None:
    assert quantize(Decimal(raw)) == Decimal(expected)


def test_total_of_empty_collection_is_zero() -> None:
    assert total([]) == Decimal("0.00")


def test_total_sums_amounts() -> None:
    assert total([Decimal("10.10"), Decimal("0.90"), Decimal("1.00")]) == Decimal("12.00")


@pytest.mark.parametrize(
    ("amount", "units"),
    [("1.23", 123), ("0.01", 1), ("1000.00", 100_000), ("0.00", 0)],
)
def test_minor_unit_conversion_round_trips(amount: str, units: int) -> None:
    assert to_minor_units(Decimal(amount)) == units
    assert from_minor_units(units) == Decimal(amount)


def test_to_minor_units_rounds_before_converting() -> None:
    """A third of a paisa cannot be stored, so it is rounded, never truncated."""
    assert to_minor_units(Decimal("1.005")) == 101
