"""Sync database engine and session factory (Day1 default)."""

from __future__ import annotations

from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infra.config import get_settings

_engine = None
SessionLocal: Optional[sessionmaker[Session]] = None


def init_engine(database_url: Optional[str] = None) -> sessionmaker[Session]:
    global _engine, SessionLocal
    url = database_url or get_settings().database_url
    _engine = create_engine(url, echo=False)
    SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return SessionLocal


def get_engine():
    global _engine
    if _engine is None:
        init_engine()
    return _engine


def get_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        init_engine()
    assert SessionLocal is not None
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
