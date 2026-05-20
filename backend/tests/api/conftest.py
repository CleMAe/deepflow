"""Shared fixtures for API integration tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.infra.db.models.user import User
from tests.factories.user import UserFactory


@pytest.fixture
def auth_user(user_factory: type[UserFactory]) -> User:
    return user_factory()


@pytest.fixture
def auth_headers(
    api_client: TestClient,
    auth_user: User,
) -> dict[str, str]:
    """Obtain a real JWT by logging in with the auth_user's credentials."""
    resp = api_client.post(
        "/api/v1/auth/login",
        json={"username": auth_user.username, "password": "testpass123"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
