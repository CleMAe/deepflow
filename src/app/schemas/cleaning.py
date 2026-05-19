from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CleanMissingRequest(BaseModel):
    columns: list[str] = Field(default_factory=list)
    strategy: str = "drop_row"
    fill_value: Any = None
    create_new_version: bool = True


class CleanOutlierRequest(BaseModel):
    columns: list[str]
    method: str = "zscore"
    threshold: float | None = None
    action: str = "drop"


class CleanDedupRequest(BaseModel):
    columns: list[str] = Field(default_factory=list)
    keep: str = "first"


class CleanEncodeRequest(BaseModel):
    columns: list[str]
    method: str = "one_hot"


class TypeConversionItem(BaseModel):
    column: str
    target_type: str
    datetime_format: str | None = None


class CleanTypeConvertRequest(BaseModel):
    conversions: list[TypeConversionItem]


class CleaningResultSchema(BaseModel):
    rows_before: int
    rows_after: int
    columns_affected: list[str]
    changes_summary: dict[str, Any] = Field(default_factory=dict)
    dataset_id: UUID
