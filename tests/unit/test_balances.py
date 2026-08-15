"""Unit tests for net balance computation."""

from decimal import Decimal

from app.services.balances import (
    MemberTotals,
    balance_of,
    balances_are_settled,
    compute_balances,
)


def test_member_who_paid_for_everyone_is_owed_money() -> None:
    totals = MemberTotals(1, total_paid=Decimal("1000.00"), total_owed=Decimal("333.34"))

    assert balance_of(totals) == Decimal("666.66")


def test_member_who_only_consumed_owes_money() -> None:
    totals = MemberTotals(2, total_owed=Decimal("333.33"))

    assert balance_of(totals) == Decimal("-333.33")


def test_member_with_no_activity_has_a_zero_balance() -> None:
    assert balance_of(MemberTotals(3)) == Decimal("0.00")


def test_paying_a_settlement_moves_a_debtor_towards_zero() -> None:
    totals = MemberTotals(
        2,
        total_owed=Decimal("333.33"),
        settlements_paid=Decimal("333.33"),
    )

    assert balance_of(totals) == Decimal("0.00")


def test_receiving_a_settlement_reduces_what_the_group_owes_a_member() -> None:
    totals = MemberTotals(
        1,
        total_paid=Decimal("1000.00"),
        total_owed=Decimal("333.34"),
        settlements_received=Decimal("666.66"),
    )

    assert balance_of(totals) == Decimal("0.00")


def test_balances_of_a_group_always_sum_to_zero() -> None:
    """The core accounting invariant: money is only ever moved, never created."""
    totals = [
        MemberTotals(1, total_paid=Decimal("1000.00"), total_owed=Decimal("333.34")),
        MemberTotals(2, total_paid=Decimal("1200.00"), total_owed=Decimal("1033.33")),
        MemberTotals(3, total_owed=Decimal("833.33")),
    ]

    balances = compute_balances(totals)

    assert sum(balances.values()) == Decimal("0.00")


def test_compute_balances_returns_one_entry_per_member() -> None:
    balances = compute_balances([MemberTotals(1), MemberTotals(2), MemberTotals(5)])

    assert list(balances) == [1, 2, 5]


def test_a_group_with_only_zero_balances_is_settled() -> None:
    assert balances_are_settled({1: Decimal("0.00"), 2: Decimal("0.00")})


def test_a_group_with_any_debt_is_not_settled() -> None:
    assert not balances_are_settled({1: Decimal("-0.01"), 2: Decimal("0.01")})
