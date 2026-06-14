"""
NEPS Digital — REDCap API Router
================================
FastAPI endpoints that proxy REDCap data.
All calls to RedCapClient are awaited because the client is now async.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.redcap_client import get_redcap_client
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/redcap", tags=["REDCap"])


@router.get("/health")
async def redcap_health():
    """Check REDCap connectivity."""
    client = get_redcap_client()
    return {
        "status": "connected",
        "mode": "mock (embedded)" if client.use_mock else f"external ({settings.REDCAP_API_URL})",
        "note": "Replace with real REDCap in production.",
    }


@router.get("/participants")
async def get_participants(
    country: Optional[str] = None,
    site: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
):
    """Get participant registry with optional filtering."""
    client = get_redcap_client()
    participants = await client.get_participants(country=country, site=site, status=status)
    return {
        "data": participants[:limit],
        "total": len(participants),
        "filtered": len(participants[:limit]),
        "mode": "mock" if client.use_mock else "external",
    }


@router.get("/participants/{record_id}")
async def get_participant(record_id: str):
    """Get a single participant by record ID."""
    client = get_redcap_client()
    participant = await client.get_participant(record_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@router.get("/participants/{record_id}/surveys")
async def get_participant_surveys(
    record_id: str,
    instrument: Optional[str] = None,
    event: Optional[str] = None,
):
    """Get all survey responses for a participant."""
    client = get_redcap_client()
    responses = await client.get_survey_responses(
        record_id=record_id, instrument=instrument, event=event
    )
    return {"record_id": record_id, "responses": responses, "count": len(responses)}


@router.get("/participants/{record_id}/consent")
async def get_consent_status(record_id: str):
    """Get consent and assent status for a participant."""
    client = get_redcap_client()
    consent = await client.get_consent_status(record_id)
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")
    return consent


@router.get("/screenings/distress")
async def get_distress_screenings(status: Optional[str] = None):
    """Get distress and safeguarding screenings."""
    client = get_redcap_client()
    screenings = await client.get_distress_screenings(status=status)
    return {
        "screenings": screenings,
        "count": len(screenings),
        "high_risk_count": len(
            [s for s in screenings if s.get("severity") in ["high", "critical"]]
        ),
    }


@router.post("/referrals")
async def create_referral(record_id: str, destination: str, notes: str = ""):
    """Create a safeguarding referral."""
    client = get_redcap_client()
    referral = await client.create_referral(record_id, destination, notes)
    return referral


@router.get("/wp6/sessions/{record_id}")
async def get_wp6_sessions(record_id: str):
    """Get WP6 intervention sessions for a participant."""
    client = get_redcap_client()
    sessions = await client.get_wp6_sessions(record_id)
    attendance_rate = (
        len([s for s in sessions if s.get("attendance") == "Present"]) / len(sessions) * 100
        if sessions
        else 0
    )
    return {
        "record_id": record_id,
        "sessions": sessions,
        "total_sessions": len(sessions),
        "attendance_rate": attendance_rate,
    }


@router.get("/nlp/responses")
async def get_nlp_responses(
    response_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
):
    """Get qualitative text responses for NLP processing."""
    client = get_redcap_client()
    responses = await client.get_nlp_responses(
        response_type=response_type, sentiment=sentiment
    )
    return {
        "data": responses[:limit],
        "count": len(responses),
        "mode": "mock" if client.use_mock else "external",
    }


@router.get("/participants/{record_id}/nlp-responses")
async def get_participant_nlp_responses(record_id: str):
    """Get NLP responses for a specific participant."""
    client = get_redcap_client()
    participant = await client.get_participant(record_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    responses = await client.get_nlp_responses(record_id=record_id)
    return {"record_id": record_id, "responses": responses, "count": len(responses)}


@router.get("/export/records")
async def export_records(
    format: str = Query("json", pattern="^(json|csv)$"),
    fields: Optional[List[str]] = Query(None),
    events: Optional[List[str]] = Query(None),
):
    """Export records in REDCap format."""
    client = get_redcap_client()
    return await client.export_records(format=format, fields=fields, events=events)


@router.get("/export/metadata")
async def export_metadata():
    """Export REDCap project metadata."""
    client = get_redcap_client()
    return await client.export_metadata()


@router.get("/stats")
async def get_project_stats():
    """Get overall project statistics."""
    client = get_redcap_client()
    return await client.get_stats()