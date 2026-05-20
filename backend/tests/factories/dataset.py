from __future__ import annotations

import factory
from factory.alchemy import SQLAlchemyModelFactory

from src.infra.db.models.dataset import Dataset, DatasetFormat, DatasetStatus
from tests.factories.project import ProjectFactory


class DatasetFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Dataset
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"dataset_{n}")
    project = factory.SubFactory(ProjectFactory)
    project_id = factory.SelfAttribute("project.id")
    format = DatasetFormat.CSV
    status = DatasetStatus.READY
    file_path = factory.LazyAttribute(
        lambda o: f"projects/{o.project_id}/datasets/raw/{o.name}.csv"
    )
    num_samples = 100
    num_columns = 2
    columns_meta = factory.LazyFunction(
        lambda: [{"name": "col_a", "dtype": "float64", "nullable": False}]
    )
    tags = factory.LazyFunction(list)
    size_bytes = 1024
