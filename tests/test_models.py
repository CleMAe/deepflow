"""Tests for Model Library and Model Config APIs."""

import pytest


class TestModelLibrary:
    def test_list_all_models(self, client):
        res = client.get("/api/v1/models/library")
        assert res.status_code == 200
        data = res.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 6

    def test_list_filter_by_task_type(self, client):
        res = client.get("/api/v1/models/library?task_type=classification")
        assert res.status_code == 200
        data = res.json()["data"]
        assert all(m["task_type"] == "classification" for m in data)

    def test_list_filter_by_search(self, client):
        res = client.get("/api/v1/models/library?search=resnet")
        assert res.status_code == 200
        data = res.json()["data"]
        assert all("resnet" in m["name"].lower() for m in data)

    def test_get_library_model_detail(self, client):
        res = client.get("/api/v1/models/library/resnet18")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["model_id"] == "resnet18"
        assert data["arch_type"] == "resnet18"
        assert data["pretrained_available"] is True

    def test_get_library_model_not_found(self, client):
        res = client.get("/api/v1/models/library/nonexistent")
        assert res.status_code == 200
        body = res.json()
        assert body["code"] != 0

    def test_list_regression_models(self, client):
        res = client.get("/api/v1/models/library?task_type=regression")
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) >= 1
        assert all(m["task_type"] == "regression" for m in data)


class TestProjectModels:
    _counter = 0

    @classmethod
    def _project_id(cls):
        cls._counter += 1
        return f"a0000000-0000-0000-0000-{cls._counter:012d}"

    def test_list_empty_project_models(self, client):
        pid = self._project_id()
        res = client.get(f"/api/v1/projects/{pid}/models")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_create_model(self, client):
        pid = self._project_id()
        res = client.post(
            f"/api/v1/projects/{pid}/models",
            json={
                "name": "My CNN Model",
                "arch_type": "resnet18",
                "params_cfg": {"num_classes": 10},
                "description": "A test model",
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["name"] == "My CNN Model"
        assert data["arch_type"] == "resnet18"
        assert "id" in data

    def test_list_project_models_after_create(self, client):
        pid = self._project_id()
        client.post(
            f"/api/v1/projects/{pid}/models",
            json={"name": "Test Model", "arch_type": "mlp"},
        )
        res = client.get(f"/api/v1/projects/{pid}/models")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] >= 1

    def test_get_model_detail(self, client):
        pid = self._project_id()
        create_res = client.post(
            f"/api/v1/projects/{pid}/models",
            json={"name": "Detail Model", "arch_type": "resnet34"},
        )
        model_id = create_res.json()["data"]["id"]

        res = client.get(f"/api/v1/projects/{pid}/models/{model_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["id"] == model_id
        assert data["name"] == "Detail Model"

    def test_get_model_not_found(self, client):
        pid = self._project_id()
        fake_id = "11111111-1111-1111-1111-111111111111"
        res = client.get(f"/api/v1/projects/{pid}/models/{fake_id}")
        assert res.status_code == 200
        assert res.json()["code"] != 0

    def test_update_model(self, client):
        pid = self._project_id()
        create_res = client.post(
            f"/api/v1/projects/{pid}/models",
            json={"name": "Update Me", "arch_type": "mlp"},
        )
        model_id = create_res.json()["data"]["id"]

        res = client.put(
            f"/api/v1/projects/{pid}/models/{model_id}",
            json={"name": "Updated Model", "description": "Updated description"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["name"] == "Updated Model"
        assert data["description"] == "Updated description"

    def test_validate_model_config(self, client):
        pid = self._project_id()
        create_res = client.post(
            f"/api/v1/projects/{pid}/models",
            json={"name": "Validate Model", "arch_type": "resnet18"},
        )
        model_id = create_res.json()["data"]["id"]

        res = client.post(
            f"/api/v1/projects/{pid}/models/{model_id}/validate",
            json={"params_cfg": {"num_classes": 10, "batch_norm": True}},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "valid" in data
        assert "errors" in data
        assert "warnings" in data

    def test_load_pretrained_weights(self, client):
        pid = self._project_id()
        create_res = client.post(
            f"/api/v1/projects/{pid}/models",
            json={"name": "Pretrained Model", "arch_type": "efficientnet_b0"},
        )
        model_id = create_res.json()["data"]["id"]

        res = client.post(
            f"/api/v1/projects/{pid}/models/{model_id}/pretrained",
            json={
                "source": "huggingface",
                "repo_id": "microsoft/resnet-18",
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "ready"
        assert "model_path" in data
