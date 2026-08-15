"""Fixtures for the integration suite.

Every test starts from an empty database: the tables are truncated and their
identity sequences restarted before each test, so results never depend on the
order tests happen to run in (GUIDE §13.2).
"""

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.main import app
from app.models import Base

# Ordered so the statement reads naturally; CASCADE handles the dependencies.
TABLES = ("expense_shares", "expenses", "settlements", "members", "groups")


@pytest.fixture(scope="session", autouse=True)
def database_schema() -> Iterator[None]:
    """Create the schema once for the session and remove it afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables(database_schema: None) -> None:
    """Empty every table before each test."""
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A test client running the application's full startup and shutdown."""
    with TestClient(app) as test_client:
        yield test_client


@dataclass(frozen=True)
class Trip:
    """A group with three members, the setup most tests need."""

    group_id: int
    sandesh: int
    bikash: int
    anita: int

    @property
    def everyone(self) -> list[int]:
        return [self.sandesh, self.bikash, self.anita]


@pytest.fixture
def group_id(client: TestClient) -> int:
    """An empty group."""
    response = client.post("/api/v1/groups", json={"name": "Pokhara Trip"})
    return response.json()["id"]


@pytest.fixture
def trip(client: TestClient, group_id: int) -> Trip:
    """A group with three members added in a known order."""
    member_ids = [
        client.post(f"/api/v1/groups/{group_id}/members", json={"name": name}).json()["id"]
        for name in ("Sandesh", "Bikash", "Anita")
    ]
    return Trip(group_id, *member_ids)
