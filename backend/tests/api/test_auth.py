"""Auth API integration tests — /api/v1/auth/*"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from src.infra.db.models.user import User
from tests.factories.user import UserFactory


def assert_api_envelope(body: dict[str, Any], *, code: int = 0) -> None:
    assert "code" in body
    assert "message" in body
    assert "data" in body
    assert "request_id" in body
    assert isinstance(body["message"], str)
    assert isinstance(body["request_id"], str)
    assert body["code"] == code


ERR_AUTH_CREDENTIALS = 10_002_001
ERR_AUTH_INVALID = 10_003_002
ERR_AUTH_USERNAME_EXISTS = 10_004_001


class TestRegister:
    def test_register_success(
        self,
        api_client: TestClient,
    ) -> None:
        resp = api_client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "secure123", "role": "developer"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["username"] == "newuser"
        assert data["role"] == "developer"
        assert "id" in data

    def test_register_duplicate_username(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
    ) -> None:
        user_factory(username="duplicate")
        resp = api_client.post(
            "/api/v1/auth/register",
            json={"username": "duplicate", "password": "another123"},
        )
        assert resp.status_code == 400
        assert_api_envelope(resp.json(), code=ERR_AUTH_USERNAME_EXISTS)

    def test_register_password_too_short(
        self,
        api_client: TestClient,
    ) -> None:
        resp = api_client.post(
            "/api/v1/auth/register",
            json={"username": "shortpw", "password": "abc"},
        )
        assert resp.status_code in (400, 422)


class TestLogin:
    def test_login_success(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
    ) -> None:
        user_factory(username="loginuser")
        resp = api_client.post(
            "/api/v1/auth/login",
            json={"username": "loginuser", "password": "testpass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)

    def test_login_wrong_password(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
    ) -> None:
        user_factory(username="wrongpw_user")
        resp = api_client.post(
            "/api/v1/auth/login",
            json={"username": "wrongpw_user", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_CREDENTIALS)

    def test_login_nonexistent_user(
        self,
        api_client: TestClient,
    ) -> None:
        resp = api_client.post(
            "/api/v1/auth/login",
            json={"username": "ghost", "password": "doesnotmatter"},
        )
        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_CREDENTIALS)


class TestRefresh:
    def test_refresh_success(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
    ) -> None:
        user_factory(username="refreshuser")
        login_resp = api_client.post(
            "/api/v1/auth/login",
            json={"username": "refreshuser", "password": "testpass123"},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        resp = api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(
        self,
        api_client: TestClient,
    ) -> None:
        resp = api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_INVALID)

    def test_refresh_with_access_token_fails(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
    ) -> None:
        user_factory(username="wrongrefreshtype")
        login_resp = api_client.post(
            "/api/v1/auth/login",
            json={"username": "wrongrefreshtype", "password": "testpass123"},
        )
        access_token = login_resp.json()["data"]["access_token"]

        resp = api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
    ) -> None:
        resp = api_client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["username"] == auth_user.username

    def test_me_without_token(
        self,
        api_client: TestClient,
    ) -> None:
        resp = api_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(
        self,
        api_client: TestClient,
    ) -> None:
        resp = api_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401
