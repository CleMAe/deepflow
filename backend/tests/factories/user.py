from __future__ import annotations

import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.core.security import hash_password
from src.infra.db.models.user import User, UserRole


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    username = factory.Sequence(lambda n: f"testuser_{n}")
    password_hash = factory.LazyFunction(lambda: hash_password("testpass123"))
    role = UserRole.DEVELOPER
