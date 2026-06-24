"""
tests/test_redcap.py — Tests for the REDCap proxy router using the embedded mock.

All tests run with REDCAP_MOCK_ENABLED=true (set in conftest.py),
so no external HTTP calls are made.
"""

import pytest


# ── /api/redcap/health ────────────────────────────────────────────────────────

def test_redcap_health_returns_200(client):
    response = client.get("/api/redcap/health")
    assert response.status_code == 200


def test_redcap_health_has_status(client):
    data = client.get("/api/redcap/health").json()
    assert "status" in data
    assert data["status"] == "connected"


def test_redcap_health_mode_is_mock(client):
    data = client.get("/api/redcap/health").json()
    assert "mock" in data.get("mode", "").lower()


# ── /api/redcap/participants ──────────────────────────────────────────────────

def test_get_participants_returns_200(client):
    response = client.get("/api/redcap/participants")
    assert response.status_code == 200


def test_get_participants_response_structure(client):
    data = client.get("/api/redcap/participants").json()
    assert "data" in data
    assert "total" in data
    assert "filtered" in data
    assert isinstance(data["data"], list)


def test_get_participants_mode_is_mock(client):
    data = client.get("/api/redcap/participants").json()
    assert data.get("mode") == "mock"


def test_get_participants_limit_param(client):
    """?limit=2 should return at most 2 participants."""
    data = client.get("/api/redcap/participants?limit=2").json()
    assert len(data["data"]) <= 2


def test_get_participants_country_filter(client):
    """Country filter should not raise an error."""
    response = client.get("/api/redcap/participants?country=Ghana")
    assert response.status_code == 200


# ── /api/redcap/stats ─────────────────────────────────────────────────────────

def test_get_stats_returns_200(client):
    response = client.get("/api/redcap/stats")
    assert response.status_code == 200


# ── /api/redcap/screenings/distress ──────────────────────────────────────────

def test_get_distress_screenings_returns_200(client):
    response = client.get("/api/redcap/screenings/distress")
    assert response.status_code == 200


def test_get_distress_screenings_structure(client):
    data = client.get("/api/redcap/screenings/distress").json()
    assert "screenings" in data
    assert "count" in data
    assert "high_risk_count" in data
    assert isinstance(data["screenings"], list)


# ── /api/redcap/export/metadata ──────────────────────────────────────────────

def test_export_metadata_returns_200(client):
    response = client.get("/api/redcap/export/metadata")
    assert response.status_code == 200


# ── /api/redcap/participants/{id} — 404 for unknown id ───────────────────────

def test_get_unknown_participant_returns_404(client):
    response = client.get("/api/redcap/participants/DOES_NOT_EXIST_9999")
    assert response.status_code == 404
