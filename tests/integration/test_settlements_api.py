"""Integration tests for recording settlements."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import Trip

pytestmark = pytest.mark.integration


def settle(client: TestClient, trip: Trip, **overrides: object):
    payload: dict[str, object] = {
        "from_member_id": trip.bikash,
        "to_member_id": trip.sandesh,
        "amount": "100.00",
    }
    payload.update(overrides)
    return client.post(f"/api/v1/groups/{trip.group_id}/settlements", json=payload)


def test_recording_a_payment_returns_it(client: TestClient, trip: Trip) -> None:
    response = settle(client, trip, note="Paid by eSewa")

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "100.00"
    assert body["note"] == "Paid by eSewa"
    assert body["from_member_id"] == trip.bikash


def test_a_payment_clears_the_debt_it_covers(client: TestClient, trip: Trip) -> None:
    client.post(
        f"/api/v1/groups/{trip.group_id}/expenses",
        json={
            "description": "Hotel",
            "amount": "300.00",
            "paid_by_id": trip.sandesh,
            "split_type": "EQUAL",
            "participant_ids": trip.everyone,
        },
    )

    settle(client, trip)

    balances = {
        entry["member_id"]: Decimal(entry["balance"])
        for entry in client.get(f"/api/v1/groups/{trip.group_id}/balances").json()["balances"]
    }
    assert balances[trip.bikash] == Decimal("0.00")
    assert balances[trip.sandesh] == Decimal("100.00")
    assert sum(balances.values()) == Decimal("0.00")


def test_a_member_cannot_pay_themselves(client: TestClient, trip: Trip) -> None:
    response = settle(client, trip, from_member_id=trip.sandesh, to_member_id=trip.sandesh)

    assert response.status_code == 422
    assert response.json()["code"] == "SAME_MEMBER_SETTLEMENT"


@pytest.mark.parametrize("field", ["from_member_id", "to_member_id"])
def test_both_members_must_belong_to_the_group(
    client: TestClient,
    trip: Trip,
    field: str,
) -> None:
    response = settle(client, trip, **{field: 9999})

    assert response.status_code == 422
    assert response.json()["code"] == "MEMBER_NOT_IN_GROUP"


@pytest.mark.parametrize("amount", ["0.00", "-10.00", "10.001"])
def test_invalid_amounts_are_rejected(client: TestClient, trip: Trip, amount: str) -> None:
    response = settle(client, trip, amount=amount)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_recording_a_payment_in_a_missing_group_returns_404(client: TestClient) -> None:
    payload = {"from_member_id": 1, "to_member_id": 2, "amount": "10.00"}

    response = client.post("/api/v1/groups/9999/settlements", json=payload)

    assert response.status_code == 404


def test_settlements_are_listed_newest_first(client: TestClient, trip: Trip) -> None:
    settle(client, trip, amount="10.00")
    settle(client, trip, amount="20.00")

    listed = client.get(f"/api/v1/groups/{trip.group_id}/settlements").json()

    assert [item["amount"] for item in listed] == ["20.00", "10.00"]


def test_listing_settlements_of_a_missing_group_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/groups/9999/settlements").status_code == 404
