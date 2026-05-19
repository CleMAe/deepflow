from __future__ import annotations

import factory
from factory.alchemy import SQLAlchemyModelFactory

from src.infra.db.models.project import Project
from tests.factories.user import UserFactory


class ProjectFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Project
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"Test Project {n}")
    description = factory.Faker("sentence")
    owner = factory.SubFactory(UserFactory)
    owner_id = factory.SelfAttribute("owner.id")
    storage_quota = 10240
    storage_used = 0
