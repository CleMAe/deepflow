"""
Inference engine — loads trained PyTorch models from checkpoints
and runs online/batch/evaluation inference plus ONNX export.

Reuses the model factory from train_worker.py to ensure architecture
parity between training and inference.
"""

from __future__ import annotations

import base64
import io
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from src.engine.train_worker import _build_model, _CV_ARCHS, _is_cv_arch

# In-memory task store for async inference tasks
_tasks: dict[str, dict[str, Any]] = {}


class InferenceEngine:
    """Core inference engine. Loads checkpoints, runs inference."""

    def _load_model(
        self,
        checkpoint_path: str,
        device: str = "auto",
    ) -> tuple[nn.Module, dict, torch.device]:
        """Load a model from a checkpoint file.

        Returns (model, checkpoint_metadata, device).
        """
        if not Path(checkpoint_path).exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        device_str = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        dev = torch.device(device_str)

        ckpt = torch.load(checkpoint_path, map_location=dev, weights_only=False)
        arch_type = ckpt.get("arch_type", "mlp")
        n_classes = ckpt.get("n_classes", 3)
        input_dim = ckpt.get("input_dim", 20)

        model = _build_model(arch_type, n_classes=n_classes, input_dim=input_dim)
        model.load_state_dict(ckpt["model_state_dict"])
        model.to(dev)
        model.eval()
        return model, ckpt, dev

    def _find_checkpoint(
        self,
        checkpoint_path: str | None,
        model_path: str | None,
    ) -> str | None:
        """Resolve the checkpoint path to use.

        Priority: explicit checkpoint_path > best checkpoint in model_path.
        """
        if checkpoint_path and Path(checkpoint_path).exists():
            return checkpoint_path

        if model_path:
            model_dir = Path(model_path)
            # Check for checkpoint dir
            ckpt_dir = model_dir / "checkpoint" if model_dir.name != "checkpoint" else model_dir
            if ckpt_dir.exists():
                # Prefer best checkpoint
                best = ckpt_dir / "checkpoint_best.pth"
                if best.exists():
                    return str(best)
                # Fall back to any checkpoint
                ckpts = sorted(ckpt_dir.glob("checkpoint_*.pth"))
                if ckpts:
                    return str(ckpts[-1])

        return None

    # ── Online inference (single item, synchronous) ──────────────

    def online_inference(
        self,
        checkpoint_path: str,
        input_data: dict[str, Any] | str,
        device: str = "auto",
    ) -> dict[str, Any]:
        """Run inference on a single input. Returns prediction, confidence, probabilities, latency_ms."""
        start = time.monotonic()

        model, ckpt, dev = self._load_model(checkpoint_path, device)
        arch_type = ckpt.get("arch_type", "mlp")
        is_cv = _is_cv_arch(arch_type)

        with torch.no_grad():
            if is_cv:
                if isinstance(input_data, str):
                    tensor = self._decode_image_input(input_data, dev)
                else:
                    raise ValueError(
                        "CV model requires base64-encoded image input, got dict/tabular data"
                    )
            else:
                tensor = self._decode_tabular_input(input_data, ckpt, dev)

            output = model(tensor)

            if output.shape[-1] > 1:
                # Multi-class classification
                probs = torch.softmax(output, dim=-1)
                confidence, pred_idx = probs.max(dim=-1)
                pred_label = pred_idx.item()
                confidence_val = confidence.item()
                prob_dict = {str(i): round(probs[0, i].item(), 6) for i in range(probs.shape[-1])}
            else:
                # Binary or regression
                if output.shape[-1] == 1:
                    prob = torch.sigmoid(output)
                    pred_label = (prob > 0.5).long().item()
                    confidence_val = prob.item() if pred_label == 1 else 1 - prob.item()
                    prob_dict = {"0": round(1 - prob.item(), 6), "1": round(prob.item(), 6)}
                else:
                    pred_label = output.item()
                    confidence_val = 1.0
                    prob_dict = {}

        latency = round((time.monotonic() - start) * 1000, 2)

        return {
            "prediction": pred_label,
            "confidence": round(confidence_val, 6),
            "probabilities": prob_dict,
            "latency_ms": latency,
        }

    def _decode_image_input(self, base64_str: str, device: torch.device) -> torch.Tensor:
        """Decode a base64-encoded image into a normalized tensor."""
        from torchvision import transforms

        img_bytes = base64.b64decode(base64_str)
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        return transform(img).unsqueeze(0).to(device)

    def _decode_tabular_input(
        self,
        input_data: dict[str, Any] | str,
        ckpt: dict,
        device: torch.device,
    ) -> torch.Tensor:
        """Decode tabular input (dict of column→value) into a tensor."""
        if isinstance(input_data, str):
            # Try to parse as JSON
            import json
            input_data = json.loads(input_data)

        input_dim = ckpt.get("input_dim", 20)
        if isinstance(input_data, dict):
            values = [float(v) for v in input_data.values()]
            if len(values) < input_dim:
                values.extend([0.0] * (input_dim - len(values)))
            values = values[:input_dim]
        elif isinstance(input_data, list):
            values = [float(v) for v in input_data]
        else:
            values = [float(input_data)] * input_dim

        return torch.tensor([values], dtype=torch.float32, device=device)

    # ── Batch inference (async task) ─────────────────────────────

    def start_batch_inference(
        self,
        model_id: str,
        checkpoint_path: str,
        dataset_path: str,
        arch_type: str,
        device: str = "auto",
    ) -> str:
        """Start batch inference as a background task. Returns task_id."""
        task_id = str(uuid.uuid4())
        _tasks[task_id] = {
            "task_id": task_id,
            "model_id": model_id,
            "status": "pending",
            "progress": 0.0,
            "predictions": [],
            "result_path": None,
            "created_at": time.time(),
            "finished_at": None,
        }
        return task_id

    def run_batch_inference(
        self,
        task_id: str,
        checkpoint_path: str,
        dataset_path: str,
        arch_type: str,
        output_dir: str,
        device: str = "auto",
    ) -> None:
        """Execute batch inference. Called from background thread."""
        task = _tasks.get(task_id)
        if not task:
            return

        task["status"] = "running"
        try:
            model, ckpt, dev = self._load_model(checkpoint_path, device)
            loader = self._load_dataset_for_inference(dataset_path, arch_type)
            if loader is None:
                task["status"] = "failed"
                return

            predictions = []
            total = len(loader.dataset)
            done = 0

            with torch.no_grad():
                for X, _ in loader:
                    X = X.to(dev)
                    output = model(X)
                    if output.shape[-1] > 1:
                        probs = torch.softmax(output, dim=-1)
                        confs, preds = probs.max(dim=-1)
                    else:
                        probs = torch.sigmoid(output)
                        preds = (probs > 0.5).long().squeeze()
                        confs = torch.where(preds == 1, probs, 1 - probs).squeeze()

                    for i in range(X.shape[0]):
                        predictions.append({
                            "prediction": preds[i].item() if preds.dim() > 0 else preds.item(),
                            "confidence": round(confs[i].item() if confs.dim() > 0 else confs.item(), 6),
                        })

                    done += X.shape[0]
                    task["progress"] = round(done / total, 4)

            # Save results
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            result_path = str(Path(output_dir) / f"batch_{task_id}.json")
            import json
            with open(result_path, "w") as f:
                json.dump(predictions, f, ensure_ascii=False)

            task["status"] = "success"
            task["progress"] = 1.0
            task["predictions"] = predictions
            task["result_path"] = result_path

        except Exception as e:
            task["status"] = "failed"
            task["predictions"] = []
            task["result_path"] = None
            task["error"] = str(e)
        finally:
            task["finished_at"] = time.time()

    # ── Evaluation ───────────────────────────────────────────────

    def evaluate(
        self,
        checkpoint_path: str,
        dataset_path: str,
        arch_type: str,
        metrics: list[str] | None = None,
        device: str = "auto",
    ) -> dict[str, Any]:
        """Evaluate model on a dataset. Returns metrics, confusion_matrix, classification_report."""
        model, ckpt, dev = self._load_model(checkpoint_path, device)
        loader = self._load_dataset_for_inference(dataset_path, arch_type)
        if loader is None:
            return {"metrics": {}, "confusion_matrix": [], "classification_report": {}, "num_samples": 0}

        all_preds = []
        all_labels = []

        with torch.no_grad():
            for X, y in loader:
                X = X.to(dev)
                output = model(X)
                if output.shape[-1] > 1:
                    preds = output.argmax(dim=-1)
                else:
                    preds = (torch.sigmoid(output) > 0.5).long().squeeze()

                all_preds.extend(preds.cpu().tolist())
                all_labels.extend(y.tolist())

        preds_arr = np.array(all_preds)
        labels_arr = np.array(all_labels)
        n = len(labels_arr)

        result: dict[str, Any] = {"num_samples": n}

        # Compute metrics
        computed: dict[str, float] = {}
        requested = metrics or ["accuracy", "f1", "precision", "recall"]

        correct = (preds_arr == labels_arr).sum()
        accuracy = correct / max(n, 1)
        computed["accuracy"] = round(accuracy, 6)

        if "f1" in requested or "precision" in requested or "recall" in requested:
            computed.update(self._compute_classification_metrics(preds_arr, labels_arr))

        result["metrics"] = computed

        # Confusion matrix
        n_classes = max(int(labels_arr.max()), int(preds_arr.max())) + 1
        cm = np.zeros((n_classes, n_classes), dtype=int)
        for t, p in zip(labels_arr, preds_arr):
            cm[int(t)][int(p)] += 1
        result["confusion_matrix"] = cm.tolist()

        # Classification report
        report: dict[str, dict[str, float]] = {}
        for cls in range(n_classes):
            tp = cm[cls][cls]
            fp = cm[:, cls].sum() - tp
            fn = cm[cls, :].sum() - tp
            p = tp / max(tp + fp, 1)
            r = tp / max(tp + fn, 1)
            f1 = 2 * p * r / max(p + r, 1e-10)
            report[str(cls)] = {"precision": round(p, 4), "recall": round(r, 4), "f1-score": round(f1, 4), "support": int(cm[cls].sum())}
        result["classification_report"] = report

        return result

    def _compute_classification_metrics(self, preds: np.ndarray, labels: np.ndarray) -> dict[str, float]:
        """Compute macro-averaged precision, recall, F1."""
        n_classes = max(int(labels.max()), int(preds.max())) + 1
        precisions, recalls, f1s = [], [], []

        for cls in range(n_classes):
            tp = ((preds == cls) & (labels == cls)).sum()
            fp = ((preds == cls) & (labels != cls)).sum()
            fn = ((preds != cls) & (labels == cls)).sum()
            p = tp / max(tp + fp, 1)
            r = tp / max(tp + fn, 1)
            f1 = 2 * p * r / max(p + r, 1e-10)
            precisions.append(p)
            recalls.append(r)
            f1s.append(f1)

        return {
            "precision": round(float(np.mean(precisions)), 6),
            "recall": round(float(np.mean(recalls)), 6),
            "f1": round(float(np.mean(f1s)), 6),
        }

    # ── ONNX Export ──────────────────────────────────────────────

    def export_onnx(
        self,
        checkpoint_path: str,
        output_path: str,
        opset_version: int = 17,
        dynamic_batch: bool = True,
    ) -> str:
        """Export model to ONNX format. Returns the output path."""
        model, ckpt, dev = self._load_model(checkpoint_path, device="cpu")

        arch_type = ckpt.get("arch_type", "mlp")
        is_cv = _is_cv_arch(arch_type)
        n_classes = ckpt.get("n_classes", 3)
        input_dim = ckpt.get("input_dim", 20)

        if is_cv:
            dummy_input = torch.randn(1, 3, 224, 224)
        else:
            dummy_input = torch.randn(1, input_dim)

        dynamic_axes = None
        if dynamic_batch:
            dynamic_axes = {"input": {0: "batch_size"}, "output": {0: "batch_size"}}

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            opset_version=opset_version,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes=dynamic_axes,
        )

        return output_path

    # ── Dataset loading for inference ────────────────────────────

    def _load_dataset_for_inference(
        self,
        dataset_path: str,
        arch_type: str,
        batch_size: int = 32,
    ) -> torch.utils.data.DataLoader | None:
        """Load a dataset for inference/evaluation. Returns None if not loadable."""
        from src.engine.train_worker import _load_tabular_dataset, _load_image_dataset, _make_synthetic_loader, _make_synthetic_cv_loader

        path = Path(dataset_path)
        if not path.exists():
            return None

        is_cv = _is_cv_arch(arch_type)

        if is_cv:
            loader = _load_image_dataset(dataset_path, batch_size)
            if loader is not None:
                return loader
            loader = _load_tabular_dataset(dataset_path, batch_size)
            if loader is not None:
                return loader
            return _make_synthetic_cv_loader(n_samples=64, batch_size=batch_size)
        else:
            loader = _load_tabular_dataset(dataset_path, batch_size)
            if loader is not None:
                return loader
            return _make_synthetic_loader(n_samples=128, batch_size=batch_size)

    # ── Task management ──────────────────────────────────────────

    @staticmethod
    def get_task(task_id: str) -> dict[str, Any] | None:
        return _tasks.get(task_id)

    @staticmethod
    def create_task(model_id: str) -> str:
        task_id = str(uuid.uuid4())
        _tasks[task_id] = {
            "task_id": task_id,
            "model_id": model_id,
            "status": "pending",
            "progress": 0.0,
            "predictions": [],
            "result_path": None,
            "created_at": time.time(),
            "finished_at": None,
        }
        return task_id

    @staticmethod
    def update_task(task_id: str, **kwargs: Any) -> None:
        task = _tasks.get(task_id)
        if task:
            task.update(kwargs)
