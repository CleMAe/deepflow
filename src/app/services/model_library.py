"""
Model library — registry of pre-built architectures with default
hyperparams and config validation. Implements ModelRegistryProtocol.
"""

from __future__ import annotations

from typing import Any

from shared.protocols import ValidationResult

# ---------------------------------------------------------------------------
# Library entries
# ---------------------------------------------------------------------------

_LIBRARY: list[dict[str, Any]] = [
    {
        "model_id": "resnet18",
        "name": "ResNet-18",
        "arch_type": "resnet18",
        "task_type": "classification",
        "description": "18-layer residual network — good baseline for image classification",
        "input_shape": [3, 224, 224],
        "num_params": 11_689_512,
        "default_hyperparams": {
            "epochs": 20,
            "batch_size": 32,
            "learning_rate": 0.001,
            "optimizer": "adam",
            "loss_function": "cross_entropy",
            "weight_decay": 0.0001,
            "lr_scheduler": "cosine",
            "grad_accum_steps": 1,
            "mixed_precision": False,
            "early_stopping": {"patience": 7, "metric": "val_loss", "mode": "min", "min_delta": 0.0},
            "checkpoint_every_n_epochs": 1,
        },
        "supported_datasets": ["image"],
        "pretrained_available": True,
    },
    {
        "model_id": "resnet34",
        "name": "ResNet-34",
        "arch_type": "resnet34",
        "task_type": "classification",
        "description": "34-layer residual network — balanced depth for medium datasets",
        "input_shape": [3, 224, 224],
        "num_params": 21_797_672,
        "default_hyperparams": {
            "epochs": 30,
            "batch_size": 32,
            "learning_rate": 0.001,
            "optimizer": "adam",
            "loss_function": "cross_entropy",
            "weight_decay": 0.0001,
            "lr_scheduler": "cosine",
            "early_stopping": {"patience": 7, "metric": "val_loss", "mode": "min"},
            "checkpoint_every_n_epochs": 1,
        },
        "supported_datasets": ["image"],
        "pretrained_available": True,
    },
    {
        "model_id": "resnet50",
        "name": "ResNet-50",
        "arch_type": "resnet50",
        "task_type": "classification",
        "description": "50-layer residual network — high accuracy for large datasets",
        "input_shape": [3, 224, 224],
        "num_params": 25_557_032,
        "default_hyperparams": {
            "epochs": 30,
            "batch_size": 16,
            "learning_rate": 0.001,
            "optimizer": "adamw",
            "loss_function": "cross_entropy",
            "weight_decay": 0.01,
            "lr_scheduler": "cosine",
            "mixed_precision": True,
            "early_stopping": {"patience": 10, "metric": "val_loss", "mode": "min"},
            "checkpoint_every_n_epochs": 1,
        },
        "supported_datasets": ["image"],
        "pretrained_available": True,
    },
    {
        "model_id": "efficientnet_b0",
        "name": "EfficientNet-B0",
        "arch_type": "efficientnet_b0",
        "task_type": "classification",
        "description": "EfficientNet-B0 — best FLOPs/accuracy trade-off",
        "input_shape": [3, 224, 224],
        "num_params": 5_288_548,
        "default_hyperparams": {
            "epochs": 20,
            "batch_size": 32,
            "learning_rate": 0.001,
            "optimizer": "adam",
            "loss_function": "cross_entropy",
            "weight_decay": 0.0001,
            "lr_scheduler": "cosine",
            "early_stopping": {"patience": 7, "metric": "val_loss", "mode": "min"},
            "checkpoint_every_n_epochs": 1,
        },
        "supported_datasets": ["image"],
        "pretrained_available": True,
    },
    {
        "model_id": "efficientnet_b1",
        "name": "EfficientNet-B1",
        "arch_type": "efficientnet_b1",
        "task_type": "classification",
        "description": "EfficientNet-B1 — slightly larger than B0, higher accuracy ceiling",
        "input_shape": [3, 240, 240],
        "num_params": 7_794_184,
        "default_hyperparams": {
            "epochs": 25,
            "batch_size": 32,
            "learning_rate": 0.001,
            "optimizer": "adam",
            "loss_function": "cross_entropy",
            "weight_decay": 0.0001,
            "lr_scheduler": "cosine",
            "early_stopping": {"patience": 7, "metric": "val_loss", "mode": "min"},
            "checkpoint_every_n_epochs": 1,
        },
        "supported_datasets": ["image"],
        "pretrained_available": True,
    },
    {
        "model_id": "mlp",
        "name": "MLP (Tabular)",
        "arch_type": "mlp",
        "task_type": "classification",
        "description": "Multi-layer perceptron — baseline for tabular/regression tasks",
        "input_shape": [],
        "num_params": 10_000,
        "default_hyperparams": {
            "epochs": 50,
            "batch_size": 32,
            "learning_rate": 0.001,
            "optimizer": "adam",
            "loss_function": "cross_entropy",
            "weight_decay": 0.0,
            "lr_scheduler": "none",
            "early_stopping": {"patience": 10, "metric": "val_loss", "mode": "min"},
            "checkpoint_every_n_epochs": 5,
        },
        "supported_datasets": ["csv", "json"],
        "pretrained_available": False,
    },
]

_LIBRARY_BY_ID: dict[str, dict[str, Any]] = {e["model_id"]: e for e in _LIBRARY}

_VALID_ARCH_TYPES = {"resnet18", "resnet34", "resnet50", "efficientnet_b0", "efficientnet_b1", "mlp", "custom"}

# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class ModelLibraryService:
    """Real implementation of ModelRegistryProtocol."""

    def list_models(
        self,
        task_type: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        results = _LIBRARY
        if task_type:
            results = [m for m in results if m["task_type"] == task_type]
        if search:
            q = search.lower()
            results = [m for m in results if q in m["name"].lower() or q in m["arch_type"]]
        return results

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        return _LIBRARY_BY_ID.get(model_id)

    def get_default_hyperparams(self, arch_type: str) -> dict[str, Any]:
        for m in _LIBRARY:
            if m["arch_type"] == arch_type:
                return dict(m["default_hyperparams"])
        return {}

    def validate_config(self, arch_type: str, params_cfg: dict[str, Any]) -> ValidationResult:
        errors: list[dict[str, str]] = []

        if arch_type not in _VALID_ARCH_TYPES:
            errors.append({"field": "arch_type", "message": f"Unknown arch_type '{arch_type}', must be one of {sorted(_VALID_ARCH_TYPES)}"})

        if "num_classes" in params_cfg:
            nc = params_cfg["num_classes"]
            if not isinstance(nc, int) or nc < 2:
                errors.append({"field": "num_classes", "message": "num_classes must be an integer >= 2"})

        if "hidden_dims" in params_cfg:
            hd = params_cfg["hidden_dims"]
            if not isinstance(hd, list) or len(hd) == 0:
                errors.append({"field": "hidden_dims", "message": "hidden_dims must be a non-empty list of integers"})

        return ValidationResult(valid=len(errors) == 0, errors=errors)
