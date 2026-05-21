"""Inference API integration tests."""

from __future__ import annotations

import uuid

import pytest
import torch
import torch.nn as nn
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.infra.db.models.ml_model import MLModel
from src.infra.db.models.user import User
from tests.factories.project import ProjectFactory
from tests.factories.user import UserFactory


@pytest.fixture
def inference_project(project_factory: type[ProjectFactory], auth_user: User):
    return project_factory(owner=auth_user, name="Inference Test Project")


def _create_mlp_checkpoint(tmp_path, n_classes=3, input_dim=20):
    """Create a minimal valid MLP checkpoint file for testing."""
    model = nn.Sequential(
        nn.Linear(input_dim, 128),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(128, 64),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(64, n_classes),
    )
    ckpt_path = str(tmp_path / "checkpoint_best.pth")
    torch.save({
        "epoch": 1,
        "model_state_dict": model.state_dict(),
        "arch_type": "mlp",
        "n_classes": n_classes,
        "input_dim": input_dim,
    }, ckpt_path)
    return ckpt_path


class TestInferenceOnline:
    def test_online_inference_model_not_found(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        inference_project,
    ):
        pid = str(inference_project.id)
        fake_model = str(uuid.uuid4())
        resp = api_client.post(
            f"/api/v1/projects/{pid}/inference/online",
            json={"model_id": fake_model, "input_data": {"f1": 1.0}},
            headers=auth_headers,
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] // 1_000_000 == 60

    def test_online_inference_no_checkpoint(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        inference_project,
        db_session: Session,
    ):
        pid = str(inference_project.id)
        model_id = uuid.uuid4()
        model = MLModel(
            id=model_id,
            project_id=inference_project.id,
            name="No-checkpoint model",
            arch_type="mlp",
        )
        db_session.add(model)
        db_session.flush()

        resp = api_client.post(
            f"/api/v1/projects/{pid}/inference/online",
            json={"model_id": str(model_id), "input_data": {"f1": 1.0}},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_online_inference_happy_path(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        inference_project,
        db_session: Session,
        tmp_path,
    ):
        """Online inference with a real MLP checkpoint should return prediction + confidence."""
        ckpt_path = _create_mlp_checkpoint(tmp_path)

        model_id = uuid.uuid4()
        model = MLModel(
            id=model_id,
            project_id=inference_project.id,
            name="Test MLP",
            arch_type="mlp",
            model_path=str(tmp_path),
        )
        db_session.add(model)
        db_session.flush()

        pid = str(inference_project.id)
        resp = api_client.post(
            f"/api/v1/projects/{pid}/inference/online",
            json={
                "model_id": str(model_id),
                "input_data": {f"f{i}": float(i) for i in range(20)},
                "checkpoint_path": ckpt_path,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "prediction" in data
        assert "confidence" in data
        assert "probabilities" in data
        assert "latency_ms" in data
        assert isinstance(data["prediction"], int)
        assert 0 <= data["confidence"] <= 1
        assert len(data["probabilities"]) == 3
        assert data["latency_ms"] > 0


class TestInferenceBatch:
    def test_batch_model_not_found(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        inference_project,
    ):
        pid = str(inference_project.id)
        fake_model = str(uuid.uuid4())
        fake_ds = str(uuid.uuid4())
        resp = api_client.post(
            f"/api/v1/projects/{pid}/inference/batch",
            json={"model_id": fake_model, "dataset_id": fake_ds},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_batch_invalid_output_format(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        inference_project,
    ):
        pid = str(inference_project.id)
        fake_model = str(uuid.uuid4())
        fake_ds = str(uuid.uuid4())
        resp = api_client.post(
            f"/api/v1/projects/{pid}/inference/batch",
            json={"model_id": fake_model, "dataset_id": fake_ds, "output_format": "xml"},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestInferenceEvaluate:
    def test_evaluate_model_not_found(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        inference_project,
    ):
        pid = str(inference_project.id)
        fake_model = str(uuid.uuid4())
        fake_ds = str(uuid.uuid4())
        resp = api_client.post(
            f"/api/v1/projects/{pid}/inference/evaluate",
            json={"model_id": fake_model, "dataset_id": fake_ds},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestInferenceTaskGet:
    def test_get_nonexistent_task(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        inference_project,
    ):
        pid = str(inference_project.id)
        fake_task = str(uuid.uuid4())
        resp = api_client.get(
            f"/api/v1/projects/{pid}/inference/{fake_task}",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestInferenceExportOnnx:
    def test_export_onnx_model_not_found(
        self,
        api_client: TestClient,
        auth_headers: dict[str, str],
        inference_project,
    ):
        pid = str(inference_project.id)
        fake_model = str(uuid.uuid4())
        resp = api_client.post(
            f"/api/v1/projects/{pid}/inference/export-onnx",
            json={"model_id": fake_model},
            headers=auth_headers,
        )
        assert resp.status_code == 404
