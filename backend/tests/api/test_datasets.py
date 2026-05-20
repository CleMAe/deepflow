"""
Dataset API integration tests — /api/v1/projects/{project_id}/datasets/*

RBAC: users may only access datasets under projects they own.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.core.errors import (
    ERR_AUTH_MISSING,
    ERR_DATASET_NOT_FOUND,
    ERR_PROJECT_FORBIDDEN,
    ERR_PROJECT_NOT_FOUND,
)
from src.infra.db.models.user import User
from tests.api.conftest import DEFAULT_PASSWORD
from tests.factories.dataset import DatasetFactory
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


def _datasets_url(project_id: uuid.UUID) -> str:
    return f"/api/v1/projects/{project_id}/datasets"


def _login_headers(api_client: TestClient, user: User) -> dict[str, str]:
    resp = api_client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": DEFAULT_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestDatasetsList:
    def test_list_datasets_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
        dataset_factory: type[DatasetFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        dataset_factory(project=project, name="iris_tabular")
        dataset_factory(project=project, name="cats_images")

        resp = api_client.get(_datasets_url(project.id), headers=auth_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["total"] >= 2
        names = {item["name"] for item in data["items"]}
        assert "iris_tabular" in names
        assert "cats_images" in names
        for item in data["items"]:
            assert item["project_id"] == str(project.id)

    def test_list_datasets_without_token(
        self,
        api_client: TestClient,
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        resp = api_client.get(_datasets_url(project.id))

        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_MISSING)

    def test_list_datasets_forbidden_other_owner_project(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
        project_factory: type[ProjectFactory],
    ) -> None:
        owner = user_factory(username="ds_owner_list")
        intruder = user_factory(username="ds_intruder_list")
        project = project_factory(owner=owner)
        headers = _login_headers(api_client, intruder)

        resp = api_client.get(_datasets_url(project.id), headers=headers)

        assert resp.status_code == 403
        assert_api_envelope(resp.json(), code=ERR_PROJECT_FORBIDDEN)


class TestDatasetsCreate:
    def test_create_dataset_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        payload = {
            "name": "new_csv_dataset",
            "format": "csv",
            "description": "Created via API",
            "tags": ["test", "tabular"],
        }

        resp = api_client.post(
            _datasets_url(project.id),
            json=payload,
            headers=auth_headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        data = body["data"]
        assert data["name"] == payload["name"]
        assert data["format"] == "csv"
        assert data["project_id"] == str(project.id)
        assert data["status"] == "uploading"
        assert "id" in data
        assert "file_path" in data

    def test_create_dataset_without_token(
        self,
        api_client: TestClient,
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        resp = api_client.post(
            _datasets_url(project.id),
            json={"name": "no_auth", "format": "csv"},
        )

        assert resp.status_code == 401
        assert_api_envelope(resp.json(), code=ERR_AUTH_MISSING)

    def test_create_dataset_forbidden_other_project(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
        project_factory: type[ProjectFactory],
    ) -> None:
        owner = user_factory(username="ds_owner_create")
        intruder = user_factory(username="ds_intruder_create")
        project = project_factory(owner=owner)
        headers = _login_headers(api_client, intruder)

        resp = api_client.post(
            _datasets_url(project.id),
            json={"name": "stolen", "format": "csv"},
            headers=headers,
        )

        assert resp.status_code == 403
        assert_api_envelope(resp.json(), code=ERR_PROJECT_FORBIDDEN)


class TestDatasetsGet:
    def test_get_dataset_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
        dataset_factory: type[DatasetFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        dataset = dataset_factory(project=project, name="detail_ds")

        resp = api_client.get(
            f"{_datasets_url(project.id)}/{dataset.id}",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        assert body["data"]["id"] == str(dataset.id)
        assert body["data"]["name"] == "detail_ds"

    def test_get_dataset_not_found(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        missing_id = uuid.uuid4()

        resp = api_client.get(
            f"{_datasets_url(project.id)}/{missing_id}",
            headers=auth_headers,
        )

        assert resp.status_code == 404
        assert_api_envelope(resp.json(), code=ERR_DATASET_NOT_FOUND)

    def test_get_dataset_wrong_project_returns_not_found(
        self,
        api_client: TestClient,
        auth_user: User,
        project_factory: type[ProjectFactory],
        dataset_factory: type[DatasetFactory],
    ) -> None:
        """Dataset exists but under another project path → 404 (not visible in scope)."""
        project_a = project_factory(owner=auth_user, name="Project A")
        project_b = project_factory(owner=auth_user, name="Project B")
        dataset = dataset_factory(project=project_a)
        headers = _login_headers(api_client, auth_user)

        resp = api_client.get(
            f"{_datasets_url(project_b.id)}/{dataset.id}",
            headers=headers,
        )

        assert resp.status_code == 404
        assert_api_envelope(resp.json(), code=ERR_DATASET_NOT_FOUND)

    def test_get_dataset_forbidden_other_owner_project(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
        project_factory: type[ProjectFactory],
        dataset_factory: type[DatasetFactory],
    ) -> None:
        owner = user_factory(username="ds_owner_get")
        intruder = user_factory(username="ds_intruder_get")
        project = project_factory(owner=owner)
        dataset = dataset_factory(project=project)
        headers = _login_headers(api_client, intruder)

        resp = api_client.get(
            f"{_datasets_url(project.id)}/{dataset.id}",
            headers=headers,
        )

        assert resp.status_code == 403
        assert_api_envelope(resp.json(), code=ERR_PROJECT_FORBIDDEN)


class TestDatasetsUpdate:
    def test_update_dataset_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
        dataset_factory: type[DatasetFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        dataset = dataset_factory(project=project, name="before_update")

        resp = api_client.put(
            f"{_datasets_url(project.id)}/{dataset.id}",
            json={"name": "after_update", "tags": ["updated"]},
            headers=auth_headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert_api_envelope(body, code=0)
        assert body["data"]["name"] == "after_update"
        assert body["data"]["tags"] == ["updated"]

    def test_update_dataset_not_found(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        resp = api_client.put(
            f"{_datasets_url(project.id)}/{uuid.uuid4()}",
            json={"name": "ghost"},
            headers=auth_headers,
        )

        assert resp.status_code == 404
        assert_api_envelope(resp.json(), code=ERR_DATASET_NOT_FOUND)


class TestDatasetsDelete:
    def test_delete_dataset_success(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        auth_user: User,
        project_factory: type[ProjectFactory],
        dataset_factory: type[DatasetFactory],
    ) -> None:
        project = project_factory(owner=auth_user)
        dataset = dataset_factory(project=project, name="to_delete")

        del_resp = api_client.delete(
            f"{_datasets_url(project.id)}/{dataset.id}",
            headers=auth_headers,
        )
        assert del_resp.status_code == 200
        assert_api_envelope(del_resp.json(), code=0)

        get_resp = api_client.get(
            f"{_datasets_url(project.id)}/{dataset.id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404
        assert_api_envelope(get_resp.json(), code=ERR_DATASET_NOT_FOUND)

    def test_delete_dataset_forbidden_other_project(
        self,
        api_client: TestClient,
        user_factory: type[UserFactory],
        project_factory: type[ProjectFactory],
        dataset_factory: type[DatasetFactory],
    ) -> None:
        owner = user_factory(username="ds_owner_del")
        intruder = user_factory(username="ds_intruder_del")
        project = project_factory(owner=owner)
        dataset = dataset_factory(project=project)
        headers = _login_headers(api_client, intruder)

        resp = api_client.delete(
            f"{_datasets_url(project.id)}/{dataset.id}",
            headers=headers,
        )

        assert resp.status_code == 403
        assert_api_envelope(resp.json(), code=ERR_PROJECT_FORBIDDEN)

    def test_delete_dataset_nonexistent_project(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        resp = api_client.delete(
            f"/api/v1/projects/{uuid.uuid4()}/datasets/{uuid.uuid4()}",
            headers=auth_headers,
        )

        assert resp.status_code == 404
        assert_api_envelope(resp.json(), code=ERR_PROJECT_NOT_FOUND)
