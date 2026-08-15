"""Integration tests for the health endpoint and framework-level errors."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_health_reports_the_service_identity(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "fairshare-api", "version": "1.0.0"}


def test_unknown_route_returns_the_standard_error_envelope(client: TestClient) -> None:
    """Even framework-generated errors carry a machine-readable code (GUIDE FR-33)."""
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_wrong_method_is_rejected(client: TestClient) -> None:
    response = client.put("/api/v1/groups")

    assert response.status_code == 405
    assert "code" in response.json()


def test_openapi_document_describes_every_endpoint(client: TestClient) -> None:
    """The documentation is generated from the code, so it cannot drift (GUIDE A-3)."""
    schema = client.get("/openapi.json").json()

    operations = sum(len(methods) for methods in schema["paths"].values())
    assert operations == 18
    assert schema["info"]["title"] == "FairShare API"
