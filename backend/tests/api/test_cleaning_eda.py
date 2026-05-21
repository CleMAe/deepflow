"""
Cleaning & EDA API integration tests — P7 data module.

Endpoints:
  POST /api/v1/projects/{id}/datasets/{ds_id}/clean/missing
  POST /api/v1/projects/{id}/datasets/{ds_id}/clean/dedup
  POST /api/v1/projects/{id}/datasets/{ds_id}/eda

Asserts HTTP 200 and unified envelope {code: 0, message: "success", data, request_id}.
Does not validate deep pandas/engine correctness.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infra.db.models.dataset import Dataset, DatasetFormat, DatasetStatus
from src.infra.db.models.project import Project
from src.infra.db.models.user import User
from tests.factories.dataset import DatasetFactory
from tests.factories.project import ProjectFactory

# Day 2 convention — paired with get_current_user_id override below
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def assert_api_envelope(body: dict[str, Any], *, code: int = 0, message: str = "success") -> None:
    assert body["code"] == code
    assert body["message"] == message
    assert "data" in body
    assert "request_id" in body
    assert isinstance(body["request_id"], str)


def _clean_url(project_id: uuid.UUID, ds_id: uuid.UUID, operation: str) -> str:
    return f"/api/v1/projects/{project_id}/datasets/{ds_id}/clean/{operation}"


def _eda_url(project_id: uuid.UUID, ds_id: uuid.UUID) -> str:
    return f"/api/v1/projects/{project_id}/datasets/{ds_id}/eda"


@pytest.fixture
def test_token_headers(api_client: TestClient, auth_user: User) -> dict[str, str]:
    """
    Day 2 placeholder Bearer token; override resolves user to auth_user for RBAC.
    """
    from app.api.deps import get_current_user_id
    from app.main import app

    async def _override_user_id() -> uuid.UUID:
        return auth_user.id

    app.dependency_overrides[get_current_user_id] = _override_user_id
    yield dict(AUTH_HEADERS)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
def tabular_project_and_dataset(
    auth_user: User,
    project_factory: type[ProjectFactory],
    dataset_factory: type[DatasetFactory],
) -> tuple[Project, Dataset]:
    """Project + CSV dataset with a real file under STORAGE_ROOT."""
    project = project_factory(owner=auth_user, name="P7 Cleaning EDA Project")
    storage_root = Path(os.environ["STORAGE_ROOT"])
    csv_path = storage_root / "projects" / str(project.id) / "datasets" / "raw" / "cleaning_eda.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(
        "age,bmi,glucose,risk_label\n"
        "30,22.5,100,0\n"
        ",25.0,110,0\n"
        "40,28.0,120,1\n"
        "40,28.0,120,1\n",
        encoding="utf-8",
    )
    dataset = dataset_factory(
        project=project,
        name="cleaning_eda_tabular",
        format=DatasetFormat.CSV,
        status=DatasetStatus.READY,
        file_path=str(csv_path),
        num_samples=4,
        num_columns=4,
        columns_meta=[
            {"name": "age", "dtype": "float64", "nullable": True},
            {"name": "bmi", "dtype": "float64", "nullable": True},
            {"name": "glucose", "dtype": "float64", "nullable": True},
            {"name": "risk_label", "dtype": "int64", "nullable": False},
        ],
    )
    return project, dataset


class TestCleaningMissing:
    def test_clean_missing_fill_mean(
        self,
        api_client: TestClient,
        test_token_headers: dict[str, str],
        tabular_project_and_dataset: tuple[Project, Dataset],
    ) -> None:
        project, dataset = tabular_project_and_dataset
        resp = api_client.post(
            _clean_url(project.id, dataset.id, "missing"),
            headers=test_token_headers,
            json={
                "columns": ["age", "bmi", "glucose"],
                "strategy": "fill_mean",
                "create_new_version": True,
            },
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert_api_envelope(body)
        assert body["data"] is not None
        assert "dataset_id" in body["data"]
        assert "rows_before" in body["data"]
        assert "rows_after" in body["data"]


class TestCleaningDedup:
    def test_clean_dedup(
        self,
        api_client: TestClient,
        test_token_headers: dict[str, str],
        tabular_project_and_dataset: tuple[Project, Dataset],
    ) -> None:
        project, dataset = tabular_project_and_dataset
        resp = api_client.post(
            _clean_url(project.id, dataset.id, "dedup"),
            headers=test_token_headers,
            json={"columns": [], "keep": "first"},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert_api_envelope(body)
        assert body["data"] is not None
        assert body["data"]["rows_before"] >= body["data"]["rows_after"]


class TestEda:
    def test_trigger_eda(
        self,
        api_client: TestClient,
        test_token_headers: dict[str, str],
        tabular_project_and_dataset: tuple[Project, Dataset],
    ) -> None:
        project, dataset = tabular_project_and_dataset
        resp = api_client.post(
            _eda_url(project.id, dataset.id),
            headers=test_token_headers,
            json={"columns": [], "include_visualizations": False},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert_api_envelope(body)
        data = body["data"]
        assert data["dataset_id"] == str(dataset.id)
        assert data["status"] == "completed"
