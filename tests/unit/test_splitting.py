"""Unit tests for the expense splitting rules.

The invariant that matters throughout: the shares of an expense always add up to
exactly the expense amount (GUIDE FR-17, FR-18).
"""

from decimal import Decimal

import pytest

from app.errors import (
    DuplicateParticipantError,
    NegativeShareError,
    NoParticipantsError,
    SharesDoNotSumError,
)
from app.services.splitting import split_equally, validate_exact_shares


def test_amount_that_divides_evenly_is_split_evenly() -> None:
    shares = split_equally(Decimal("900.00"), [1, 2, 3])

    assert shares == {1: Decimal("300.00"), 2: Decimal("300.00"), 3: Decimal("300.00")}


def test_indivisible_amount_gives_the_remainder_to_the_lowest_member_ids() -> None:
    shares = split_equally(Decimal("1000.00"), [1, 2, 3])

    assert shares == {1: Decimal("333.33"), 2: Decimal("333.33"), 3: Decimal("333.33")}
    assert sum(shares.values()) == Decimal("1000.00")


def test_split_is_independent_of_the_order_participants_are_given_in() -> None:
    assert split_equally(Decimal("100.00"), [3, 1, 2]) == split_equally(
        Decimal("100.00"), [1, 2, 3]
    )


def test_single_participant_owes_the_whole_amount() -> None:
    assert split_equally(Decimal("49.99"), [7]) == {7: Decimal("49.99")}


def test_smallest_possible_amount_is_not_lost() -> None:
    """One paisa between three people: somebody owes it, and only one paisa exists."""
    shares = split_equally(Decimal("0.01"), [1, 2, 3])

    assert sum(shares.values()) == Decimal("0.01")
    assert sorted(shares.values()) == [Decimal("0.00"), Decimal("0.00"), Decimal("0.01")]


@pytest.mark.parametrize("participant_count", [2, 3, 6, 7, 11, 23])
def test_shares_always_sum_to_the_exact_amount(participant_count: int) -> None:
    amount = Decimal("9999.99")

    shares = split_equally(amount, list(range(1, participant_count + 1)))

    assert sum(shares.values()) == amount


def test_equal_split_rejects_an_empty_participant_list() -> None:
    with pytest.raises(NoParticipantsError):
        split_equally(Decimal("10.00"), [])


def test_equal_split_rejects_a_repeated_participant() -> None:
    with pytest.raises(DuplicateParticipantError):
        split_equally(Decimal("10.00"), [1, 2, 1])


def test_exact_shares_that_add_up_are_accepted() -> None:
    entries = [(1, Decimal("500.00")), (2, Decimal("700.00"))]

    assert validate_exact_shares(Decimal("1200.00"), entries) == {
        1: Decimal("500.00"),
        2: Decimal("700.00"),
    }


def test_a_zero_share_is_allowed() -> None:
    """Somebody can be part of an expense without owing anything for it."""
    entries = [(1, Decimal("0.00")), (2, Decimal("50.00"))]

    assert validate_exact_shares(Decimal("50.00"), entries)[1] == Decimal("0.00")


@pytest.mark.parametrize("last_share", ["700.01", "699.99"])
def test_exact_shares_are_rejected_when_they_miss_by_one_paisa(last_share: str) -> None:
    entries = [(1, Decimal("500.00")), (2, Decimal(last_share))]

    with pytest.raises(SharesDoNotSumError):
        validate_exact_shares(Decimal("1200.00"), entries)


def test_exact_shares_reject_a_negative_share() -> None:
    entries = [(1, Decimal("-10.00")), (2, Decimal("60.00"))]

    with pytest.raises(NegativeShareError):
        validate_exact_shares(Decimal("50.00"), entries)


def test_exact_shares_reject_an_empty_list() -> None:
    with pytest.raises(NoParticipantsError):
        validate_exact_shares(Decimal("10.00"), [])


def test_exact_shares_reject_a_repeated_member() -> None:
    entries = [(1, Decimal("5.00")), (1, Decimal("5.00"))]

    with pytest.raises(DuplicateParticipantError):
        validate_exact_shares(Decimal("10.00"), entries)
