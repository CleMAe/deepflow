"""Mock `CleaningProtocol` — Day2 replaces with pandas engine."""

from __future__ import annotations

import uuid

from app.repositories.dataset_repository import DatasetRepository
from app.schemas.cleaning import CleaningResultSchema
from app.services.dataset_service import DatasetService
from app.services.storage_mock import MockFileStorage


class MockCleaningService:
    def __init__(
        self,
        repo: DatasetRepository,
        storage: MockFileStorage,
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
            format=source.format,
            file_path=cleaned_path,
            num_samples=source.num_samples,
            columns_meta=source.columns_meta,
            tags=list(source.tags or []),
            status="cleaned",
        )
        return CleaningResultSchema(
            rows_before=source.num_samples,
            rows_after=source.num_samples,
            columns_affected=[],
            changes_summary={"operation": operation, "mock": True},
            dataset_id=row.id,
        )
