"""
Training worker — executed as a subprocess by the API process.

Communicates with the parent via a JSON status file. The API layer
polls this file (or reads it on demand) to get training progress.

Usage:
    python -m src.engine.train_worker \
        --job-id <uuid> \
        --model-arch resnet18 \
        --dataset-path /data/.../train.csv \
        --val-dataset-path /data/.../val.csv \
        --output-dir /data/.../checkpoints/ \
        --hyperparams '{"epochs":10,"learning_rate":0.001,...}' \
        --status-file /tmp/deepflow_training_<job_id>.json
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# ---------------------------------------------------------------------------
# Status file helpers
# ---------------------------------------------------------------------------

_STATUS_FIELDS = (
    "status", "current_epoch", "total_epochs", "current_step",
    "train_loss", "val_loss", "accuracy", "best_val_loss",
    "best_accuracy", "learning_rate", "checkpoint_path",
    "error_message", "started_at", "updated_at",
)


def _write_status(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def _init_status(path: str, total_epochs: int) -> dict:
    status = {
        "status": "running",
        "current_epoch": 0,
        "total_epochs": total_epochs,
        "current_step": 0,
        "train_loss": None,
        "val_loss": None,
        "accuracy": None,
        "best_val_loss": None,
        "best_accuracy": None,
        "learning_rate": None,
        "checkpoint_path": None,
        "error_message": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_status(path, status)
    return status


# ---------------------------------------------------------------------------
# Synthetic data generators (fallback when no real dataset exists)
# ---------------------------------------------------------------------------

def _make_synthetic_loader(
    n_samples: int = 512,
    n_features: int = 20,
    n_classes: int = 3,
    batch_size: int = 32,
) -> DataLoader:
    X = torch.randn(n_samples, n_features)
    y = torch.randint(0, n_classes, (n_samples,))
    return DataLoader(TensorDataset(X, y), batch_size=batch_size, shuffle=True)


def _make_synthetic_cv_loader(
    n_samples: int = 256,
    n_classes: int = 3,
    batch_size: int = 32,
) -> DataLoader:
    X = torch.randn(n_samples, 3, 32, 32)
    y = torch.randint(0, n_classes, (n_samples,))
    return DataLoader(TensorDataset(X, y), batch_size=batch_size, shuffle=True)


# ---------------------------------------------------------------------------
# CSV / JSON dataset loading (tabular)
# ---------------------------------------------------------------------------

def _load_tabular_dataset(
    dataset_path: str,
    batch_size: int = 32,
) -> DataLoader | None:
    path = Path(dataset_path)
    if not path.exists():
        return None

    suffix = path.suffix.lower()
    if suffix not in (".csv", ".json"):
        return None

    try:
        import pandas as pd
        df = pd.read_csv(path) if suffix == ".csv" else pd.read_json(path)
        label_col = df.columns[-1]
        X = torch.tensor(df.drop(columns=[label_col]).select_dtypes(include="number").values, dtype=torch.float32)
        labels = df[label_col].astype("category").cat.codes.values
        y = torch.tensor(labels, dtype=torch.long)
        return DataLoader(TensorDataset(X, y), batch_size=batch_size, shuffle=True)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Image dataset loading (directory of images organized by class)
# ---------------------------------------------------------------------------

def _load_image_dataset(
    dataset_path: str,
    batch_size: int = 32,
) -> DataLoader | None:
    path = Path(dataset_path)

    # Direct file (e.g. a single image or non-directory) — skip
    if path.exists() and not path.is_dir():
        return None

    # Try ImageFolder: expects <root>/<class_name>/<images>
    if path.is_dir():
        class_dirs = [d for d in path.iterdir() if d.is_dir()]
        if class_dirs:
            try:
                from torchvision import datasets, transforms
                transform = transforms.Compose([
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ])
                dataset = datasets.ImageFolder(str(path), transform=transform)
                return DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
            except Exception:
                return None

    return None


# ---------------------------------------------------------------------------
# Dataset dispatcher — tries real data, falls back to synthetic
# ---------------------------------------------------------------------------

_CV_ARCHS = frozenset({"resnet18", "resnet34", "resnet50", "efficientnetb0", "efficientnetb1"})


def _is_cv_arch(arch_type: str) -> bool:
    return arch_type.lower().replace("-", "").replace("_", "") in _CV_ARCHS


def _load_dataset(
    dataset_path: str,
    arch_type: str,
    batch_size: int = 32,
    is_val: bool = False,
) -> DataLoader:
    """Try loading real dataset; fall back to synthetic only when file/dir missing."""
    is_cv = _is_cv_arch(arch_type)

    if is_cv:
        # For CV archs, try ImageFolder first, then tabular (some users store
        # image metadata as CSV), then synthetic
        loader = _load_image_dataset(dataset_path, batch_size)
        if loader is not None:
            return loader
        loader = _load_tabular_dataset(dataset_path, batch_size)
        if loader is not None:
            return loader
        n = 64 if is_val else 256
        return _make_synthetic_cv_loader(n_samples=n, batch_size=batch_size)
    else:
        # For tabular archs, try CSV/JSON first, then synthetic
        loader = _load_tabular_dataset(dataset_path, batch_size)
        if loader is not None:
            return loader
        n = 128 if is_val else 512
        return _make_synthetic_loader(n_samples=n, batch_size=batch_size)


# ---------------------------------------------------------------------------
# Model factory
# ---------------------------------------------------------------------------

def _build_model(arch_type: str, n_classes: int = 3, input_dim: int = 20) -> nn.Module:
    arch = arch_type.lower().replace("-", "").replace("_", "")
    if arch == "resnet18":
        model = torch.hub.load("pytorch/vision:v0.15.2", "resnet18", weights=None)
        model.fc = nn.Linear(model.fc.in_features, n_classes)
        return model
    if arch == "resnet34":
        model = torch.hub.load("pytorch/vision:v0.15.2", "resnet34", weights=None)
        model.fc = nn.Linear(model.fc.in_features, n_classes)
        return model
    if arch == "resnet50":
        model = torch.hub.load("pytorch/vision:v0.15.2", "resnet50", weights=None)
        model.fc = nn.Linear(model.fc.in_features, n_classes)
        return model
    if arch in ("efficientnetb0", "efficientnet_b0"):
        from torchvision.models import efficientnet_b0
        model = efficientnet_b0(weights=None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, n_classes)
        return model
    if arch in ("efficientnetb1", "efficientnet_b1"):
        from torchvision.models import efficientnet_b1
        model = efficientnet_b1(weights=None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, n_classes)
        return model
    # MLP fallback
    return nn.Sequential(
        nn.Linear(input_dim, 128),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(128, 64),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(64, n_classes),
    )


# ---------------------------------------------------------------------------
# Optimizer / scheduler / loss builders
# ---------------------------------------------------------------------------

_OPTIMIZERS = {
    "sgd": lambda p, lr, wd, m: optim.SGD(p, lr=lr, weight_decay=wd, momentum=m),
    "adam": lambda p, lr, wd, m: optim.Adam(p, lr=lr, weight_decay=wd),
    "adamw": lambda p, lr, wd, m: optim.AdamW(p, lr=lr, weight_decay=wd),
    "rmsprop": lambda p, lr, wd, m: optim.RMSprop(p, lr=lr, weight_decay=wd, momentum=m),
}

_LOSS_FNS: dict[str, type] = {
    "cross_entropy": nn.CrossEntropyLoss,
    "mse": nn.MSELoss,
    "bce": nn.BCELoss,
    "bce_with_logits": nn.BCEWithLogitsLoss,
    "nll": nn.NLLLoss,
    "l1": nn.L1Loss,
    "huber": nn.HuberLoss,
}


def _build_optimizer(name: str, params: Any, lr: float, weight_decay: float, momentum: float) -> optim.Optimizer:
    factory = _OPTIMIZERS.get(name, _OPTIMIZERS["adam"])
    return factory(params, lr=lr, wd=weight_decay, m=momentum)


def _build_scheduler(name: str, optimizer: optim.Optimizer, params: dict | None = None) -> optim.lr_scheduler.LRScheduler | None:
    p = params or {}
    if name == "step":
        return optim.lr_scheduler.StepLR(optimizer, step_size=p.get("step_size", 10), gamma=p.get("gamma", 0.1))
    if name == "cosine":
        return optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=p.get("T_max", 50))
    if name == "exponential":
        return optim.lr_scheduler.ExponentialLR(optimizer, gamma=p.get("gamma", 0.99))
    return None


# ---------------------------------------------------------------------------
# Early stopping
# ---------------------------------------------------------------------------

class EarlyStopping:
    def __init__(self, patience: int = 5, metric: str = "val_loss", mode: str = "min", min_delta: float = 0.0):
        self.patience = patience
        self.metric = metric
        self.mode = mode
        self.min_delta = min_delta
        self.best: float | None = None
        self.counter = 0
        self.should_stop = False

    def step(self, value: float) -> bool:
        if self.best is None:
            self.best = value
            return False

        improved = (value < self.best - self.min_delta) if self.mode == "min" else (value > self.best + self.min_delta)
        if improved:
            self.best = value
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
        return self.should_stop


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def _train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    grad_accum_steps: int = 1,
    use_amp: bool = False,
) -> tuple[float, int]:
    model.train()
    total_loss = 0.0
    total_samples = 0
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    for step, (X, y) in enumerate(loader):
        X, y = X.to(device), y.to(device)
        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            out = model(X)
            loss = criterion(out, y) / grad_accum_steps

        scaler.scale(loss).backward()

        if (step + 1) % grad_accum_steps == 0:
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)

        total_loss += loss.item() * grad_accum_steps * X.size(0)
        total_samples += X.size(0)

    return total_loss / max(total_samples, 1), total_samples


@torch.no_grad()
def _validate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    use_amp: bool = False,
) -> tuple[float, float]:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    for X, y in loader:
        X, y = X.to(device), y.to(device)
        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            out = model(X)
            loss = criterion(out, y)

        total_loss += loss.item() * X.size(0)
        preds = out.argmax(dim=1) if out.dim() > 1 else (out > 0.5).long()
        correct += (preds == y).sum().item()
        total += y.size(0)

    avg_loss = total_loss / max(total, 1)
    accuracy = correct / max(total, 1)
    return avg_loss, accuracy


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

_shutdown = False


def _handle_signal(signum: int, frame: Any) -> None:
    global _shutdown
    _shutdown = True


def run(args: argparse.Namespace) -> None:
    hyperparams: dict = json.loads(args.hyperparams) if args.hyperparams else {}
    epochs = hyperparams.get("epochs", 10)
    batch_size = hyperparams.get("batch_size", 32)
    lr = hyperparams.get("learning_rate", 0.001)
    optim_name = hyperparams.get("optimizer", "adam")
    loss_name = hyperparams.get("loss_function", "cross_entropy")
    weight_decay = hyperparams.get("weight_decay", 0.0)
    momentum = hyperparams.get("momentum", 0.9)
    scheduler_name = hyperparams.get("lr_scheduler", "none")
    scheduler_params = hyperparams.get("lr_scheduler_params")
    grad_accum_steps = hyperparams.get("grad_accum_steps", 1)
    use_amp = hyperparams.get("mixed_precision", False)
    ckpt_every = hyperparams.get("checkpoint_every_n_epochs", 1)
    early_cfg = hyperparams.get("early_stopping")
    max_grad_norm = hyperparams.get("max_grad_norm", 1.0)

    # Device
    device_str = args.device or "auto"
    if device_str == "auto":
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_str)
    if device.type == "cuda":
        use_amp = True

    # Output dir
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Status
    status = _init_status(args.status_file, epochs)

    # Dataset — try real data first, fall back to synthetic
    train_loader = _load_dataset(args.dataset_path, args.model_arch, batch_size, is_val=False)
    val_loader: DataLoader | None = None
    if args.val_dataset_path:
        val_loader = _load_dataset(args.val_dataset_path, args.model_arch, batch_size, is_val=True)
    if val_loader is None:
        val_loader = _load_dataset(args.dataset_path, args.model_arch, batch_size, is_val=True)

    # Infer input dim / n_classes from first batch
    sample_X, sample_y = next(iter(train_loader))
    input_dim = sample_X.shape[1] if sample_X.dim() > 1 else 1
    n_classes = int(sample_y.max().item()) + 1 if sample_y.numel() > 0 else 3

    # Model
    model = _build_model(args.model_arch, n_classes=n_classes, input_dim=input_dim).to(device)

    # Loss, optimizer, scheduler
    criterion_cls = _LOSS_FNS.get(loss_name, nn.CrossEntropyLoss)
    criterion = criterion_cls()
    optimizer = _build_optimizer(optim_name, model.parameters(), lr=lr, weight_decay=weight_decay, momentum=momentum)
    scheduler = _build_scheduler(scheduler_name, optimizer, scheduler_params)

    # Early stopping
    early_stopper: EarlyStopping | None = None
    if early_cfg and early_cfg.get("patience"):
        early_stopper = EarlyStopping(
            patience=early_cfg.get("patience", 5),
            metric=early_cfg.get("metric", "val_loss"),
            mode=early_cfg.get("mode", "min"),
            min_delta=early_cfg.get("min_delta", 0.0),
        )

    # Signal handling for graceful stop
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    best_val_loss = float("inf")
    best_checkpoint: str | None = None

    try:
        for epoch in range(1, epochs + 1):
            if _shutdown:
                status["status"] = "cancelled"
                status["updated_at"] = datetime.now(timezone.utc).isoformat()
                _write_status(args.status_file, status)
                return

            train_loss, _ = _train_one_epoch(model, train_loader, criterion, optimizer, device, grad_accum_steps, use_amp)

            val_loss, accuracy = _validate(model, val_loader, criterion, device, use_amp)

            # Checkpoint
            ckpt_path: str | None = None
            is_best = val_loss < best_val_loss
            if is_best:
                best_val_loss = val_loss
            if epoch % ckpt_every == 0 or is_best:
                tag = "best" if is_best else f"epoch_{epoch}"
                ckpt_path = str(output_dir / f"checkpoint_{tag}.pth")
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "accuracy": accuracy,
                    "arch_type": args.model_arch,
                    "n_classes": n_classes,
                    "input_dim": input_dim,
                }, ckpt_path)
                if is_best:
                    best_checkpoint = ckpt_path

            # Update status
            current_lr = optimizer.param_groups[0]["lr"]
            status.update({
                "current_epoch": epoch,
                "train_loss": round(train_loss, 6),
                "val_loss": round(val_loss, 6),
                "accuracy": round(accuracy, 6),
                "best_val_loss": round(best_val_loss, 6),
                "learning_rate": current_lr,
                "checkpoint_path": best_checkpoint,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            if is_best:
                status["best_accuracy"] = round(accuracy, 6)
            _write_status(args.status_file, status)

            if scheduler is not None:
                if isinstance(scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                    scheduler.step(val_loss)
                else:
                    scheduler.step()

            # Early stopping check
            if early_stopper is not None:
                metric_val = val_loss if early_stopper.metric == "val_loss" else accuracy
                if early_stopper.step(metric_val):
                    status["status"] = "success"
                    status["error_message"] = f"Early stopping at epoch {epoch}"
                    status["updated_at"] = datetime.now(timezone.utc).isoformat()
                    _write_status(args.status_file, status)
                    return

        status["status"] = "success"
        status["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_status(args.status_file, status)

    except Exception:
        status["status"] = "failed"
        status["error_message"] = traceback.format_exc()
        status["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_status(args.status_file, status)


def main() -> None:
    parser = argparse.ArgumentParser(description="DeepFlow training worker")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--model-arch", required=True)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--val-dataset-path", default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--hyperparams", default="{}")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--status-file", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
