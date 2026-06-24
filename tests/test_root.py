"""
tests/test_root.py — Tests for the root endpoint and core app behaviour.
"""

import pytest
from app.core.config import get_settings


def test_root_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_root_response_keys(client):
    """Root endpoint must return the four documented keys."""
    data = client.get("/").json()
    assert "message" in data
    assert "app_name" in data
    assert "app_env" in data
    assert "redcap_mock_enabled" in data


def test_root_message(client):
    data = client.get("/").json()
    assert data["message"] == "hello neps"


def test_root_app_name(client):
    settings = get_settings()
    data = client.get("/").json()
    assert data["app_name"] == settings.APP_NAME


def test_root_mock_enabled(client):
    """In the test environment REDCAP_MOCK_ENABLED is forced to True."""
    data = client.get("/").json()
    assert data["redcap_mock_enabled"] is True


def test_openapi_schema_accessible(client):
    """FastAPI /openapi.json must be reachable (docs are not disabled)."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
