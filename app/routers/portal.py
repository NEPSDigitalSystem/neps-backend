from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.longitudinal import (
    DistressScreening,
    Referral,
    ReferralStatus,
    RiskLevel,
    SurveyResponse,
    SurveyStatus,
    WP6Session,
)
from app.models.participant import ConsentStatus, CohortStatus, Participant

router = APIRouter(prefix="/api/portal", tags=["Portal"])


@router.get("/stats")
async def get_portal_stats(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    total_participants = (
        await db.execute(select(func.count(Participant.id)))
    ).scalar_one()

    active_participants = (
        await db.execute(
            select(func.count(Participant.id)).where(
                Participant.cohort_status == CohortStatus.ACTIVE.value,
                Participant.consent_status == ConsentStatus.CONSENTED.value,
            )
        )
    ).scalar_one()

    consent_result = await db.execute(
        select(Participant.consent_status, func.count(Participant.id)).group_by(Participant.consent_status)
    )
    consent_breakdown = {status.value: 0 for status in ConsentStatus}
    for status, count in consent_result.all():
        consent_breakdown[status.value if status else "unknown"] = count

    cohort_result = await db.execute(
        select(Participant.cohort_status, func.count(Participant.id)).group_by(Participant.cohort_status)
    )
    cohort_breakdown = {status.value: 0 for status in CohortStatus}
    for status, count in cohort_result.all():
        cohort_breakdown[status.value if status else "unknown"] = count

    total_screenings = (
        await db.execute(select(func.count(DistressScreening.id)))
    ).scalar_one()

    open_alerts = (
        await db.execute(
            select(func.count(DistressScreening.id)).where(
                DistressScreening.resolution_status == "open"
            )
        )
    ).scalar_one()

    high_severity_alerts = (
        await db.execute(
            select(func.count(DistressScreening.id)).where(
                DistressScreening.resolution_status == "open",
                DistressScreening.severity.in_(
                    [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
                ),
            )
        )
    ).scalar_one()

    total_wp6_sessions = (
        await db.execute(select(func.count(WP6Session.id)))
    ).scalar_one()

    open_referrals = (
        await db.execute(
            select(func.count(Referral.id)).where(
                Referral.status.in_(
                    [ReferralStatus.INITIATED.value, ReferralStatus.IN_PROGRESS.value]
                )
            )
        )
    ).scalar_one()

    total_surveys = (
        await db.execute(select(func.count(SurveyResponse.id)))
    ).scalar_one()

    return {
        "total_participants": total_participants,
        "active_participants": active_participants,
        "consent_breakdown": consent_breakdown,
        "cohort_breakdown": cohort_breakdown,
        "total_screenings": total_screenings,
        "open_alerts": open_alerts,
        "high_severity_alerts": high_severity_alerts,
        "total_wp6_sessions": total_wp6_sessions,
        "open_referrals": open_referrals,
        "total_surveys": total_surveys,
    }


@router.get("/participants")
async def list_participants(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    country: str | None = None,
    site: str | None = None,
    cohort_status: CohortStatus | None = None,
    consent_status: ConsentStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(func.count(Participant.id))
    if country:
        stmt = stmt.where(Participant.country.ilike(f"%{country}%"))
    if site:
        stmt = stmt.where(Participant.site.ilike(f"%{site}%"))
    if cohort_status:
        stmt = stmt.where(Participant.cohort_status == cohort_status.value)
    if consent_status:
        stmt = stmt.where(Participant.consent_status == consent_status.value)

    total = (await db.execute(stmt)).scalar_one()

    items_stmt = select(Participant)
    if country:
        items_stmt = items_stmt.where(Participant.country.ilike(f"%{country}%"))
    if site:
        items_stmt = items_stmt.where(Participant.site.ilike(f"%{site}%"))
    if cohort_status:
        items_stmt = items_stmt.where(Participant.cohort_status == cohort_status.value)
    if consent_status:
        items_stmt = items_stmt.where(Participant.consent_status == consent_status.value)

    items_stmt = (
        items_stmt.order_by(Participant.record_id.asc())
        .offset(offset)
        .limit(limit)
    )
    participants = (await db.execute(items_stmt)).scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(participant.id),
                "record_id": participant.record_id,
                "country": participant.country,
                "site": participant.site,
                "school": participant.school,
                "age": participant.age,
                "gender": participant.gender,
                "grade_level": participant.grade_level,
                "cohort_status": participant.cohort_status.value if participant.cohort_status else None,
                "consent_status": participant.consent_status.value if participant.consent_status else None,
                "enrollment_date": participant.enrollment_date.isoformat() if participant.enrollment_date else None,
                "created_at": participant.created_at.isoformat() if participant.created_at else None,
            }
            for participant in participants
        ],
    }


@router.get("/participants/breakdown/by-country")
async def participants_by_country(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(
                Participant.country,
                func.count(Participant.id).label("total"),
            )
            .group_by(Participant.country)
            .order_by(func.count(Participant.id).desc())
        )
    ).all()

    return [
        {"country": row.country, "total": row.total}
        for row in rows
    ]


@router.get("/participants/breakdown/by-site")
async def participants_by_site(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(
                Participant.country,
                Participant.site,
                func.count(Participant.id).label("total"),
            )
            .group_by(Participant.country, Participant.site)
            .order_by(Participant.country.asc(), func.count(Participant.id).desc())
        )
    ).all()

    return [
        {"country": row.country, "site": row.site, "total": row.total}
        for row in rows
    ]


@router.get("/participants/{record_id}")
async def get_participant_detail(
    record_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = (
        select(Participant)
        .options(
            selectinload(Participant.consents),
            selectinload(Participant.surveys),
            selectinload(Participant.distress_screenings),
            selectinload(Participant.referrals),
            selectinload(Participant.wp6_sessions),
        )
        .where(Participant.record_id == record_id)
    )
    participant = (await db.execute(stmt)).scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    consent = participant.consents[0] if participant.consents else None
    latest_survey = (
        max(participant.surveys, key=lambda survey: survey.month if survey.month is not None else -1)
        if participant.surveys
        else None
    )

    return {
        "id": str(participant.id),
        "record_id": participant.record_id,
        "country": participant.country,
        "site": participant.site,
        "school": participant.school,
        "age": participant.age,
        "date_of_birth": participant.date_of_birth.isoformat() if participant.date_of_birth else None,
        "gender": participant.gender,
        "grade_level": participant.grade_level,
        "cohort_status": participant.cohort_status.value if participant.cohort_status else None,
        "consent_status": participant.consent_status.value if participant.consent_status else None,
        "enrollment_date": participant.enrollment_date.isoformat() if participant.enrollment_date else None,
        "redcap_data_access_group": participant.redcap_data_access_group,
        "consent": {
            "consent_date": consent.consent_date.isoformat() if consent and consent.consent_date else None,
            "consent_version": consent.consent_version if consent else None,
            "guardian_consent": consent.guardian_consent if consent else None,
            "assent_status": consent.assent_status if consent else None,
            "consent_withdrawn": consent.consent_withdrawn if consent else None,
        } if consent else None,
        "latest_survey": {
            "month": latest_survey.month,
            "survey_date": latest_survey.survey_date.isoformat() if latest_survey and latest_survey.survey_date else None,
            "perceived_stress_score": latest_survey.perceived_stress_score if latest_survey else None,
            "anxiety_score": latest_survey.anxiety_score if latest_survey else None,
            "depression_score": latest_survey.depression_score if latest_survey else None,
            "risk_flag": latest_survey.risk_flag if latest_survey else None,
            "suicidality_screening": latest_survey.suicidality_screening if latest_survey else None,
            "requires_follow_up": latest_survey.requires_follow_up if latest_survey else None,
        } if latest_survey else None,
        "open_alerts": [
            {
                "id": str(alert.id),
                "severity": alert.severity.value if alert.severity else None,
                "trigger_form": alert.trigger_form,
                "assigned_responder": alert.assigned_responder,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
            for alert in sorted(
                [
                    alert for alert in participant.distress_screenings
                    if alert.resolution_status == "open"
                ],
                key=lambda alert: alert.created_at or alert.id,
                reverse=True,
            )
        ],
        "survey_count": len(participant.surveys),
        "wp6_session_count": len(participant.wp6_sessions),
        "referral_count": len(participant.referrals),
        "created_at": participant.created_at.isoformat() if participant.created_at else None,
        "updated_at": participant.updated_at.isoformat() if participant.updated_at else None,
    }


@router.get("/distress/trends")
async def distress_trends(
    country: str | None = None,
    site: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = (
        select(
            SurveyResponse.month,
            func.round(func.avg(SurveyResponse.perceived_stress_score), 2).label("avg_stress"),
            func.round(func.avg(SurveyResponse.anxiety_score), 2).label("avg_anxiety"),
            func.round(func.avg(SurveyResponse.depression_score), 2).label("avg_depression"),
            func.count(SurveyResponse.id).label("n"),
        )
        .join(Participant, SurveyResponse.record_id == Participant.record_id)
        .where(SurveyResponse.month.is_not(None))
        .group_by(SurveyResponse.month)
        .order_by(SurveyResponse.month.asc())
    )
    if country:
        stmt = stmt.where(Participant.country.ilike(f"%{country}%"))
    if site:
        stmt = stmt.where(Participant.site.ilike(f"%{site}%"))

    rows = (await db.execute(stmt)).all()

    return [
        {
            "month": row.month,
            "avg_stress": round(float(row.avg_stress), 2) if row.avg_stress is not None else None,
            "avg_anxiety": round(float(row.avg_anxiety), 2) if row.avg_anxiety is not None else None,
            "avg_depression": round(float(row.avg_depression), 2) if row.avg_depression is not None else None,
            "n": row.n,
        }
        for row in rows
    ]


@router.get("/distress/alerts")
async def distress_alerts(
    status: str = "open",
    severity: RiskLevel | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = (
        select(func.count(DistressScreening.id))
        .join(Participant, DistressScreening.record_id == Participant.record_id)
        .where(DistressScreening.resolution_status == status)
    )
    if severity:
        stmt = stmt.where(DistressScreening.severity == severity.value)

    total = (await db.execute(stmt)).scalar_one()

    items_stmt = (
        select(
            DistressScreening.id,
            DistressScreening.record_id,
            Participant.country,
            Participant.site,
            DistressScreening.distress_score,
            DistressScreening.severity,
            DistressScreening.suicidality_flag,
            DistressScreening.trigger_form,
            DistressScreening.resolution_status,
            DistressScreening.assigned_responder,
            DistressScreening.welfare_check_due,
            DistressScreening.created_at,
        )
        .join(Participant, DistressScreening.record_id == Participant.record_id)
        .where(DistressScreening.resolution_status == status)
        .order_by(DistressScreening.created_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )
    if severity:
        items_stmt = items_stmt.where(DistressScreening.severity == severity.value)

    rows = (await db.execute(items_stmt)).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(row.id),
                "record_id": row.record_id,
                "country": row.country,
                "site": row.site,
                "distress_score": row.distress_score,
                "severity": row.severity.value if row.severity else None,
                "suicidality_flag": row.suicidality_flag,
                "trigger_form": row.trigger_form,
                "resolution_status": row.resolution_status,
                "assigned_responder": row.assigned_responder,
                "welfare_check_due": row.welfare_check_due.isoformat() if row.welfare_check_due else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


@router.get("/wp6/sessions")
async def wp6_sessions(
    record_id: str | None = None,
    country: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = (
        select(func.count(WP6Session.id))
        .join(Participant, WP6Session.record_id == Participant.record_id)
    )
    if record_id:
        stmt = stmt.where(WP6Session.record_id == record_id)
    if country:
        stmt = stmt.where(Participant.country.ilike(f"%{country}%"))

    total = (await db.execute(stmt)).scalar_one()

    items_stmt = (
        select(
            WP6Session.id,
            WP6Session.record_id,
            Participant.country,
            Participant.site,
            WP6Session.session_number,
            WP6Session.session_date,
            WP6Session.attendance,
            WP6Session.engagement_level,
            WP6Session.fidelity_score,
            WP6Session.satisfaction_score,
            WP6Session.distress_pre,
            WP6Session.distress_post,
        )
        .join(Participant, WP6Session.record_id == Participant.record_id)
        .order_by(WP6Session.session_date.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )
    if record_id:
        items_stmt = items_stmt.where(WP6Session.record_id == record_id)
    if country:
        items_stmt = items_stmt.where(Participant.country.ilike(f"%{country}%"))

    rows = (await db.execute(items_stmt)).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(row.id),
                "record_id": row.record_id,
                "country": row.country,
                "site": row.site,
                "session_number": row.session_number,
                "session_date": row.session_date.isoformat() if row.session_date else None,
                "attendance": row.attendance,
                "engagement_level": row.engagement_level,
                "fidelity_score": row.fidelity_score,
                "satisfaction_score": row.satisfaction_score,
                "distress_pre": row.distress_pre,
                "distress_post": row.distress_post,
            }
            for row in rows
        ],
    }


@router.get("/wp6/summary")
async def wp6_summary(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    row = (
        await db.execute(
            select(
                func.count(WP6Session.id).label("total_sessions"),
                func.round(func.avg(WP6Session.engagement_level), 2).label("avg_engagement"),
                func.round(func.avg(WP6Session.fidelity_score), 2).label("avg_fidelity"),
                func.round(func.avg(WP6Session.satisfaction_score), 2).label("avg_satisfaction"),
                func.round(func.avg(WP6Session.distress_pre), 2).label("avg_distress_pre"),
                func.round(func.avg(WP6Session.distress_post), 2).label("avg_distress_post"),
                func.round(func.avg(WP6Session.distress_pre - WP6Session.distress_post), 2).label("avg_distress_reduction"),
            )
        )
    ).one()

    return {
        "total_sessions": row.total_sessions,
        "avg_engagement": round(float(row.avg_engagement), 2) if row.avg_engagement is not None else None,
        "avg_fidelity": round(float(row.avg_fidelity), 2) if row.avg_fidelity is not None else None,
        "avg_satisfaction": round(float(row.avg_satisfaction), 2) if row.avg_satisfaction is not None else None,
        "avg_distress_pre": round(float(row.avg_distress_pre), 2) if row.avg_distress_pre is not None else None,
        "avg_distress_post": round(float(row.avg_distress_post), 2) if row.avg_distress_post is not None else None,
        "avg_distress_reduction": round(float(row.avg_distress_reduction), 2) if row.avg_distress_reduction is not None else None,
    }


@router.get("/surveys")
async def list_surveys(
    record_id: str | None = None,
    month: int | None = None,
    risk_flag: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(func.count(SurveyResponse.id))
    if record_id:
        stmt = stmt.where(SurveyResponse.record_id == record_id)
    if month is not None:
        stmt = stmt.where(SurveyResponse.month == month)
    if risk_flag:
        stmt = stmt.where(SurveyResponse.risk_flag == risk_flag)

    total = (await db.execute(stmt)).scalar_one()

    items_stmt = (
        select(
            SurveyResponse.id,
            SurveyResponse.record_id,
            SurveyResponse.month,
            SurveyResponse.survey_date,
            SurveyResponse.perceived_stress_score,
            SurveyResponse.anxiety_score,
            SurveyResponse.depression_score,
            SurveyResponse.mood_status,
            SurveyResponse.sleep_quality,
            SurveyResponse.daily_functioning,
            SurveyResponse.social_isolation_score,
            SurveyResponse.resilience_score,
            SurveyResponse.suicidality_screening,
            SurveyResponse.risk_flag,
            SurveyResponse.requires_follow_up,
        )
        .order_by(SurveyResponse.survey_date.desc().nullslast(), SurveyResponse.created_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )
    if record_id:
        items_stmt = items_stmt.where(SurveyResponse.record_id == record_id)
    if month is not None:
        items_stmt = items_stmt.where(SurveyResponse.month == month)
    if risk_flag:
        items_stmt = items_stmt.where(SurveyResponse.risk_flag == risk_flag)

    rows = (await db.execute(items_stmt)).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(row.id),
                "record_id": row.record_id,
                "month": row.month,
                "survey_date": row.survey_date.isoformat() if row.survey_date else None,
                "perceived_stress_score": row.perceived_stress_score,
                "anxiety_score": row.anxiety_score,
                "depression_score": row.depression_score,
                "mood_status": row.mood_status,
                "sleep_quality": row.sleep_quality,
                "daily_functioning": row.daily_functioning,
                "social_isolation_score": row.social_isolation_score,
                "resilience_score": row.resilience_score,
                "suicidality_screening": row.suicidality_screening,
                "risk_flag": row.risk_flag,
                "requires_follow_up": row.requires_follow_up,
            }
            for row in rows
        ],
    }


@router.get("/surveys/{record_id}/longitudinal")
async def participant_longitudinal_surveys(
    record_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    exists = (
        await db.execute(select(Participant.id).where(Participant.record_id == record_id))
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="Participant not found")

    rows = (
        await db.execute(
            select(
                SurveyResponse.month,
                SurveyResponse.survey_date,
                SurveyResponse.perceived_stress_score,
                SurveyResponse.anxiety_score,
                SurveyResponse.depression_score,
                SurveyResponse.resilience_score,
                SurveyResponse.social_support,
                SurveyResponse.daily_functioning,
                SurveyResponse.self_esteem_score,
                SurveyResponse.loneliness_score,
                SurveyResponse.risk_flag,
                SurveyResponse.suicidality_screening,
            )
            .where(SurveyResponse.record_id == record_id)
            .order_by(SurveyResponse.month.asc().nullslast(), SurveyResponse.survey_date.asc().nullslast())
        )
    ).all()

    return {
        "record_id": record_id,
        "wave_count": len(rows),
        "waves": [
            {
                "month": row.month,
                "survey_date": row.survey_date.isoformat() if row.survey_date else None,
                "perceived_stress_score": row.perceived_stress_score,
                "anxiety_score": row.anxiety_score,
                "depression_score": row.depression_score,
                "resilience_score": row.resilience_score,
                "social_support": row.social_support,
                "daily_functioning": row.daily_functioning,
                "self_esteem_score": row.self_esteem_score,
                "loneliness_score": row.loneliness_score,
                "risk_flag": row.risk_flag,
                "suicidality_screening": row.suicidality_screening,
            }
            for row in rows
        ],
    }


@router.get("/referrals")
async def list_referrals(
    record_id: str | None = None,
    status: ReferralStatus | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(func.count(Referral.id))
    if record_id:
        stmt = stmt.where(Referral.record_id == record_id)
    if status:
        stmt = stmt.where(Referral.status == status.value)

    total = (await db.execute(stmt)).scalar_one()

    items_stmt = (
        select(
            Referral.id,
            Referral.referral_id,
            Referral.record_id,
            Referral.initiation_date,
            Referral.destination,
            Referral.status,
            Referral.notes,
            Referral.follow_up_date,
        )
        .order_by(Referral.initiation_date.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )
    if record_id:
        items_stmt = items_stmt.where(Referral.record_id == record_id)
    if status:
        items_stmt = items_stmt.where(Referral.status == status.value)

    rows = (await db.execute(items_stmt)).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(row.id),
                "referral_id": row.referral_id,
                "record_id": row.record_id,
                "initiation_date": row.initiation_date.isoformat() if row.initiation_date else None,
                "destination": row.destination,
                "status": row.status.value if row.status else None,
                "notes": row.notes,
                "follow_up_date": row.follow_up_date.isoformat() if row.follow_up_date else None,
            }
            for row in rows
        ],
    }
