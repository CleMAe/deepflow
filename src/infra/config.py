"""Application configuration."""

import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        # Sync SQLAlchemy URL (used by Alembic, FastAPI routers, and session.py).
        # Day1 uses sync sessions only; introduce async engine in a later perf pass.
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "sqlite:///./deepflow.db",
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
