import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dateutil.parser import parse

from app.db.session import get_db, AsyncSessionLocal
from app.models.participant import Participant, ConsentRecord, ConsentStatus, CohortStatus
from app.services.redcap_client import get_redcap_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sync", tags=["Sync"])

LAST_SYNC_STATUS = {"participants": None, "surveys": None}


def parse_date_safe(date_str: str):
    """Safely parse a date string into a python date object."""
    if not date_str:
        return None
    try:
        return parse(date_str).date()
    except Exception:
        return None


async def sync_participants(db: AsyncSession) -> dict:
    """
    Fetch participants from REDCap and upsert into the neps_core registry.
    Then fetch and upsert corresponding consent records.
    """
    client = get_redcap_client()
    participants = await client.get_participants()

    stats = {
        "created": 0,
        "updated": 0,
        "errors": 0,
        "synced_at": datetime.utcnow().isoformat()
    }

    for p_data in participants:
        try:
            record_id = p_data.get("record_id") or p_data.get("participant_id") 
            if not record_id:
                continue

            # Check if participant already exists
            stmt = select(Participant).where(Participant.record_id == record_id)
            result = await db.execute(stmt)
            participant = result.scalars().first()

            is_new = False
            if not participant:
                participant = Participant(record_id=record_id)
                db.add(participant)
                is_new = True

            # Safely apply REDCap data
            participant.redcap_event_name = p_data.get("redcap_event_name")
            participant.country = p_data.get("country", "Unknown")  # required field
            participant.site = p_data.get("site", "Unknown")        # required field
            participant.school = p_data.get("school")
            
            age_raw = p_data.get("age")
            participant.age = int(age_raw) if age_raw is not None and str(age_raw).isdigit() else None
            
            participant.date_of_birth = parse_date_safe(p_data.get("date_of_birth"))
            participant.gender = p_data.get("gender")
            
            # Always cast grade_level to str
            grade_level = p_data.get("grade_level")
            participant.grade_level = str(grade_level) if grade_level is not None else None
            
            participant.enrollment_date = parse_date_safe(p_data.get("enrollment_date"))
            
            try:
                participant.cohort_status = CohortStatus(str(p_data.get("cohort_status", "active")).lower())
            except ValueError:
                pass
                
            participant.phone_contact = p_data.get("phone_contact")
            
            try:
                participant.consent_status = ConsentStatus(str(p_data.get("consent_status", "pending")).lower())
            except ValueError:
                pass
                
            participant.redcap_data_access_group = p_data.get("redcap_data_access_group")

            # Flush to get the participant ID assigned for linking the consent record
            await db.flush()

            # Fetch and upsert Consent Record
            consent_data = await client.get_consent_status(record_id)
            if consent_data:
                stmt_consent = select(ConsentRecord).where(ConsentRecord.record_id == record_id)
                res_consent = await db.execute(stmt_consent)
                consent_record = res_consent.scalars().first()

                if not consent_record:
                    consent_record = ConsentRecord(
                        participant_id=participant.id,
                        record_id=record_id
                    )
                    db.add(consent_record)

                consent_record.consent_date = parse_date_safe(consent_data.get("consent_date"))
                consent_record.consent_version = consent_data.get("consent_version")
                
                try:
                    consent_record.consent_status = ConsentStatus(str(consent_data.get("consent_status", "pending")).lower())
                except ValueError:
                    pass

                consent_record.guardian_consent = consent_data.get("guardian_consent")
                consent_record.assent_status = consent_data.get("assent_status")
                consent_record.consent_withdrawn = str(consent_data.get("consent_withdrawn", "0"))
                consent_record.withdrawal_reason = consent_data.get("withdrawal_reason")
                consent_record.re_consent_required = str(consent_data.get("re_consent_required", "0"))
                consent_record.re_consent_date = parse_date_safe(consent_data.get("re_consent_date"))

            if is_new:
                stats["created"] += 1
            else:
                stats["updated"] += 1

        except Exception as e:
            logger.error(f"Failed syncing participant {record_id or 'Unknown'}: {e}")
            stats["errors"] += 1

    # Single commit for all upserts
    await db.commit()
    
    global LAST_SYNC_STATUS
    LAST_SYNC_STATUS["participants"] = stats
    
    return stats


async def scheduled_sync():
    """Cron job target to execute sync within its own fresh database session."""
    try:
        async with AsyncSessionLocal() as session:
            await sync_participants(session)
    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")


@router.post("/participants")
async def manual_sync_participants(db: AsyncSession = Depends(get_db)):
    """Trigger the participants sync manually."""
    return await sync_participants(db)


@router.get("/status")
async def get_sync_status():
    """Get the result of the last sync operation."""
    return LAST_SYNC_STATUS