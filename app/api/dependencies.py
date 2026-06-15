from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.participant import ConsentRecord, Participant, ConsentStatus


async def require_consent(
    record_id: str,
    db: AsyncSession = Depends(get_db)
) -> ConsentRecord:
    """
    FastAPI dependency to enforce consent status for a participant.
    Raises HTTPException if consent is not found, not given, or withdrawn.
    """
    stmt = select(ConsentRecord).filter(ConsentRecord.record_id == record_id)
    result = await db.execute(stmt)
    consent_record = result.scalar_one_or_none()

    if not consent_record:
        # According to instructions, this should be "Participant not found"
        # but it refers to a ConsentRecord search. Clarifying detail.
        raise HTTPException(status_code=404, detail="Participant not found")

    if consent_record.consent_status != ConsentStatus.CONSENTED:
        raise HTTPException(status_code=403, detail="Participant has not provided consent. Workflow blocked.")

    if consent_record.consent_withdrawn == "1":
        raise HTTPException(status_code=403, detail="Consent has been withdrawn for this participant.")

    return consent_record


async def get_participant_or_404(
    record_id: str,
    db: AsyncSession = Depends(get_db)
) -> Participant:
    """
    FastAPI dependency to fetch a Participant by record_id or raise 404.
    """
    stmt = select(Participant).filter(Participant.record_id == record_id)
    result = await db.execute(stmt)
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    return participant
