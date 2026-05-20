from __future__ import annotations

import asyncio
import json
from collections.abc import Generator

from app import main
from app.core.errors import ERR_SYSTEM_DB_UNAVAILABLE


class FakeDb:
    def execute(self, statement):
        self.statement = statement

    def commit(self):
        self.committed = True


def test_health_route_uses_api_v1_prefix():
    paths = {route.path for route in main.app.routes}

    assert "/api/v1/health" in paths
    assert "/health" not in paths


def test_health_returns_success_and_closes_db_session(monkeypatch):
    closed = False

    def fake_get_db() -> Generator[FakeDb, None, None]:
        nonlocal closed
        try:
            yield FakeDb()
        finally:
            closed = True

    monkeypatch.setattr(main, "get_db", fake_get_db)

    response = asyncio.run(main.health())

    assert response["code"] == 0
    assert response["data"]["status"] == "ok"
    assert response["data"]["db"] == "connected"
    assert closed is True


def test_health_returns_503_when_db_unavailable(monkeypatch):
    closed = False

    def fake_get_db() -> Generator[FakeDb, None, None]:
        nonlocal closed
        try:
            raise RuntimeError("database unavailable")
            yield FakeDb()
        finally:
            closed = True

    monkeypatch.setattr(main, "get_db", fake_get_db)

    response = asyncio.run(main.health())
    body = json.loads(response.body)

    assert response.status_code == 503
    assert body["code"] == ERR_SYSTEM_DB_UNAVAILABLE
    assert body["message"] == "Database unavailable"
    assert body["data"]["status"] == "degraded"
    assert body["data"]["db"] == "disconnected"
    assert closed is True
