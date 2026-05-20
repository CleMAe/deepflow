"""Project API integration tests — /api/v1/projects/*"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient

from src.infra.db.models.user import User
from tests.factories.project import ProjectFactory
from tests.factories.user import UserFactory


def assert_api_envelope(body: dict[str, Any], *, code: int = 0) -> None:
    assert "code" in body
    assert "message" in body
    assert "data" in body
    assert "request_id" in body
    assert isinstance(body["message"], str)
    assert isinstance(body["request_id"], str)
    assert body["code"] == code


ERR_PROJECT_NOT_FOUND = 20_002_001  # project module
ERR_PROJECT_FORBIDDEN = 20_003_001
ERR_PROJECT_FORBIDDEN = 20_003_001
ERR_AUTH_MISSING = 10_003_001


class TestProjectList:
    def test_list_projects_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project_factory(owner=auth_user, name="My Project")
        project_factory(owner=auth_user, name="Another Project")

        resp = api_client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["total"] >= 2
        names = {item["name"] for item in data["items"]}
        assert "My Project" in names
        assert "Another Project" in names

    def test_list_projects_excludes_other_owner(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        user_factory: type[UserFactory],
        project_factory: type[ProjectFactory],
    ) -> None:
        other = user_factory(username="other_owner")
        project_factory(owner=other, name="Other's Project")
        project_factory(owner=auth_user, name="My Project")

        resp = api_client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        names = {item["name"] for item in items}
        assert "My Project" in names
        assert "Other's Project" not in names

    def test_list_projects_without_token(
        self,
        api_client: TestClient,
    ) -> None:
        resp = api_client.get("/api/v1/projects")
        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_MISSING)

    def test_list_projects_search(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project_factory(owner=auth_user, name="Alpha Project")
        project_factory(owner=auth_user, name="Beta Project")

        resp = api_client.get("/api/v1/projects?search=Alpha", headers=auth_headers)
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        names = {item["name"] for item in items}
        assert "Alpha Project" in names
        assert "Beta Project" not in names


class TestProjectCreate:
    def test_create_project_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        resp = api_client.post(
            "/api/v1/projects",
            json={"name": "New Project", "description": "Test project"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["name"] == "New Project"
        assert data["description"] == "Test project"
        assert "id" in data

    def test_create_project_without_token(
        self,
        api_client: TestClient,
    ) -> None:
        resp = api_client.post(
            "/api/v1/projects",
            json={"name": "No Auth Project"},
        )
        assert resp.status_code == 401


class TestProjectGet:
    def test_get_project_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user, name="Detail Project")
        resp = api_client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        assert body["data"]["name"] == "Detail Project"

    def test_get_project_not_found(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        missing_id = uuid.uuid4()
        resp = api_client.get(f"/api/v1/projects/{missing_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_project_forbidden_other_owner(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        user_factory: type[UserFactory],
        project_factory: type[ProjectFactory],
    ) -> None:
        other = user_factory(username="other_get")
        project = project_factory(owner=other)
        resp = api_client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        assert resp.status_code == 404  # not owned → not found (no info leak)


class TestProjectUpdate:
    def test_update_project_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user, name="Before Update")
        resp = api_client.put(
            f"/api/v1/projects/{project.id}",
            json={"name": "After Update", "description": "Updated"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "After Update"
        assert data["description"] == "Updated"

    def test_update_project_not_found(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        resp = api_client.put(
            f"/api/v1/projects/{uuid.uuid4()}",
            json={"name": "Ghost"},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestProjectDelete:
    def test_delete_project_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user, name="To Delete")
        del_resp = api_client.delete(f"/api/v1/projects/{project.id}", headers=auth_headers)
        assert del_resp.status_code == 200

        get_resp = api_client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_project_forbidden_other_owner(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        user_factory: type[UserFactory],
        project_factory: type[ProjectFactory],
    ) -> None:
        other = user_factory(username="other_del")
        project = project_factory(owner=other)
        resp = api_client.delete(f"/api/v1/projects/{project.id}", headers=auth_headers)
        assert resp.status_code == 404
