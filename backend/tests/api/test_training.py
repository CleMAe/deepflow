"""
Training & model library API integration tests — P8 module.

Endpoints:
  GET  /api/v1/models/library
  POST /api/v1/projects/{id}/models
  POST /api/v1/projects/{id}/training-jobs
  POST /api/v1/projects/{id}/training-jobs/{job_id}/start

Asserts HTTP 200 and envelope {code: 0, message: "success", data, request_id}.
PyTorch/subprocess training is mocked — no real training loop.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.infra.db.models.dataset import Dataset
from src.infra.db.models.project import Project
from src.infra.db.models.user import User
from tests.factories.dataset import DatasetFactory
from tests.factories.project import ProjectFactory

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def assert_api_envelope(body: dict[str, Any], *, code: int = 0, message: str = "success") -> None:
    assert body["code"] == code
    assert body["message"] == message
    assert "data" in body
    assert "request_id" in body
    assert isinstance(body["request_id"], str)


def _models_url(project_id: uuid.UUID) -> str:
    return f"/api/v1/projects/{project_id}/models"


def _training_jobs_url(project_id: uuid.UUID, job_id: uuid.UUID | None = None, action: str | None = None) -> str:
    base = f"/api/v1/projects/{project_id}/training-jobs"
    if job_id is None:
        return base
    path = f"{base}/{job_id}"
    return f"{path}/{action}" if action else path


@pytest.fixture
def test_token_headers(api_client: TestClient, auth_user: User) -> dict[str, str]:
    """Bearer test-token with get_current_user_id overridden to auth_user."""
    from app.api.deps import get_current_user_id
    from app.main import app

    async def _override_user_id() -> uuid.UUID:
        return auth_user.id

    app.dependency_overrides[get_current_user_id] = _override_user_id
    yield dict(AUTH_HEADERS)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
def training_project_and_dataset(
    auth_user: User,
    project_factory: type[ProjectFactory],
    dataset_factory: type[DatasetFactory],
) -> tuple[Project, Dataset]:
    project = project_factory(owner=auth_user, name="P8 Training Project")
    dataset = dataset_factory(
        project=project,
        name="train_dataset",
        num_samples=100,
    )
    return project, dataset


class TestModelLibrary:
    def test_list_model_library(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/models/library")

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert_api_envelope(body)
        items = body["data"]
        assert isinstance(items, list)
        assert len(items) >= 1
        model_ids = {m["model_id"] for m in items}
        assert "resnet18" in model_ids or "mlp" in model_ids
        first = items[0]
        assert "arch_type" in first
        assert "task_type" in first


class TestProjectModel:
    def test_create_project_model_resnet(
        self,
        api_client: TestClient,
        test_token_headers: dict[str, str],
        training_project_and_dataset: tuple[Project, Dataset],
    ) -> None:
        project, _ = training_project_and_dataset
        resp = api_client.post(
            _models_url(project.id),
            headers=test_token_headers,
            json={
                "name": "integration_resnet18",
                "arch_type": "resnet18",
                "params_cfg": {"num_classes": 10, "pretrained": False},
                "description": "P8 integration test model",
            },
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert_api_envelope(body)
        data = body["data"]
        assert data["arch_type"] == "resnet18"
        assert data["project_id"] == str(project.id)
        assert data["name"] == "integration_resnet18"


class TestTrainingJobs:
    @pytest.fixture
    def model_id(
        self,
        api_client: TestClient,
        test_token_headers: dict[str, str],
        training_project_and_dataset: tuple[Project, Dataset],
    ) -> tuple[Project, Dataset, str]:
        project, dataset = training_project_and_dataset
        resp = api_client.post(
            _models_url(project.id),
            headers=test_token_headers,
            json={
                "name": "job_mlp_model",
                "arch_type": "mlp",
                "params_cfg": {"hidden_dims": [128, 64], "num_classes": 5},
                "description": "MLP for training job tests",
            },
        )
        assert resp.status_code == 200, resp.text
        return project, dataset, resp.json()["data"]["id"]

    def test_create_training_job(
        self,
        api_client: TestClient,
        test_token_headers: dict[str, str],
        model_id: tuple[Project, Dataset, str],
    ) -> None:
        project, dataset, mid = model_id
        resp = api_client.post(
            _training_jobs_url(project.id),
            headers=test_token_headers,
            json={
                "name": "smoke_training_job",
                "model_id": mid,
                "dataset_id": str(dataset.id),
                "hyperparams": {
                    "epochs": 2,
                    "batch_size": 8,
                    "learning_rate": 0.001,
                    "optimizer": "adam",
                },
                "device": "cpu",
                "description": "CI fast integration test",
            },
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert_api_envelope(body)
        data = body["data"]
        assert data["status"] == "pending"
        assert data["model_id"] == mid
        assert data["dataset_id"] == str(dataset.id)
        assert data["project_id"] == str(project.id)

    def test_start_training_job(
        self,
        api_client: TestClient,
        test_token_headers: dict[str, str],
        model_id: tuple[Project, Dataset, str],
    ) -> None:
        project, dataset, mid = model_id

        create_resp = api_client.post(
            _training_jobs_url(project.id),
            headers=test_token_headers,
            json={
                "name": "start_smoke_job",
                "model_id": mid,
                "dataset_id": str(dataset.id),
                "hyperparams": {"epochs": 1, "batch_size": 4},
                "device": "cpu",
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        job_id = create_resp.json()["data"]["id"]
        assert create_resp.json()["data"]["status"] == "pending"

        with patch("app.services.training_service._engine.start_training") as mock_start:
            mock_start.return_value = None
            start_resp = api_client.post(
                _training_jobs_url(project.id, uuid.UUID(job_id), "start"),
                headers=test_token_headers,
            )

        assert start_resp.status_code == 200, start_resp.text
        body = start_resp.json()
        assert_api_envelope(body)
        data = body["data"]
        assert data["status"] == "running"
        assert data["id"] == job_id
        mock_start.assert_called_once()
