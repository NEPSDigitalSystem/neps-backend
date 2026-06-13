
"""
NEPS Digital — Mock REDCap API Router
======================================
FastAPI endpoints that simulate REDCap API responses.
Mount this in development mode, swap to real REDCap client in production.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from app.services.redcap_mock import RedCapMockClient

router = APIRouter(prefix="/api/redcap", tags=["REDCap Mock"])

# Initialize mock client (singleton)
_mock_client = None


def get_mock_client() -> RedCapMockClient:
    global _mock_client
    if _mock_client is None:
        _mock_client = RedCapMockClient()
    return _mock_client


@router.get("/health")
async def redcap_health():
    """Check mock REDCap connectivity."""
    return {
        "status": "connected (mock)",
        "mode": "development",
        "note": "Using mock data. Replace with real REDCap in production."
    }


@router.get("/participants")
async def get_participants(
    country: Optional[str] = None,
    site: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Get participant registry with filtering."""
    participants = client.get_participants(country=country, site=site, status=status)
    return {
        "data": participants[:limit],
        "total": len(participants),
        "filtered": len(participants[:limit]),
        "mode": "mock"
    }


@router.get("/participants/{record_id}")
async def get_participant(
    record_id: str,
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Get single participant by record ID."""
    participant = client.get_participant(record_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@router.get("/participants/{record_id}/surveys")
async def get_participant_surveys(
    record_id: str,
    instrument: Optional[str] = None,
    event: Optional[str] = None,
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Get all survey responses for a participant."""
    responses = client.get_survey_responses(record_id=record_id,
                                            instrument=instrument,
                                            event=event)
    return {
        "record_id": record_id,
        "responses": responses,
        "count": len(responses)
    }


@router.get("/participants/{record_id}/consent")
async def get_consent_status(
    record_id: str,
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Get consent/assent status."""
    consent = client.get_consent_status(record_id)
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")
    return consent


@router.get("/screenings/distress")
async def get_distress_screenings(
    status: Optional[str] = None,
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Get distress/safeguarding screenings."""
    screenings = client.get_distress_screenings(status=status)
    return {
        "screenings": screenings,
        "count": len(screenings),
        "high_risk_count": len([s for s in screenings if s["severity"] in ["high", "critical"]])
    }


@router.post("/referrals")
async def create_referral(
    record_id: str, 
    destination: str, 
    notes: str = "",
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Create a safeguarding referral."""
    referral = client.create_referral(record_id, destination, notes)
    return referral


@router.get("/wp6/sessions/{record_id}")
async def get_wp6_sessions(
    record_id: str,
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Get WP6 intervention sessions."""
    sessions = client.get_wp6_sessions(record_id)
    return {
        "record_id": record_id,
        "sessions": sessions,
        "total_sessions": len(sessions),
        "attendance_rate": len([s for s in sessions if s["attendance"] == "Present"]) / len(sessions) * 100 if sessions else 0
    }


@router.get("/export/records")
async def export_records(
    format: str = Query("json", regex="^(json|csv)$"),
    fields: Optional[List[str]] = Query(None),
    events: Optional[List[str]] = Query(None),
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Export records in REDCap format."""
    return client.export_records(format=format, fields=fields, events=events)


@router.get("/export/metadata")
async def export_metadata(
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Export REDCap project metadata."""
    return client.export_metadata()


@router.get("/stats")
async def get_project_stats(
    client: RedCapMockClient = Depends(get_mock_client)
):
    """Get project statistics."""
    return client.get_stats()
