"""Integration tests for balances, settlement plans and summaries."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import Trip

pytestmark = pytest.mark.integration


def add_expense(client: TestClient, trip: Trip, payer: int, amount: str) -> None:
    client.post(
        f"/api/v1/groups/{trip.group_id}/expenses",
        json={
            "description": "Shared cost",
            "amount": amount,
            "paid_by_id": payer,
            "split_type": "EQUAL",
            "participant_ids": trip.everyone,
        },
    )


def balances_of(client: TestClient, trip: Trip) -> dict[int, Decimal]:
    body = client.get(f"/api/v1/groups/{trip.group_id}/balances").json()
    return {entry["member_id"]: Decimal(entry["balance"]) for entry in body["balances"]}


def test_a_group_without_expenses_has_only_zero_balances(
    client: TestClient,
    trip: Trip,
) -> None:
    assert set(balances_of(client, trip).values()) == {Decimal("0.00")}


def test_every_member_appears_even_with_no_activity(client: TestClient, trip: Trip) -> None:
    add_expense(client, trip, trip.sandesh, "300.00")

    assert sorted(balances_of(client, trip)) == sorted(trip.everyone)


def test_the_payer_is_owed_what_the_others_consumed(client: TestClient, trip: Trip) -> None:
    add_expense(client, trip, trip.sandesh, "300.00")

    balances = balances_of(client, trip)

    assert balances[trip.sandesh] == Decimal("200.00")
    assert balances[trip.bikash] == Decimal("-100.00")
    assert balances[trip.anita] == Decimal("-100.00")


def test_balances_always_sum_to_zero(client: TestClient, trip: Trip) -> None:
    """The accounting invariant, checked end to end (GUIDE FR-23)."""
    add_expense(client, trip, trip.sandesh, "1000.00")
    add_expense(client, trip, trip.bikash, "755.55")
    add_expense(client, trip, trip.anita, "0.07")

    assert sum(balances_of(client, trip).values()) == Decimal("0.00")


def test_deleting_an_expense_updates_the_balances(client: TestClient, trip: Trip) -> None:
    expense = client.post(
        f"/api/v1/groups/{trip.group_id}/expenses",
        json={
            "description": "Hotel",
            "amount": "300.00",
            "paid_by_id": trip.sandesh,
            "split_type": "EQUAL",
            "participant_ids": trip.everyone,
        },
    ).json()

    client.delete(f"/api/v1/expenses/{expense['id']}")

    assert set(balances_of(client, trip).values()) == {Decimal("0.00")}


def test_balances_of_a_missing_group_return_404(client: TestClient) -> None:
    assert client.get("/api/v1/groups/9999/balances").status_code == 404


def test_a_settled_group_has_an_empty_plan(client: TestClient, trip: Trip) -> None:
    body = client.get(f"/api/v1/groups/{trip.group_id}/settlement-plan").json()

    assert body["transfers"] == []
    assert body["transfer_count"] == 0


def test_the_plan_names_both_sides_of_each_payment(client: TestClient, trip: Trip) -> None:
    add_expense(client, trip, trip.sandesh, "300.00")

    transfers = client.get(f"/api/v1/groups/{trip.group_id}/settlement-plan").json()["transfers"]

    assert {transfer["to_member_name"] for transfer in transfers} == {"Sandesh"}
    assert {transfer["from_member_name"] for transfer in transfers} == {"Bikash", "Anita"}
    assert all(transfer["amount"] == "100.00" for transfer in transfers)


def test_the_plan_never_exceeds_one_payment_per_member_minus_one(
    client: TestClient,
    trip: Trip,
) -> None:
    add_expense(client, trip, trip.sandesh, "1000.00")
    add_expense(client, trip, trip.bikash, "250.00")

    body = client.get(f"/api/v1/groups/{trip.group_id}/settlement-plan").json()

    assert body["transfer_count"] <= len(trip.everyone) - 1


def test_a_plan_for_a_missing_group_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/groups/9999/settlement-plan").status_code == 404


def test_the_summary_reports_group_wide_totals(client: TestClient, trip: Trip) -> None:
    add_expense(client, trip, trip.sandesh, "300.00")
    add_expense(client, trip, trip.bikash, "600.00")

    body = client.get(f"/api/v1/groups/{trip.group_id}/summary").json()

    assert body["member_count"] == 3
    assert body["expense_count"] == 2
    assert body["total_spend"] == "900.00"
    assert body["group_name"] == "Pokhara Trip"


def test_the_summary_reports_paid_and_owed_per_member(client: TestClient, trip: Trip) -> None:
    add_expense(client, trip, trip.sandesh, "300.00")

    members = {
        entry["member_id"]: entry
        for entry in client.get(f"/api/v1/groups/{trip.group_id}/summary").json()["members"]
    }

    assert members[trip.sandesh]["total_paid"] == "300.00"
    assert members[trip.sandesh]["total_owed"] == "100.00"
    assert members[trip.anita]["total_paid"] == "0.00"
    assert members[trip.anita]["balance"] == "-100.00"


def test_a_summary_for_a_missing_group_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/groups/9999/summary").status_code == 404
