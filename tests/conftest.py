import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setattr(settings, "dev_allow_anonymous", True)
    monkeypatch.setattr(settings, "mock_mode", True)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
