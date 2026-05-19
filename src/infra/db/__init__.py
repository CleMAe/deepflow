"""Database package — SQLAlchemy models and session management."""

from src.infra.db.base import Base

__all__ = ["Base", "SessionLocal", "get_session", "init_engine"]


def __getattr__(name: str):
    if name in ("get_session", "init_engine", "SessionLocal"):
        from src.infra.db import session

        return getattr(session, name)
    raise AttributeError(name)
