"""Pydantic schemas for Training Jobs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EarlyStoppingConfig(BaseModel):
    patience: int = 5
    metric: str = "val_loss"
    mode: str = "min"
    min_delta: float = 0.0


class Hyperparams(BaseModel):
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    optimizer: str = "adam"
    loss_function: str = "cross_entropy"
    weight_decay: float = 0.0
    momentum: float | None = None
    lr_scheduler: str = "none"
    lr_scheduler_params: dict[str, Any] | None = None
    grad_accum_steps: int = 1
    mixed_precision: bool = False
    early_stopping: EarlyStoppingConfig | None = None
    checkpoint_every_n_epochs: int = 1
    max_grad_norm: float | None = None


class TrainingJobCreate(BaseModel):
    name: str
    model_id: str
    dataset_id: str
    val_dataset_id: str | None = None
    hyperparams: Hyperparams = Field(default_factory=Hyperparams)
    device: str = "auto"
    description: str | None = None


class TrainingMetrics(BaseModel):
    train_loss: float | None = None
    val_loss: float | None = None
    accuracy: float | None = None
    best_val_loss: float | None = None
    best_accuracy: float | None = None


class TrainingJobOut(BaseModel):
    id: str
    project_id: str
    name: str
    model_id: str
    dataset_id: str
    val_dataset_id: str | None = None
    hyperparams: dict[str, Any] | None = None
    status: str
    device: str | None = None
    current_epoch: int = 0
    total_epochs: int | None = None
    metrics: TrainingMetrics = Field(default_factory=TrainingMetrics)
    checkpoint: str | None = None
    error_message: str | None = None
    description: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CheckpointOut(BaseModel):
    epoch: int = 0
    step: int = 0
    path: str
    is_best: bool = False
    metrics: dict[str, float] = Field(default_factory=dict)
    file_size: int | None = None
    created_at: str | None = None


class TrainingLogOut(BaseModel):
    logs: list[str] = Field(default_factory=list)
