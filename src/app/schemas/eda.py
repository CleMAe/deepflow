from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EdaRequest(BaseModel):
    columns: list[str] = Field(default_factory=list)
    include_visualizations: bool = True


class AugmentTransform(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)


class AugmentRequest(BaseModel):
    transforms: list[AugmentTransform]
    num_augmented: int = 1
    output_dataset_name: str | None = None


class SplitRatios(BaseModel):
    train: float
    val: float | None = None
    test: float | None = None


class SplitRequest(BaseModel):
    ratios: SplitRatios
    stratify_column: str | None = None
    random_seed: int = 42


class SplitResultSchema(BaseModel):
    train_dataset_id: UUID
    val_dataset_id: UUID | None = None
    test_dataset_id: UUID | None = None
    train_count: int
    val_count: int
    test_count: int
