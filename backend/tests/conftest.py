"""Shared pytest fixtures.

All tests run against an in-memory SQLite database that is rebuilt for every
test function. The settings singleton is cleared and re-read with a SQLite URL
*before* any app module is imported, so the engine/session wiring points at the
test database.
"""

from __future__ import annotations

import os
import sys

import pytest

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_root)

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("ALLOW_DEMO_DATA", "true")
os.environ.setdefault("ENVIRONMENT", "development")


@pytest.fixture(scope="session", autouse=True)
def _test_settings():
    from app.core.config import get_settings

    get_settings.cache_clear()
    return get_settings()


@pytest.fixture()
def client(_test_settings):
    """FastAPI TestClient with a freshly created empty schema per test."""
    from fastapi.testclient import TestClient

    from app import models  # noqa: F401  ensure all models are registered
    from app.database.base import Base
    from app.database.session import engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client):
    """Register a default user and return headers carrying its access token."""

    def _register(email: str = "user@example.com", password: str = "Str0ng!pass") -> dict[str, str]:
        resp = client.post(
            "/api/v1/auth/register",
            json={"name": "Test User", "email": email, "password": password},
        )
        assert resp.status_code == 201, resp.text
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _register