"""Integration tests for the expense endpoints."""

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import Trip

pytestmark = pytest.mark.integration


def equal_expense(trip: Trip, **overrides: object) -> dict[str, object]:
    """Build a valid EQUAL-split payload for the trip fixture."""
    payload: dict[str, object] = {
        "description": "Hotel in Pokhara",
        "amount": "1000.00",
        "paid_by_id": trip.sandesh,
        "split_type": "EQUAL",
        "participant_ids": trip.everyone,
    }
    payload.update(overrides)
    return payload


def post_expense(client: TestClient, trip: Trip, **overrides: object):
    return client.post(
        f"/api/v1/groups/{trip.group_id}/expenses", json=equal_expense(trip, **overrides)
    )


def test_an_equal_split_that_does_not_divide_evenly_still_adds_up(
    client: TestClient,
    trip: Trip,
) -> None:
    """1000 between three people: the odd paisa goes to the lowest member id."""
    response = post_expense(client, trip)

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "1000.00"
    assert [share["share_amount"] for share in body["shares"]] == ["333.34", "333.33", "333.33"]
    assert sum(float(share["share_amount"]) for share in body["shares"]) == 1000.00


def test_the_response_names_every_participant(client: TestClient, trip: Trip) -> None:
    body = post_expense(client, trip).json()

    assert [share["member_name"] for share in body["shares"]] == ["Sandesh", "Bikash", "Anita"]
    assert body["paid_by_name"] == "Sandesh"


def test_an_exact_split_is_stored_as_given(client: TestClient, trip: Trip) -> None:
    payload = {
        "description": "Dinner",
        "amount": "1200.00",
        "paid_by_id": trip.bikash,
        "split_type": "EXACT",
        "shares": [
            {"member_id": trip.sandesh, "share_amount": "500.00"},
            {"member_id": trip.bikash, "share_amount": "700.00"},
        ],
    }

    body = client.post(f"/api/v1/groups/{trip.group_id}/expenses", json=payload).json()

    assert [share["share_amount"] for share in body["shares"]] == ["500.00", "700.00"]


def test_exact_shares_that_do_not_add_up_are_rejected(client: TestClient, trip: Trip) -> None:
    payload = {
        "description": "Dinner",
        "amount": "1200.00",
        "paid_by_id": trip.bikash,
        "split_type": "EXACT",
        "shares": [
            {"member_id": trip.sandesh, "share_amount": "500.00"},
            {"member_id": trip.bikash, "share_amount": "699.99"},
        ],
    }

    response = client.post(f"/api/v1/groups/{trip.group_id}/expenses", json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "SHARES_DO_NOT_SUM"


def test_a_payer_from_outside_the_group_is_rejected(client: TestClient, trip: Trip) -> None:
    response = post_expense(client, trip, paid_by_id=9999)

    assert response.status_code == 422
    assert response.json()["code"] == "PAYER_NOT_IN_GROUP"


def test_a_participant_from_outside_the_group_is_rejected(client: TestClient, trip: Trip) -> None:
    response = post_expense(client, trip, participant_ids=[trip.sandesh, 9999])

    assert response.status_code == 422
    assert response.json()["code"] == "PARTICIPANT_NOT_IN_GROUP"


def test_a_repeated_participant_is_rejected(client: TestClient, trip: Trip) -> None:
    response = post_expense(client, trip, participant_ids=[trip.sandesh, trip.sandesh])

    assert response.status_code == 422
    assert response.json()["code"] == "DUPLICATE_PARTICIPANT"


def test_an_expense_with_no_participants_is_rejected(client: TestClient, trip: Trip) -> None:
    response = post_expense(client, trip, participant_ids=[])

    assert response.status_code == 422
    assert response.json()["code"] == "NO_PARTICIPANTS"


@pytest.mark.parametrize("amount", ["0.00", "-5.00", "10.005"])
def test_invalid_amounts_are_rejected(client: TestClient, trip: Trip, amount: str) -> None:
    response = post_expense(client, trip, amount=amount)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_recording_an_expense_in_a_missing_group_returns_404(client: TestClient) -> None:
    payload = {
        "description": "Hotel",
        "amount": "10.00",
        "paid_by_id": 1,
        "split_type": "EQUAL",
        "participant_ids": [1],
    }

    response = client.post("/api/v1/groups/9999/expenses", json=payload)

    assert response.status_code == 404


def test_a_single_expense_can_be_read_back(client: TestClient, trip: Trip) -> None:
    created = post_expense(client, trip).json()

    body = client.get(f"/api/v1/expenses/{created['id']}").json()

    assert body == created


def test_reading_a_missing_expense_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/expenses/9999")

    assert response.status_code == 404
    assert response.json()["code"] == "EXPENSE_NOT_FOUND"


def test_expenses_are_listed_newest_first(client: TestClient, trip: Trip) -> None:
    for description in ("First", "Second", "Third"):
        post_expense(client, trip, description=description)

    listed = client.get(f"/api/v1/groups/{trip.group_id}/expenses").json()

    assert [expense["description"] for expense in listed] == ["Third", "Second", "First"]


def test_listing_can_be_paginated(client: TestClient, trip: Trip) -> None:
    for description in ("First", "Second", "Third"):
        post_expense(client, trip, description=description)

    page = client.get(
        f"/api/v1/groups/{trip.group_id}/expenses",
        params={"limit": 1, "offset": 1},
    ).json()

    assert [expense["description"] for expense in page] == ["Second"]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_invalid_pagination_is_rejected(client: TestClient, trip: Trip, params: dict) -> None:
    response = client.get(f"/api/v1/groups/{trip.group_id}/expenses", params=params)

    assert response.status_code == 422


def test_deleting_an_expense_removes_it(client: TestClient, trip: Trip) -> None:
    created = post_expense(client, trip).json()

    assert client.delete(f"/api/v1/expenses/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/expenses/{created['id']}").status_code == 404


def test_deleting_a_missing_expense_returns_404(client: TestClient) -> None:
    assert client.delete("/api/v1/expenses/9999").status_code == 404
