"""Async database engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.infra.config import get_settings

_engine = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def init_engine(database_url: Optional[str] = None) -> None:
    global _engine, _session_factory
    url = database_url or get_settings().database_url
    _engine = create_async_engine(url, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        yield session
