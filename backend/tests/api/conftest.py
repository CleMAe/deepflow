"""Shared fixtures for API integration tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.infra.db.models.user import User
from tests.conftest import AUTH_PREFIX
from tests.factories.user import UserFactory

DEFAULT_PASSWORD = "testpass123"


@pytest.fixture
def auth_user(user_factory: type[UserFactory]) -> User:
    return user_factory()


@pytest.fixture
def auth_headers(api_client: TestClient, auth_user: User) -> dict[str, str]:
    resp = api_client.post(
        f"{AUTH_PREFIX}/login",
        json={"username": auth_user.username, "password": DEFAULT_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
