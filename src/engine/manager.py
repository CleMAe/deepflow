"""
Training engine manager — API layer uses this to spawn and control
training subprocesses. Matches TrainingEngineProtocol from shared.protocols.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from shared.protocols import TrainingStatus

_STATUS_DIR = Path(os.environ.get("DEEPFLOW_STATUS_DIR", "/tmp/deepflow_training"))


def _status_path(job_id: str) -> Path:
    return _STATUS_DIR / f"{job_id}.json"


def _read_status(job_id: str) -> dict | None:
    p = _status_path(job_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


class TrainingEngineManager:
    """Manages training subprocesses. Implements TrainingEngineProtocol."""

    _processes: dict[str, subprocess.Popen]

    def __init__(self) -> None:
        self._processes: dict[str, subprocess.Popen] = {}
        _STATUS_DIR.mkdir(parents=True, exist_ok=True)

    def start_training(
        self,
        job_id: str,
        model_arch: str,
        dataset_path: str,
        output_dir: str,
        val_dataset_path: str | None = None,
        hyperparams: dict | None = None,
        device: str = "auto",
    ) -> None:
        status_file = str(_status_path(job_id))

        cmd = [
            sys.executable, "-m", "src.engine.train_worker",
            "--job-id", job_id,
            "--model-arch", model_arch,
            "--dataset-path", dataset_path,
            "--output-dir", output_dir,
            "--device", device,
            "--status-file", status_file,
        ]
        if val_dataset_path:
            cmd += ["--val-dataset-path", val_dataset_path]
        if hyperparams:
            cmd += ["--hyperparams", json.dumps(hyperparams)]

        log_stdout = _STATUS_DIR / f"{job_id}.log"
        log_file = open(log_stdout, "a")

        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self._processes[job_id] = proc

    def pause_training(self, job_id: str) -> None:
        proc = self._processes.get(job_id)
        if proc and proc.poll() is None:
            proc.send_signal(signal.SIGSTOP if _has_sigstop() else signal.SIGTERM)

    def resume_training(self, job_id: str) -> None:
        proc = self._processes.get(job_id)
        if proc and proc.poll() is None:
            proc.send_signal(signal.SIGCONT if _has_sigcont() else signal.SIGTERM)

    def stop_training(self, job_id: str) -> None:
        proc = self._processes.get(job_id)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

        # Write cancelled status
        sf = _status_path(job_id)
        if sf.exists():
            try:
                data = json.loads(sf.read_text())
                data["status"] = "cancelled"
                data["updated_at"] = datetime.now(timezone.utc).isoformat()
                sf.write_text(json.dumps(data))
            except (json.JSONDecodeError, OSError):
                pass

    def get_status(self, job_id: str) -> TrainingStatus:
        data = _read_status(job_id)
        if data is None:
            proc = self._processes.get(job_id)
            if proc is None:
                return TrainingStatus.PENDING
            if proc.poll() is not None:
                return TrainingStatus.FAILED
            return TrainingStatus.PENDING

        status_str = data.get("status", "pending")
        try:
            return TrainingStatus(status_str)
        except ValueError:
            return TrainingStatus.FAILED

    def get_progress(self, job_id: str) -> dict | None:
        return _read_status(job_id)

    def get_checkpoints(self, job_id: str, output_dir: str) -> list[dict]:
        checkpoints = []
        d = Path(output_dir)
        if not d.exists():
            return checkpoints
        for p in sorted(d.glob("checkpoint_*.pth")):
            stat = p.stat()
            name = p.stem.replace("checkpoint_", "")
            checkpoints.append({
                "epoch": 0,
                "step": 0,
                "path": str(p),
                "is_best": name == "best",
                "metrics": {},
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
        # Try to read epoch/metrics from the checkpoint files
        try:
            import torch as _torch
            for ckpt in checkpoints:
                data = _torch.load(ckpt["path"], map_location="cpu", weights_only=False)
                ckpt["epoch"] = data.get("epoch", 0)
                ckpt["step"] = data.get("epoch", 0)
                ckpt["metrics"] = {
                    k: v for k, v in data.items()
                    if k in ("train_loss", "val_loss", "accuracy") and isinstance(v, (int, float))
                }
        except Exception:
            pass
        return checkpoints

    def get_logs(self, job_id: str, tail: int = 200) -> list[str]:
        log_path = _STATUS_DIR / f"{job_id}.log"
        if not log_path.exists():
            data = _read_status(job_id)
            if data:
                return [json.dumps(data, ensure_ascii=False)]
            return []
        lines = log_path.read_text().strip().splitlines()
        return lines[-tail:]

    def is_process_alive(self, job_id: str) -> bool:
        proc = self._processes.get(job_id)
        return proc is not None and proc.poll() is None


# Signal availability check (Windows lacks SIGSTOP/SIGCONT)
def _has_sigstop() -> bool:
    return hasattr(signal, "SIGSTOP")

def _has_sigcont() -> bool:
    return hasattr(signal, "SIGCONT")


import signal
