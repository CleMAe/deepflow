"""Tests for Experiment APIs."""

import pytest


class TestExperiments:
    _counter = 200

    @staticmethod
    def _next_pid():
        TestExperiments._counter += 1
        return f"c0000000-0000-0000-0000-{TestExperiments._counter:012d}"

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self._pid = self._next_pid()
        client.post(
            f"/api/v1/projects/{self._pid}/training-jobs",
            json={
                "name": "Experiment Source Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
                "hyperparams": {
                    "epochs": 5,
                    "batch_size": 64,
                    "learning_rate": 0.01,
                },
            },
        )

    def test_list_experiments(self, client):
        res = client.get(f"/api/v1/projects/{self._pid}/experiments")
        assert res.status_code == 200
        data = res.json()["data"]
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 1

    def test_get_experiment_detail(self, client):
        res = client.get(f"/api/v1/projects/{self._pid}/experiments")
        exp_id = res.json()["data"]["items"][0]["id"]

        res = client.get(f"/api/v1/projects/{self._pid}/experiments/{exp_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["id"] == exp_id
        assert data["name"] == "Experiment Source Job"

    def test_get_experiment_not_found(self, client):
        fake_id = "11111111-1111-1111-1111-111111111111"
        res = client.get(f"/api/v1/projects/{self._pid}/experiments/{fake_id}")
        assert res.status_code == 200
        assert res.json()["code"] != 0

    def test_update_experiment(self, client):
        res = client.get(f"/api/v1/projects/{self._pid}/experiments")
        exp_id = res.json()["data"]["items"][0]["id"]

        res = client.put(
            f"/api/v1/projects/{self._pid}/experiments/{exp_id}",
            json={"tags": ["best", "production"], "notes": "Best performing model so far"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "best" in data["tags"]
        assert "production" in data["tags"]
        assert data["notes"] == "Best performing model so far"

    def test_compare_experiments(self, client):
        client.post(
            f"/api/v1/projects/{self._pid}/training-jobs",
            json={
                "name": "Experiment 2",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
                "hyperparams": {"epochs": 20, "batch_size": 16},
            },
        )

        res = client.get(f"/api/v1/projects/{self._pid}/experiments")
        exp_ids = [item["id"] for item in res.json()["data"]["items"]]

        res = client.post(
            f"/api/v1/projects/{self._pid}/experiments/compare",
            json={"experiment_ids": exp_ids},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "experiments" in data
        assert "metric_comparison" in data
        assert "param_diff" in data
        assert len(data["experiments"]) >= 2
