"""Inference API integration tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.infra.db.models.ml_model import MLModel
from src.infra.db.models.user import User
from tests.factories.project import ProjectFactory
from tests.factories.user import UserFactory


@pytest.fixture
def inference_project(project_factory: type[ProjectFactory], auth_user: User):
    return project_factory(owner=auth_user, name="Inference Test Project")


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
