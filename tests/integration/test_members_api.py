"""Integration tests for the member endpoints."""

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import Trip

pytestmark = pytest.mark.integration


def test_adding_a_member_returns_it(client: TestClient, group_id: int) -> None:
    response = client.post(f"/api/v1/groups/{group_id}/members", json={"name": "Sandesh"})

    assert response.status_code == 201
    assert response.json()["name"] == "Sandesh"
    assert response.json()["group_id"] == group_id


def test_a_name_cannot_be_used_twice_in_the_same_group(client: TestClient, group_id: int) -> None:
    client.post(f"/api/v1/groups/{group_id}/members", json={"name": "Sandesh"})

    response = client.post(f"/api/v1/groups/{group_id}/members", json={"name": "Sandesh"})

    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_MEMBER_NAME"


def test_duplicate_names_are_detected_regardless_of_case(client: TestClient, group_id: int) -> None:
    """'sandesh' and 'Sandesh' are the same person to everybody except a database."""
    client.post(f"/api/v1/groups/{group_id}/members", json={"name": "Sandesh"})

    response = client.post(f"/api/v1/groups/{group_id}/members", json={"name": "sandesh"})

    assert response.status_code == 409


def test_the_same_name_may_be_used_in_a_different_group(client: TestClient, group_id: int) -> None:
    other_group = client.post("/api/v1/groups", json={"name": "Flat 3B"}).json()["id"]
    client.post(f"/api/v1/groups/{group_id}/members", json={"name": "Sandesh"})

    response = client.post(f"/api/v1/groups/{other_group}/members", json={"name": "Sandesh"})

    assert response.status_code == 201


def test_adding_a_member_to_a_missing_group_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/groups/9999/members", json={"name": "Sandesh"})

    assert response.status_code == 404
    assert response.json()["code"] == "GROUP_NOT_FOUND"


@pytest.mark.parametrize("name", ["", "   ", "x" * 81])
def test_invalid_member_names_are_rejected(client: TestClient, group_id: int, name: str) -> None:
    response = client.post(f"/api/v1/groups/{group_id}/members", json={"name": name})

    assert response.status_code == 422


def test_members_are_listed_in_the_order_they_were_added(client: TestClient, trip: Trip) -> None:
    names = [
        member["name"] for member in client.get(f"/api/v1/groups/{trip.group_id}/members").json()
    ]

    assert names == ["Sandesh", "Bikash", "Anita"]


def test_listing_members_of_a_missing_group_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/groups/9999/members").status_code == 404


def test_a_member_with_no_financial_history_can_be_removed(
    client: TestClient,
    trip: Trip,
) -> None:
    response = client.delete(f"/api/v1/groups/{trip.group_id}/members/{trip.anita}")

    assert response.status_code == 204
    remaining = [m["id"] for m in client.get(f"/api/v1/groups/{trip.group_id}/members").json()]
    assert trip.anita not in remaining


def test_a_member_who_paid_for_something_cannot_be_removed(
    client: TestClient,
    trip: Trip,
) -> None:
    """Removing them would silently change everybody else's balance."""
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

    response = client.delete(f"/api/v1/groups/{trip.group_id}/members/{trip.sandesh}")

    assert response.status_code == 409
    assert response.json()["code"] == "MEMBER_HAS_ACTIVITY"


def test_a_member_who_owes_a_share_cannot_be_removed(client: TestClient, trip: Trip) -> None:
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

    response = client.delete(f"/api/v1/groups/{trip.group_id}/members/{trip.anita}")

    assert response.status_code == 409


def test_a_member_involved_in_a_settlement_cannot_be_removed(
    client: TestClient,
    trip: Trip,
) -> None:
    client.post(
        f"/api/v1/groups/{trip.group_id}/settlements",
        json={"from_member_id": trip.anita, "to_member_id": trip.bikash, "amount": "10.00"},
    )

    response = client.delete(f"/api/v1/groups/{trip.group_id}/members/{trip.anita}")

    assert response.status_code == 409


def test_removing_a_member_of_another_group_returns_404(client: TestClient, trip: Trip) -> None:
    other_group = client.post("/api/v1/groups", json={"name": "Flat 3B"}).json()["id"]

    response = client.delete(f"/api/v1/groups/{other_group}/members/{trip.sandesh}")

    assert response.status_code == 404
    assert response.json()["code"] == "MEMBER_NOT_FOUND"
