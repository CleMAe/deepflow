"""Session factory — delegates to canonical infra session."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from src.infra.db.base import Base
from src.infra.db.session import get_engine, get_session as _infra_get_session


def get_db() -> Generator[Session, None, None]:
    yield from _infra_get_session()


def init_db() -> None:
    import src.infra.db.models  # noqa: F401 — register all models with Base.metadata
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
