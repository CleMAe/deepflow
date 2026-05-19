"""Mock `CleaningProtocol` — Day2 replaces with pandas engine."""

from __future__ import annotations

import uuid

from app.repositories.dataset_repository import DatasetRepository
from app.schemas.cleaning import CleaningResultSchema
from app.services.dataset_service import DatasetService
from shared.protocols import StorageProtocol

_OPERATION_EFFECTS: dict[str, dict] = {
    "missing": {"rows_removed": 12, "columns_affected": ["age", "income"], "summary_key": "strategy", "summary_val": "fill_median"},
    "outlier": {"rows_removed": 5, "columns_affected": ["amount", "score"], "summary_key": "method", "summary_val": "iqr"},
    "dedup": {"rows_removed": 23, "columns_affected": [], "summary_key": "keep", "summary_val": "first"},
    "encode": {"rows_removed": 0, "columns_affected": ["category", "region"], "summary_key": "method", "summary_val": "label_encoding"},
    "type-convert": {"rows_removed": 0, "columns_affected": ["price", "date"], "summary_key": "conversions", "summary_val": 2},
}


class MockCleaningService:
    def __init__(
        self,
        repo: DatasetRepository,
        storage: StorageProtocol,
        datasets: DatasetService,
    ) -> None:
        self._repo = repo
        self._storage = storage
        self._datasets = datasets

    def run(self, project_id: uuid.UUID, dataset_id: uuid.UUID, operation: str) -> CleaningResultSchema:
        source_row = self._repo.get_by_id_and_project(dataset_id, project_id)
        if not source_row:
            from app.core.errors import AppError

            raise AppError.not_found("Dataset not found")

        source = source_row
        new_id = uuid.uuid4()
        cleaned_path = self._storage.get_cleaned_path(str(project_id), str(new_id))
        row = self._repo.create(
            project_id=project_id,
            name=f"{source.name}_{operation}",
            format=source.format.value if hasattr(source.format, "value") else source.format,
            file_path=cleaned_path,
            num_samples=source.num_samples,
            columns_meta=source.columns_meta,
            tags=list(source.tags or []),
            status="cleaned",
        )

        effect = _OPERATION_EFFECTS.get(operation, {"rows_removed": 0, "columns_affected": [], "summary_key": "operation", "summary_val": operation})
        rows_before = source.num_samples
        rows_after = rows_before - effect["rows_removed"]

        return CleaningResultSchema(
            rows_before=rows_before,
            rows_after=rows_after,
            columns_affected=effect["columns_affected"],
            changes_summary={"operation": operation, effect["summary_key"]: effect["summary_val"], "mock": True},
            dataset_id=row.id,
        )
