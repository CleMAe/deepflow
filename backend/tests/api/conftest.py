"""Shared fixtures for API integration tests."""

from __future__ import annotations

import pytest

from src.infra.db.models.user import User
from tests.factories.user import UserFactory

# P6 placeholder: deps.get_current_user_id accepts any Bearer token when login is absent.
AUTH_HEADERS = {"Authorization": "Bearer test-token"}

P6_SKIP = pytest.mark.skip(reason="Waiting for P6 implementation")


@pytest.fixture
def auth_user(user_factory: type[UserFactory]) -> User:
    return user_factory()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return dict(AUTH_HEADERS)
