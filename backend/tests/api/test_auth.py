"""
Auth API integration tests — /api/v1/auth/*

Covers login, register, refresh, me per openapi.yaml and P9 contract.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.core.errors import ERR_AUTH_DUPLICATE_USER, ERR_AUTH_INVALID
from app.core.security import hash_password
from src.infra.db.models.user import UserRole
from tests.conftest import AUTH_PREFIX
from tests.factories.user import UserFactory


def assert_api_envelope(body: dict[str, Any], *, code: int = 0) -> None:
    """Assert unified response shape {code, message, data, request_id}."""
    assert "code" in body
    assert "message" in body
    assert "data" in body
    assert "request_id" in body
    assert isinstance(body["message"], str)
    assert isinstance(body["request_id"], str)
    assert body["code"] == code


def _register_payload(username: str, password: str = "testpass123", role: str = "developer") -> dict:
    return {"username": username, "password": password, "role": role}


class TestAuthRegister:
    def test_register_success(self, api_client: TestClient) -> None:
        resp = api_client.post(f"{AUTH_PREFIX}/register", json=_register_payload("new_user_reg"))

        assert resp.status_code == 201
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["username"] == "new_user_reg"
        assert data["role"] == "developer"
        assert "id" in data
        assert "created_at" in data

    def test_register_duplicate_username(self, api_client: TestClient, user_factory: type[UserFactory]) -> None:
        user_factory(username="dup_user", password_hash=hash_password("testpass123"))

        resp = api_client.post(f"{AUTH_PREFIX}/register", json=_register_payload("dup_user"))

        assert resp.status_code == 400
        body = resp.json()
        assert_api_envelope(body, code=ERR_AUTH_DUPLICATE_USER)
        assert "already" in body["message"].lower() or "registered" in body["message"].lower()

    def test_register_validation_short_password(self, api_client: TestClient) -> None:
        resp = api_client.post(
            f"{AUTH_PREFIX}/register",
            json={"username": "short_pw", "password": "123", "role": "developer"},
        )

        assert resp.status_code == 400
        body = resp.json()
        assert "code" in body
        assert "message" in body
        assert "request_id" in body
        assert body["code"] != 0


class TestAuthLogin:
    def test_login_success(self, api_client: TestClient, user_factory: type[UserFactory]) -> None:
        password = "testpass123"
        user_factory(username="login_ok", password_hash=hash_password(password))

        resp = api_client.post(
            f"{AUTH_PREFIX}/login",
            json={"username": "login_ok", "password": password},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    def test_login_wrong_password(self, api_client: TestClient, user_factory: type[UserFactory]) -> None:
        user_factory(username="login_bad", password_hash=hash_password("correct_pass"))

        resp = api_client.post(
            f"{AUTH_PREFIX}/login",
            json={"username": "login_bad", "password": "wrong_pass"},
        )

        assert resp.status_code == 401
        body = resp.json()
        assert_api_envelope(body, code=ERR_AUTH_INVALID)

    def test_login_unknown_user(self, api_client: TestClient) -> None:
        resp = api_client.post(
            f"{AUTH_PREFIX}/login",
            json={"username": "no_such_user", "password": "testpass123"},
        )

        assert resp.status_code == 401
        body = resp.json()
        assert_api_envelope(body, code=ERR_AUTH_INVALID)


class TestAuthRefresh:
    def test_refresh_success(self, api_client: TestClient, user_factory: type[UserFactory]) -> None:
        password = "testpass123"
        user_factory(username="refresh_user", password_hash=hash_password(password))

        login_resp = api_client.post(
            f"{AUTH_PREFIX}/login",
            json={"username": "refresh_user", "password": password},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        resp = api_client.post(f"{AUTH_PREFIX}/refresh", json={"refresh_token": refresh_token})

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"

    def test_refresh_invalid_token(self, api_client: TestClient) -> None:
        resp = api_client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": "not-a-valid-jwt"},
        )

        assert resp.status_code == 401
        body = resp.json()
        assert_api_envelope(body, code=ERR_AUTH_INVALID)


class TestAuthMe:
    def test_me_success(self, api_client: TestClient, user_factory: type[UserFactory]) -> None:
        password = "testpass123"
        user = user_factory(
            username="me_user",
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )

        login_resp = api_client.post(
            f"{AUTH_PREFIX}/login",
            json={"username": "me_user", "password": password},
        )
        token = login_resp.json()["data"]["access_token"]

        resp = api_client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["username"] == "me_user"
        assert data["role"] == "admin"
        assert data["id"] == str(user.id)

    def test_me_missing_token(self, api_client: TestClient) -> None:
        resp = api_client.get(f"{AUTH_PREFIX}/me")

        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] != 0
        assert "message" in body
        assert "request_id" in body

    def test_me_invalid_token(self, api_client: TestClient) -> None:
        resp = api_client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": "Bearer invalid.token.value"},
        )

        assert resp.status_code == 401
        body = resp.json()
        assert_api_envelope(body, code=ERR_AUTH_INVALID)
