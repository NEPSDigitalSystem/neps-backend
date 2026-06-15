from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any

from app.api.dependencies import get_db

router = APIRouter(prefix="/api/portal", tags=["Portal"])

@router.get("/stats")
async def get_portal_stats(db: AsyncSession = Depends(get_db)):
    """Get high-level statistics for the dashboard."""
    # Total participants
    participants_result = await db.execute(text("SELECT COUNT(*) FROM redcap.raw_redcap_demographics"))
    total_participants = participants_result.scalar() or 0

    # Total distress screenings
    distress_result = await db.execute(text("SELECT COUNT(*) FROM redcap.raw_redcap_distress_screening"))
    total_screenings = distress_result.scalar() or 0

    # Total WP6 sessions
    wp6_result = await db.execute(text("SELECT COUNT(*) FROM redcap.raw_redcap_wp6_session"))
    total_wp6 = wp6_result.scalar() or 0

    return {
        "total_participants": total_participants,
        "total_screenings": total_screenings,
        "total_wp6_sessions": total_wp6
    }

@router.get("/participants")
async def get_portal_participants(limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get a list of participants for the portal."""
    query = text("""
        SELECT 
            record_id, 
            age, 
            gender, 
            country, 
            site, 
            consent_status, 
            cohort_status 
        FROM redcap.raw_redcap_demographics
        ORDER BY record_id ASC
        LIMIT :limit
    """)
    result = await db.execute(query, {"limit": limit})
    participants = []
    for row in result.mappings():
        participants.append(dict(row))
    return participants
