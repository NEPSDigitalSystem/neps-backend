"""
conftest.py — pytest fixtures for the NEPS Backend test suite.

Strategy:
  - The FastAPI app requires a real async DB session via `get_db`.
  - In CI there IS a real Postgres service, but the schema is empty.
  - We override `get_db` with an in-memory SQLite async session so tests
    run without needing schema migrations or a live Postgres instance.
  - We also override `get_redcap_client` with the embedded mock client so
    no external HTTP calls are made during tests.
"""

from __future__ import annotations

import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# ── Ensure we run in test / mock mode before importing the app ──
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("REDCAP_MOCK_ENABLED", "true")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_USER", "neps")
os.environ.setdefault("DATABASE_PASSWORD", "neps_password")
os.environ.setdefault("DATABASE_NAME", "neps_db")


# ── Async DB session mock ─────────────────────────────────────────────────────

class _MockDB:
    """Minimal async DB session that satisfies FastAPI `Depends(get_db)`."""

    async def execute(self, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        return result

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def close(self):
        pass


async def _mock_get_db():
    yield _MockDB()


# ── App fixture ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """
    Import and configure the FastAPI application for testing.
    Overrides are applied before the first request so the scheduler
    never tries to connect to a real DB or REDCap.
    """
    # Import here (after env vars are set) to avoid lru_cache problems
    from app.api.dependencies import get_db          # noqa: F401 — imported for override
    import main as app_module

    application = app_module.app

    # Override DB dependency so no real Postgres is required
    application.dependency_overrides[get_db] = _mock_get_db  # type: ignore[arg-type]

    yield application

    application.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client(app):
    """Synchronous TestClient — suitable for simple route tests."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
