"""Unit tests for the settlement planner.

Beyond checking individual plans, these tests assert the two properties the
planner promises for *any* input: executing the plan settles the group, and the
number of payments never exceeds ``n - 1`` (GUIDE FR-25..FR-27).
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal

import pytest

from app.services.settlement_plan import Transfer, suggest_settlements

# Balance sets used by the property tests below; each one sums to zero.
BALANCE_SCENARIOS: list[dict[int, Decimal]] = [
    {1: Decimal("0.00")},
    {1: Decimal("50.00"), 2: Decimal("-50.00")},
    {1: Decimal("666.66"), 2: Decimal("-333.33"), 3: Decimal("-333.33")},
    {1: Decimal("-166.67"), 2: Decimal("166.67"), 3: Decimal("0.00")},
    {
        1: Decimal("100.00"),
        2: Decimal("200.00"),
        3: Decimal("-50.00"),
        4: Decimal("-150.00"),
        5: Decimal("-100.00"),
    },
    {1: Decimal("0.01"), 2: Decimal("-0.01")},
]


def apply_transfers(
    balances: Mapping[int, Decimal],
    transfers: Sequence[Transfer],
) -> dict[int, Decimal]:
    """Return the balances that would remain after making every payment."""
    remaining = dict(balances)
    for transfer in transfers:
        remaining[transfer.from_member_id] += transfer.amount
        remaining[transfer.to_member_id] -= transfer.amount
    return remaining


def test_a_settled_group_needs_no_payments() -> None:
    assert suggest_settlements({1: Decimal("0.00"), 2: Decimal("0.00")}) == []


def test_a_single_debt_becomes_a_single_payment() -> None:
    plan = suggest_settlements({1: Decimal("50.00"), 2: Decimal("-50.00")})

    assert plan == [Transfer(from_member_id=2, to_member_id=1, amount=Decimal("50.00"))]


def test_circular_debts_cancel_out_instead_of_being_paid() -> None:
    """A owes B, B owes C and C owes A the same amount: nobody needs to pay."""
    circular = {1: Decimal("0.00"), 2: Decimal("0.00"), 3: Decimal("0.00")}

    assert suggest_settlements(circular) == []


def test_the_largest_debtor_pays_the_largest_creditor_first() -> None:
    balances = {
        1: Decimal("300.00"),
        2: Decimal("100.00"),
        3: Decimal("-400.00"),
    }

    plan = suggest_settlements(balances)

    assert plan[0] == Transfer(from_member_id=3, to_member_id=1, amount=Decimal("300.00"))
    assert plan[1] == Transfer(from_member_id=3, to_member_id=2, amount=Decimal("100.00"))


def test_a_debt_is_split_when_one_debtor_owes_several_creditors() -> None:
    balances = {1: Decimal("-90.00"), 2: Decimal("60.00"), 3: Decimal("30.00")}

    plan = suggest_settlements(balances)

    assert [transfer.amount for transfer in plan] == [Decimal("60.00"), Decimal("30.00")]
    assert {transfer.from_member_id for transfer in plan} == {1}


@pytest.mark.parametrize("balances", BALANCE_SCENARIOS)
def test_executing_the_plan_settles_every_member(balances: dict[int, Decimal]) -> None:
    plan = suggest_settlements(balances)

    remaining = apply_transfers(balances, plan)

    assert all(value == Decimal("0.00") for value in remaining.values())


@pytest.mark.parametrize("balances", BALANCE_SCENARIOS)
def test_plan_never_needs_more_than_one_payment_per_member_minus_one(
    balances: dict[int, Decimal],
) -> None:
    plan = suggest_settlements(balances)

    assert len(plan) <= max(len(balances) - 1, 0)


@pytest.mark.parametrize("balances", BALANCE_SCENARIOS)
def test_every_proposed_payment_is_a_positive_amount(balances: dict[int, Decimal]) -> None:
    assert all(transfer.amount > Decimal("0.00") for transfer in suggest_settlements(balances))


@pytest.mark.parametrize("balances", BALANCE_SCENARIOS)
def test_the_same_balances_always_produce_the_same_plan(balances: dict[int, Decimal]) -> None:
    """Determinism matters: the plan is shown to people who must act on it."""
    assert suggest_settlements(balances) == suggest_settlements(balances)


def test_plan_does_not_depend_on_the_order_of_the_input() -> None:
    balances = {1: Decimal("100.00"), 2: Decimal("-40.00"), 3: Decimal("-60.00")}
    reversed_balances = dict(reversed(list(balances.items())))

    assert suggest_settlements(balances) == suggest_settlements(reversed_balances)


def test_members_with_a_zero_balance_are_left_out_of_the_plan() -> None:
    balances = {1: Decimal("25.00"), 2: Decimal("-25.00"), 3: Decimal("0.00")}

    involved = {
        member
        for transfer in suggest_settlements(balances)
        for member in (transfer.from_member_id, transfer.to_member_id)
    }

    assert involved == {1, 2}
