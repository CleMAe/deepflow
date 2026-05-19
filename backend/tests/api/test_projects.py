"""
Project API integration tests — /api/v1/projects/*

Requires Authorization Bearer token on all endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.core.errors import ERR_AUTH_MISSING, ERR_PROJECT_FORBIDDEN, ERR_PROJECT_NOT_FOUND
from src.infra.db.models.user import User
from tests.factories.project import ProjectFactory
from tests.factories.user import UserFactory

PROJECTS_PREFIX = "/api/v1/projects"
DEFAULT_PASSWORD = "testpass123"


def assert_api_envelope(body: dict[str, Any], *, code: int = 0) -> None:
    assert "code" in body
    assert "message" in body
    assert "data" in body
    assert "request_id" in body
    assert isinstance(body["message"], str)
    assert isinstance(body["request_id"], str)
    assert body["code"] == code


class TestProjectsList:
    def test_list_projects_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project_factory(owner=auth_user, name="Alpha Project")
        project_factory(owner=auth_user, name="Beta Project")

        resp = api_client.get(PROJECTS_PREFIX, headers=auth_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["page"] == 1
        assert data["total"] >= 2
        names = {item["name"] for item in data["items"]}
        assert "Alpha Project" in names
        assert "Beta Project" in names

    def test_list_projects_without_token(self, api_client: TestClient) -> None:
        resp = api_client.get(PROJECTS_PREFIX)

        assert resp.status_code == 401
        body = resp.json()
        assert_api_envelope(body, code=ERR_AUTH_MISSING)


class TestProjectsCreate:
    def test_create_project_success(
        self, api_client: TestClient, auth_headers: dict[str, str], auth_user: User
    ) -> None:
        payload = {
            "name": "New ML Project",
            "description": "Integration test project",
            "storage_quota": 20480,
        }
        resp = api_client.post(PROJECTS_PREFIX, json=payload, headers=auth_headers)

        assert resp.status_code == 201
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["storage_quota"] == payload["storage_quota"]
        assert data["storage_used"] == 0
        assert data["owner_id"] == str(auth_user.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_project_without_token(self, api_client: TestClient) -> None:
        resp = api_client.post(PROJECTS_PREFIX, json={"name": "No Auth"})

        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_MISSING)


class TestProjectsGet:
    def test_get_project_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user, name="Detail Project")

        resp = api_client.get(f"{PROJECTS_PREFIX}/{project.id}", headers=auth_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        assert body["data"]["id"] == str(project.id)
        assert body["data"]["name"] == "Detail Project"

    def test_get_project_not_found(self, api_client: TestClient, auth_headers: dict[str, str]) -> None:
        missing_id = uuid.uuid4()
        resp = api_client.get(f"{PROJECTS_PREFIX}/{missing_id}", headers=auth_headers)

        assert resp.status_code == 404
        assert_api_envelope(resp.json(), code=ERR_PROJECT_NOT_FOUND)

    def test_get_project_without_token(
        self,
        api_client: TestClient,
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        resp = api_client.get(f"{PROJECTS_PREFIX}/{project.id}")

        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_MISSING)

    def test_get_project_forbidden_other_owner(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
        project_factory: type[ProjectFactory],
    ) -> None:
        owner = user_factory(username="proj_owner_a")
        intruder = user_factory(username="proj_intruder_b")
        project = project_factory(owner=owner)

        login = api_client.post(
            "/api/v1/auth/login",
            json={"username": intruder.username, "password": DEFAULT_PASSWORD},
        )
        headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

        resp = api_client.get(f"{PROJECTS_PREFIX}/{project.id}", headers=headers)

        assert resp.status_code == 403
        assert_api_envelope(resp.json(), code=ERR_PROJECT_FORBIDDEN)


class TestProjectsUpdate:
    def test_update_project_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user, name="Before Update")
        payload = {"name": "After Update", "description": "Updated desc"}

        resp = api_client.put(
            f"{PROJECTS_PREFIX}/{project.id}",
            json=payload,
            headers=auth_headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        assert body["data"]["name"] == "After Update"
        assert body["data"]["description"] == "Updated desc"

    def test_update_project_not_found(self, api_client: TestClient, auth_headers: dict[str, str]) -> None:
        resp = api_client.put(
            f"{PROJECTS_PREFIX}/{uuid.uuid4()}",
            json={"name": "Ghost"},
            headers=auth_headers,
        )

        assert resp.status_code == 404
        assert_api_envelope(resp.json(), code=ERR_PROJECT_NOT_FOUND)


class TestProjectsDelete:
    def test_delete_project_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user, name="To Delete")

        del_resp = api_client.delete(f"{PROJECTS_PREFIX}/{project.id}", headers=auth_headers)
        assert del_resp.status_code == 200
        assert_api_envelope(del_resp.json(), code=0)

        get_resp = api_client.get(f"{PROJECTS_PREFIX}/{project.id}", headers=auth_headers)
        assert get_resp.status_code == 404
        assert_api_envelope(get_resp.json(), code=ERR_PROJECT_NOT_FOUND)

    def test_delete_project_not_found(self, api_client: TestClient, auth_headers: dict[str, str]) -> None:
        resp = api_client.delete(f"{PROJECTS_PREFIX}/{uuid.uuid4()}", headers=auth_headers)

        assert resp.status_code == 404
        assert_api_envelope(resp.json(), code=ERR_PROJECT_NOT_FOUND)

    def test_delete_project_without_token(
        self,
        api_client: TestClient,
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        resp = api_client.delete(f"{PROJECTS_PREFIX}/{project.id}")

        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_MISSING)
