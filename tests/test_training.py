"""Tests for Training Job APIs."""


class TestTrainingJobs:
    _counter = 100

    @staticmethod
    def _next_pid():
        TestTrainingJobs._counter += 1
        return f"b0000000-0000-0000-0000-{TestTrainingJobs._counter:012d}"

    def test_list_empty_training_jobs(self, client):
        pid = self._next_pid()
        res = client.get(f"/api/v1/projects/{pid}/training-jobs")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_create_training_job(self, client):
        pid = self._next_pid()
        res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "My Training Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
                "hyperparams": {
                    "epochs": 10,
                    "batch_size": 32,
                    "learning_rate": 0.001,
                    "optimizer": "adam",
                    "loss_function": "cross_entropy",
                },
                "device": "auto",
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["name"] == "My Training Job"
        assert data["status"] == "pending"
        assert data["total_epochs"] == 10
        assert "id" in data

    def test_create_training_job_minimal(self, client):
        pid = self._next_pid()
        res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Minimal Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["name"] == "Minimal Job"
        assert data["status"] == "pending"

    def test_get_training_job_detail(self, client):
        pid = self._next_pid()
        create_res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Detail Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        job_id = create_res.json()["data"]["id"]

        res = client.get(f"/api/v1/projects/{pid}/training-jobs/{job_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["id"] == job_id
        assert data["name"] == "Detail Job"

    def test_get_training_job_not_found(self, client):
        pid = self._next_pid()
        fake_id = "11111111-1111-1111-1111-111111111111"
        res = client.get(f"/api/v1/projects/{pid}/training-jobs/{fake_id}")
        assert res.status_code == 200
        assert res.json()["code"] != 0

    def test_start_training(self, client):
        pid = self._next_pid()
        create_res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Start Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        job_id = create_res.json()["data"]["id"]

        res = client.post(
            f"/api/v1/projects/{pid}/training-jobs/{job_id}/start"
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "running"

    def test_pause_training(self, client):
        pid = self._next_pid()
        create_res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Pause Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        job_id = create_res.json()["data"]["id"]

        client.post(f"/api/v1/projects/{pid}/training-jobs/{job_id}/start")
        res = client.post(
            f"/api/v1/projects/{pid}/training-jobs/{job_id}/pause"
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "paused"

    def test_resume_training(self, client):
        pid = self._next_pid()
        create_res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Resume Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        job_id = create_res.json()["data"]["id"]

        client.post(f"/api/v1/projects/{pid}/training-jobs/{job_id}/start")
        client.post(
            f"/api/v1/projects/{pid}/training-jobs/{job_id}/pause"
        )
        res = client.post(
            f"/api/v1/projects/{pid}/training-jobs/{job_id}/resume"
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "running"

    def test_stop_training(self, client):
        pid = self._next_pid()
        create_res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Stop Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        job_id = create_res.json()["data"]["id"]

        client.post(f"/api/v1/projects/{pid}/training-jobs/{job_id}/start")
        res = client.post(
            f"/api/v1/projects/{pid}/training-jobs/{job_id}/stop"
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "cancelled"

    def test_get_training_logs(self, client):
        pid = self._next_pid()
        create_res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Log Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        job_id = create_res.json()["data"]["id"]

        res = client.get(
            f"/api/v1/projects/{pid}/training-jobs/{job_id}/logs",
            params={"tail": 10},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "logs" in data
        assert isinstance(data["logs"], list)
        assert len(data["logs"]) > 0

    def test_get_checkpoints(self, client):
        pid = self._next_pid()
        create_res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Checkpoint Job",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        job_id = create_res.json()["data"]["id"]

        res = client.get(
            f"/api/v1/projects/{pid}/training-jobs/{job_id}/checkpoints"
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "checkpoints" in data
        assert isinstance(data["checkpoints"], list)

    def test_filter_jobs_by_status(self, client):
        pid = self._next_pid()
        create_res = client.post(
            f"/api/v1/projects/{pid}/training-jobs",
            json={
                "name": "Status Test",
                "model_id": "00000000-0000-0000-0000-000000000001",
                "dataset_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        job_id = create_res.json()["data"]["id"]
        client.post(f"/api/v1/projects/{pid}/training-jobs/{job_id}/start")

        res = client.get(
            f"/api/v1/projects/{pid}/training-jobs",
            params={"status": "running"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        for item in data["items"]:
            assert item["status"] == "running"
