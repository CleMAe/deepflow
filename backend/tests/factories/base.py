from __future__ import annotations

import factory
from factory.alchemy import SQLAlchemyModelFactory

from tests.support.models import TestRecord


class TestRecordFactory(SQLAlchemyModelFactory):
    class Meta:
        model = TestRecord
        sqlalchemy_session_persistence = "flush"

    name = factory.Faker("word")
