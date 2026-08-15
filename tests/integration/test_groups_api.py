"""Integration tests for the group endpoints."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_creating_a_group_returns_it_with_defaults(client: TestClient) -> None:
    response = client.post("/api/v1/groups", json={"name": "Pokhara Trip"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Pokhara Trip"
    assert body["currency"] == "NPR"
    assert body["description"] is None
    assert body["id"] > 0


def test_creating_a_group_accepts_a_description_and_currency(client: TestClient) -> None:
    payload = {"name": "Flat 3B", "description": "Monthly bills", "currency": "USD"}

    body = client.post("/api/v1/groups", json=payload).json()

    assert body["description"] == "Monthly bills"
    assert body["currency"] == "USD"


@pytest.mark.parametrize("payload", [{"name": ""}, {"name": "   "}, {"name": "x" * 101}, {}])
def test_invalid_group_payloads_are_rejected(client: TestClient, payload: dict) -> None:
    response = client.post("/api/v1/groups", json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_groups_are_listed_newest_first(client: TestClient) -> None:
    for name in ("First", "Second", "Third"):
        client.post("/api/v1/groups", json={"name": name})

    names = [group["name"] for group in client.get("/api/v1/groups").json()]

    assert names == ["Third", "Second", "First"]


def test_group_detail_includes_its_members(client: TestClient, group_id: int) -> None:
    client.post(f"/api/v1/groups/{group_id}/members", json={"name": "Sandesh"})

    body = client.get(f"/api/v1/groups/{group_id}").json()

    assert [member["name"] for member in body["members"]] == ["Sandesh"]


def test_requesting_a_missing_group_returns_a_documented_error(client: TestClient) -> None:
    response = client.get("/api/v1/groups/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Group 9999 does not exist", "code": "GROUP_NOT_FOUND"}


def test_updating_only_the_name_leaves_the_description_untouched(client: TestClient) -> None:
    created = client.post(
        "/api/v1/groups",
        json={"name": "Trip", "description": "Keep me"},
    ).json()

    updated = client.patch(f"/api/v1/groups/{created['id']}", json={"name": "Trip 2026"}).json()

    assert updated["name"] == "Trip 2026"
    assert updated["description"] == "Keep me"


def test_updating_a_missing_group_returns_404(client: TestClient) -> None:
    response = client.patch("/api/v1/groups/9999", json={"name": "Nope"})

    assert response.status_code == 404


def test_updating_with_an_invalid_name_is_rejected(client: TestClient, group_id: int) -> None:
    response = client.patch(f"/api/v1/groups/{group_id}", json={"name": "  "})

    assert response.status_code == 422


def test_deleting_a_group_makes_it_unreachable(client: TestClient, group_id: int) -> None:
    assert client.delete(f"/api/v1/groups/{group_id}").status_code == 204
    assert client.get(f"/api/v1/groups/{group_id}").status_code == 404


def test_deleting_a_group_removes_its_members_and_expenses(client: TestClient, trip) -> None:
    """Deleting a group must not leave orphaned financial records behind."""
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

    client.delete(f"/api/v1/groups/{trip.group_id}")

    assert client.get(f"/api/v1/expenses/{expense['id']}").status_code == 404
    assert client.get(f"/api/v1/groups/{trip.group_id}/members").status_code == 404


def test_deleting_a_missing_group_returns_404(client: TestClient) -> None:
    assert client.delete("/api/v1/groups/9999").status_code == 404
