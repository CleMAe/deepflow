"""Database package — SQLAlchemy models and session management."""

from src.infra.db.base import Base

__all__ = ["Base"]


def __getattr__(name: str):
    if name in ("get_async_session", "init_engine"):
        from src.infra.db import session

        return getattr(session, name)
    raise AttributeError(name)
