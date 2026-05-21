"""
E2E API flow — PRD Scenario 2: business data regression / risk prediction.

Pipeline (single test, no engine mock on training):
  upload CSV → clean (fill_mean) → create MLP → train (epochs=1) → evaluate → agent chat

Requires: Python 3.10+, torch, pandas, synthetic fixture CSV.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.infra.db.models.user import User
from tests.factories.user import UserFactory

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CSV = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_data" / "tabular" / "health_metrics.csv"

AUTH_HEADERS = {"Authorization": "Bearer test-token"}

POLL_TIMEOUT_SEC = 120
POLL_INTERVAL_SEC = 0.5
TERMINAL_FAILURE = frozenset({"failed", "cancelled"})


def assert_api_envelope(body: dict[str, Any], *, code: int = 0, message: str = "success") -> dict[str, Any]:
    assert body["code"] == code, body
    assert body["message"] == message
    assert "data" in body
    assert "request_id" in body
    return body["data"]


def _ok_status(status_code: int) -> bool:
    return status_code in (200, 201)


@pytest.fixture
def auth_user(user_factory: type[UserFactory]) -> User:
    return user_factory()


@pytest.fixture
def e2e_headers(api_client: TestClient, auth_user: User) -> dict[str, str]:
    """Day 2 Bearer test-token + user override for project RBAC."""
    from app.api.deps import get_current_user_id
    from app.main import app

    async def _override_user_id() -> uuid.UUID:
        return auth_user.id

    app.dependency_overrides[get_current_user_id] = _override_user_id
    yield dict(AUTH_HEADERS)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
def training_status_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate subprocess training status files per test run."""
    status_dir = tmp_path / "deepflow_training_status"
    status_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DEEPFLOW_STATUS_DIR", str(status_dir))
    import src.engine.manager as engine_mgr

    monkeypatch.setattr(engine_mgr, "_STATUS_DIR", status_dir)
    return status_dir


def _fetch_and_print_training_logs(
    api_client: TestClient,
    project_id: str,
    job_id: str,
    headers: dict[str, str],
    *,
    reason: str,
) -> None:
    logs_url = f"/api/v1/projects/{project_id}/training-jobs/{job_id}/logs"
    print(f"\n{'=' * 72}\n[E2E] Training logs ({reason}): GET {logs_url}\n{'=' * 72}")
    try:
        logs_resp = api_client.get(logs_url, headers=headers, params={"tail": 500})
        if logs_resp.status_code != 200:
            print(f"[E2E] logs API status={logs_resp.status_code} body={logs_resp.text}")
            return
        logs_body = logs_resp.json()
        log_lines = logs_body.get("data", {}).get("logs", logs_body.get("data", []))
        if isinstance(log_lines, list):
            for line in log_lines:
                print(line)
        else:
            print(json.dumps(logs_body, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"[E2E] Failed to fetch training logs: {exc}")
    print(f"{'=' * 72}\n")


def _poll_training_job(
    api_client: TestClient,
    project_id: str,
    job_id: str,
    job_url: str,
    headers: dict[str, str],
    *,
    timeout: float = POLL_TIMEOUT_SEC,
    interval: float = POLL_INTERVAL_SEC,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_status = "unknown"
    last_payload: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        resp = api_client.get(job_url, headers=headers)
        assert resp.status_code == 200, resp.text
        data = assert_api_envelope(resp.json())
        last_payload = data
        last_status = data.get("status", last_status)
        if last_status == "success":
            return data
        if last_status in TERMINAL_FAILURE:
            _fetch_and_print_training_logs(
                api_client, project_id, job_id, headers, reason=f"status={last_status}"
            )
            err_msg = data.get("error_message") or "(no error_message in job payload)"
            pytest.fail(
                f"Training job ended with status={last_status!r}; error_message={err_msg!r}"
            )
        time.sleep(interval)

    _fetch_and_print_training_logs(
        api_client, project_id, job_id, headers, reason=f"timeout last_status={last_status}"
    )
    err_hint = ""
    if last_payload and last_payload.get("error_message"):
        err_hint = f"; error_message={last_payload['error_message']!r}"
    pytest.fail(
        f"Timeout ({timeout}s) waiting for training success; last status={last_status!r}{err_hint}"
    )


@pytest.mark.e2e
@pytest.mark.integration
class TestScenario2BusinessRegressionE2E:
    """PRD 场景二：业务数据回归预测 — full API chain."""

    def test_full_pipeline(
        self,
        api_client: TestClient,
        e2e_headers: dict[str, str],
        training_status_dir: Path,
    ) -> None:
        if not FIXTURE_CSV.is_file():
            pytest.skip(
                f"Missing fixture CSV: {FIXTURE_CSV}. "
                "Run: python scripts/gen_synthetic_data.py"
            )

        headers = e2e_headers
        _ = training_status_dir  # ensure env + manager patch applied

        # ── 0. Project ─────────────────────────────────────────────
        proj_resp = api_client.post(
            "/api/v1/projects",
            headers=headers,
            json={
                "name": "E2E Scenario2 Risk Prediction",
                "description": "P9 E2E — tabular health risk pipeline",
            },
        )
        assert _ok_status(proj_resp.status_code), proj_resp.text
        project_id = assert_api_envelope(proj_resp.json())["id"]

        # ── 1. Upload / register dataset ───────────────────────────
        with FIXTURE_CSV.open("rb") as csv_file:
            upload_resp = api_client.post(
                f"/api/v1/projects/{project_id}/datasets/upload",
                headers=headers,
                files={"file": ("health_metrics.csv", csv_file, "text/csv")},
                data={"name": "health_metrics", "tags": "e2e,synthetic"},
            )
        assert _ok_status(upload_resp.status_code), upload_resp.text
        dataset_id = assert_api_envelope(upload_resp.json())["id"]

        # ── 2. Cleaning — missing value fill_mean ─────────────────
        clean_resp = api_client.post(
            f"/api/v1/projects/{project_id}/datasets/{dataset_id}/clean/missing",
            headers=headers,
            json={
                "columns": ["age", "bmi", "glucose", "blood_pressure"],
                "strategy": "fill_mean",
                "create_new_version": True,
            },
        )
        assert clean_resp.status_code == 200, clean_resp.text
        clean_data = assert_api_envelope(clean_resp.json())
        cleaned_dataset_id = clean_data["dataset_id"]

        # ── 3. Model — MLP for tabular risk ───────────────────────
        model_resp = api_client.post(
            f"/api/v1/projects/{project_id}/models",
            headers=headers,
            json={
                "name": "e2e_risk_mlp",
                "arch_type": "mlp",
                "params_cfg": {"hidden_dims": [64, 32], "num_classes": 2},
                "description": "E2E MLP for health_metrics risk_label",
            },
        )
        assert model_resp.status_code == 200, model_resp.text
        model_id = assert_api_envelope(model_resp.json())["id"]

        # ── 4. Training job + real start (no mock) ────────────────
        job_resp = api_client.post(
            f"/api/v1/projects/{project_id}/training-jobs",
            headers=headers,
            json={
                "name": "e2e_risk_train",
                "model_id": model_id,
                "dataset_id": cleaned_dataset_id,
                "hyperparams": {
                    "epochs": 1,
                    "batch_size": 4,
                    "learning_rate": 0.01,
                    "optimizer": "adam",
                    "loss_function": "cross_entropy",
                },
                "device": "cpu",
                "description": "E2E one-epoch smoke training",
            },
        )
        assert job_resp.status_code == 200, job_resp.text
        job_data = assert_api_envelope(job_resp.json())
        job_id = job_data["id"]
        assert job_data["status"] == "pending"

        start_resp = api_client.post(
            f"/api/v1/projects/{project_id}/training-jobs/{job_id}/start",
            headers=headers,
        )
        assert start_resp.status_code == 200, start_resp.text
        start_data = assert_api_envelope(start_resp.json())
        assert start_data["status"] == "running"

        job_url = f"/api/v1/projects/{project_id}/training-jobs/{job_id}"
        final_job = _poll_training_job(
            api_client, project_id, job_id, job_url, headers
        )
        assert final_job["status"] == "success"

        # ── 5. Inference / evaluation ─────────────────────────────
        eval_resp = api_client.post(
            f"/api/v1/projects/{project_id}/inference/evaluate",
            headers=headers,
            json={
                "model_id": model_id,
                "dataset_id": cleaned_dataset_id,
                "metrics": ["accuracy", "f1"],
            },
        )
        assert eval_resp.status_code == 200, eval_resp.text
        eval_data = assert_api_envelope(eval_resp.json())
        assert eval_data.get("status") == "completed"
        task_id = eval_data["task_id"]

        result_resp = api_client.get(
            f"/api/v1/projects/{project_id}/inference/{task_id}",
            headers=headers,
        )
        assert result_resp.status_code == 200, result_resp.text
        result_data = assert_api_envelope(result_resp.json())
        assert result_data["status"] == "completed"
        assert "metrics" in result_data

        # ── 6. Agent — create, bind model tool, chat ──────────────
        agent_resp = api_client.post(
            f"/api/v1/projects/{project_id}/agents",
            headers=headers,
            json={
                "name": "E2E Risk Agent",
                "description": "Scenario 2 closure agent",
                "system_prompt": "你是健康风险预测助手，可调用模型工具分析数据。",
                "model_config": {"provider": "mock", "model": "gpt-4"},
            },
        )
        assert _ok_status(agent_resp.status_code), agent_resp.text
        agent_id = assert_api_envelope(agent_resp.json())["id"]

        bind_resp = api_client.post(
            f"/api/v1/projects/{project_id}/agents/{agent_id}/tools/bind",
            headers=headers,
            json={
                "tools": [
                    {
                        "name": "predict_health_risk",
                        "type": "model_inference",
                        "model_id": model_id,
                        "description": "Predict risk_label from health metrics",
                    }
                ]
            },
        )
        assert bind_resp.status_code == 200, bind_resp.text
        assert_api_envelope(bind_resp.json())

        chat_resp = api_client.post(
            f"/api/v1/projects/{project_id}/agents/{agent_id}/chat",
            headers=headers,
            json={
                "message": "请根据已训练模型，评估一位 45 岁、BMI 28、血糖 140 的患者的健康风险。",
            },
        )
        assert chat_resp.status_code == 200, chat_resp.text
        # SSE stream — consume at least one event chunk
        body_text = chat_resp.text or ""
        assert body_text.strip(), "Expected non-empty SSE response body"
        if body_text.lstrip().startswith("{"):
            # Some clients aggregate JSON lines
            assert "token" in body_text.lower() or "done" in body_text.lower() or "tool" in body_text.lower()
