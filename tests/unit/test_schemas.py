"""Unit tests for the request contracts.

These cover validation that happens before any router or database is involved.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.expense import ExpenseCreate, ExpenseShareRead
from app.schemas.group import GroupCreate
from app.schemas.member import MemberCreate
from app.schemas.settlement import SettlementCreate


def equal_expense(**overrides: object) -> dict[str, object]:
    """Return a valid EQUAL-split payload with the given fields replaced."""
    payload: dict[str, object] = {
        "description": "Hotel",
        "amount": "1000.00",
        "paid_by_id": 1,
        "split_type": "EQUAL",
        "participant_ids": [1, 2],
    }
    payload.update(overrides)
    return payload


def test_group_name_is_trimmed() -> None:
    assert GroupCreate(name="  Pokhara Trip  ").name == "Pokhara Trip"


def test_group_defaults_to_the_configured_currency() -> None:
    assert GroupCreate(name="Trip").currency == "NPR"


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_blank_group_names_are_rejected(name: str) -> None:
    with pytest.raises(ValidationError):
        GroupCreate(name=name)


def test_over_long_group_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GroupCreate(name="x" * 101)


def test_over_long_group_description_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GroupCreate(name="Trip", description="x" * 501)


@pytest.mark.parametrize("currency", ["npr", "NPRR", "N1R", ""])
def test_invalid_currency_codes_are_rejected(currency: str) -> None:
    with pytest.raises(ValidationError):
        GroupCreate(name="Trip", currency=currency)


@pytest.mark.parametrize("name", ["", "  "])
def test_blank_member_names_are_rejected(name: str) -> None:
    with pytest.raises(ValidationError):
        MemberCreate(name=name)


def test_over_long_member_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MemberCreate(name="x" * 81)


@pytest.mark.parametrize("amount", ["0", "-1.00", "10.005", "1000000.01"])
def test_invalid_expense_amounts_are_rejected(amount: str) -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(**equal_expense(amount=amount))


@pytest.mark.parametrize("description", ["", "   "])
def test_blank_expense_description_is_rejected(description: str) -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(**equal_expense(description=description))


def test_unknown_split_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(**equal_expense(split_type="HALF"))


def test_equal_split_requires_participants() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(**equal_expense(participant_ids=None))


def test_equal_split_rejects_an_exact_share_list() -> None:
    payload = equal_expense(shares=[{"member_id": 1, "share_amount": "1000.00"}])

    with pytest.raises(ValidationError):
        ExpenseCreate(**payload)


def test_exact_split_requires_shares() -> None:
    payload = equal_expense(split_type="EXACT", participant_ids=None)

    with pytest.raises(ValidationError):
        ExpenseCreate(**payload)


def test_exact_split_rejects_a_participant_list() -> None:
    payload = equal_expense(
        split_type="EXACT",
        shares=[{"member_id": 1, "share_amount": "1000.00"}],
    )

    with pytest.raises(ValidationError):
        ExpenseCreate(**payload)


def test_exact_split_rejects_a_negative_share() -> None:
    payload = equal_expense(
        split_type="EXACT",
        participant_ids=None,
        shares=[{"member_id": 1, "share_amount": "-1.00"}],
    )

    with pytest.raises(ValidationError):
        ExpenseCreate(**payload)


def test_settlement_amount_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        SettlementCreate(from_member_id=1, to_member_id=2, amount="0.00")


def test_over_long_settlement_note_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SettlementCreate(from_member_id=1, to_member_id=2, amount="5.00", note="x" * 201)


def test_money_is_serialised_as_a_two_decimal_string() -> None:
    """JSON numbers cannot represent money exactly, so amounts leave as strings."""
    share = ExpenseShareRead(member_id=1, member_name="Anita", share_amount=Decimal("333.3"))

    assert share.model_dump(mode="json")["share_amount"] == "333.30"
