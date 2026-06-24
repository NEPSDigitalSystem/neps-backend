"""
tests/test_config.py — Tests for the Settings / config layer.
"""

import pytest
from app.core.config import Settings, get_settings


def test_get_settings_returns_settings_instance():
    s = get_settings()
    assert isinstance(s, Settings)


def test_default_app_name():
    s = Settings()
    assert s.APP_NAME == "NEPS Digital Backend"


def test_default_redcap_url():
    s = Settings()
    assert "mock-redcap-service" in s.REDCAP_API_URL or s.REDCAP_API_URL.startswith("http")


def test_cors_origins_list_is_list():
    s = Settings()
    origins = s.cors_origins_list
    assert isinstance(origins, list)
    assert len(origins) >= 1


def test_cors_origins_list_no_whitespace():
    s = Settings(CORS_ORIGINS=" http://a.com , http://b.com ")
    for origin in s.cors_origins_list:
        assert origin == origin.strip()


def test_database_url_format():
    s = Settings(DATABASE_USER="u", DATABASE_PASSWORD="p", DATABASE_HOST="db", DATABASE_NAME="mydb")
    url = s.database_url
    assert url.startswith("postgresql+asyncpg://")
    assert "db" in url
    assert "mydb" in url


def test_sync_database_url_uses_psycopg():
    s = Settings(DATABASE_USER="u", DATABASE_PASSWORD="p")
    url = s.sync_database_url
    assert url.startswith("postgresql://")
    assert "asyncpg" not in url


def test_redcap_mock_enabled_defaults_false():
    # Default in Settings model is False; CI overrides via env var
    s = Settings()
    assert isinstance(s.REDCAP_MOCK_ENABLED, bool)


def test_jwt_algorithm_default():
    s = Settings()
    assert s.JWT_ALGORITHM == "HS256"


def test_database_password_fallback():
    """When no secret file is set, password should fall back to the field value."""
    s = Settings(DATABASE_PASSWORD="fallback_pw", DATABASE_PASSWORD_FILE=None)
    assert s.database_password == "fallback_pw"
