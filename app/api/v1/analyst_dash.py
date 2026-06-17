from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.longitudinal import DistressScreening, SurveyResponse, SurveyStatus, WP6Session
from app.models.participant import CohortStatus, ConsentStatus, Participant

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/cohort-overview")
async def cohort_overview(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    by_country_rows = (
        await db.execute(
            select(
                Participant.country,
                func.count(Participant.id).label("total"),
                func.coalesce(
                    func.sum(case((Participant.cohort_status == CohortStatus.ACTIVE.value, 1), else_=0)),
                    0,
                ).label("active"),
                func.coalesce(
                    func.sum(case((Participant.consent_status == ConsentStatus.CONSENTED.value, 1), else_=0)),
                    0,
                ).label("consented"),
                func.coalesce(
                    func.sum(case((Participant.cohort_status == CohortStatus.WITHDRAWN.value, 1), else_=0)),
                    0,
                ).label("withdrawn"),
            )
            .group_by(Participant.country)
            .order_by(Participant.country.asc())
        )
    ).all()

    by_site_rows = (
        await db.execute(
            select(
                Participant.country,
                Participant.site,
                func.count(Participant.id).label("total"),
                func.coalesce(
                    func.sum(case((Participant.cohort_status == CohortStatus.ACTIVE.value, 1), else_=0)),
                    0,
                ).label("active"),
            )
            .group_by(Participant.country, Participant.site)
            .order_by(Participant.country.asc(), Participant.site.asc())
        )
    ).all()

    return {
        "by_country": [
            {
                "country": row.country,
                "total": row.total,
                "active": row.active,
                "consented": row.consented,
                "withdrawn": row.withdrawn,
            }
            for row in by_country_rows
        ],
        "by_site": [
            {
                "country": row.country,
                "site": row.site,
                "total": row.total,
                "active": row.active,
            }
            for row in by_site_rows
        ],
    }


@router.get("/survey-completion")
async def survey_completion(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(
                SurveyResponse.month,
                func.count(SurveyResponse.id).label("total_submitted"),
                func.coalesce(
                    func.sum(case((SurveyResponse.survey_complete == SurveyStatus.COMPLETE.value, 1), else_=0)),
                    0,
                ).label("complete"),
                func.coalesce(
                    func.sum(case((SurveyResponse.survey_complete == SurveyStatus.INCOMPLETE.value, 1), else_=0)),
                    0,
                ).label("incomplete"),
                case(
                    (
                        func.count(SurveyResponse.id) > 0,
                        func.round(
                            func.coalesce(
                                func.sum(case((SurveyResponse.survey_complete == SurveyStatus.COMPLETE.value, 1), else_=0)),
                                0,
                            ) * 100.0 / func.count(SurveyResponse.id),
                            1,
                        ),
                    ),
                    else_=None,
                ).label("completion_rate_pct"),
            )
            .group_by(SurveyResponse.month)
            .order_by(SurveyResponse.month.asc())
        )
    ).all()

    return [
        {
            "month": row.month,
            "total_submitted": row.total_submitted,
            "complete": row.complete,
            "incomplete": row.incomplete,
            "completion_rate_pct": round(float(row.completion_rate_pct), 1) if row.completion_rate_pct is not None else None,
        }
        for row in rows
    ]


@router.get("/distress-summary")
async def distress_summary(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(case((DistressScreening.severity == "low", 1), else_=0)), 0).label("low"),
                func.coalesce(func.sum(case((DistressScreening.severity == "moderate", 1), else_=0)), 0).label("moderate"),
                func.coalesce(func.sum(case((DistressScreening.severity == "high", 1), else_=0)), 0).label("high"),
                func.coalesce(func.sum(case((DistressScreening.severity == "critical", 1), else_=0)), 0).label("critical"),
                func.coalesce(func.sum(case((DistressScreening.resolution_status == "open", 1), else_=0)), 0).label("open"),
                func.coalesce(func.sum(case((DistressScreening.resolution_status == "resolved", 1), else_=0)), 0).label("resolved"),
                func.round(func.avg(DistressScreening.distress_score), 1).label("avg_distress_score"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                DistressScreening.suicidality_flag.is_not(None)
                                & (DistressScreening.suicidality_flag != "0")
                                & (DistressScreening.suicidality_flag != "No"),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("suicidality_flagged"),
            )
        )
    ).one()

    return {
        "by_severity": {
            "low": row.low,
            "moderate": row.moderate,
            "high": row.high,
            "critical": row.critical,
        },
        "by_resolution": {
            "open": row.open,
            "resolved": row.resolved,
        },
        "avg_distress_score": round(float(row.avg_distress_score), 1) if row.avg_distress_score is not None else None,
        "suicidality_flagged": row.suicidality_flagged,
    }


@router.get("/wp6-fidelity")
async def wp6_fidelity(
    country: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = (
        select(
            WP6Session.session_number,
            func.round(func.avg(WP6Session.fidelity_score), 2).label("avg_fidelity"),
            func.round(func.avg(WP6Session.engagement_level), 2).label("avg_engagement"),
            func.round(func.avg(WP6Session.satisfaction_score), 2).label("avg_satisfaction"),
            func.count(WP6Session.id).label("attendance_count"),
            func.round(func.avg(WP6Session.distress_pre - WP6Session.distress_post), 2).label("avg_distress_reduction"),
        )
        .group_by(WP6Session.session_number)
        .order_by(WP6Session.session_number.asc())
    )
    if country:
        stmt = (
            stmt.join(Participant, WP6Session.record_id == Participant.record_id)
            .where(Participant.country.ilike(f"%{country}%"))
        )

    rows = (await db.execute(stmt)).all()

    return [
        {
            "session_number": row.session_number,
            "avg_fidelity": round(float(row.avg_fidelity), 2) if row.avg_fidelity is not None else None,
            "avg_engagement": round(float(row.avg_engagement), 2) if row.avg_engagement is not None else None,
            "avg_satisfaction": round(float(row.avg_satisfaction), 2) if row.avg_satisfaction is not None else None,
            "attendance_count": row.attendance_count,
            "avg_distress_reduction": round(float(row.avg_distress_reduction), 2) if row.avg_distress_reduction is not None else None,
        }
        for row in rows
    ]


@router.get("/risk-distribution")
async def risk_distribution(
    month: int | None = None,
    country: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = (
        select(
            func.count(SurveyResponse.id).label("n"),
            func.round(func.avg(SurveyResponse.perceived_stress_score), 2).label("avg_stress"),
            func.round(func.avg(SurveyResponse.anxiety_score), 2).label("avg_anxiety"),
            func.round(func.avg(SurveyResponse.depression_score), 2).label("avg_depression"),
            func.round(func.avg(SurveyResponse.resilience_score), 2).label("avg_resilience"),
            case(
                (
                    func.count(SurveyResponse.id) > 0,
                    func.round(
                        func.coalesce(
                            func.sum(case((SurveyResponse.risk_flag == "HIGH", 1), else_=0)),
                            0,
                        ) * 100.0 / func.count(SurveyResponse.id),
                        1,
                    ),
                ),
                else_=None,
            ).label("pct_high_risk"),
            case(
                (
                    func.count(SurveyResponse.id) > 0,
                    func.round(
                        func.coalesce(
                            func.sum(
                                case(
                                    (
                                        (SurveyResponse.requires_follow_up == "1")
                                        | (SurveyResponse.requires_follow_up == "Yes"),
                                        1,
                                    ),
                                    else_=0,
                                )
                            ),
                            0,
                        ) * 100.0 / func.count(SurveyResponse.id),
                        1,
                    ),
                ),
                else_=None,
            ).label("pct_requires_follow_up"),
        )
    )
    if month is not None:
        stmt = stmt.where(SurveyResponse.month == month)
    if country:
        stmt = (
            stmt.join(Participant, SurveyResponse.record_id == Participant.record_id)
            .where(Participant.country.ilike(f"%{country}%"))
        )

    row = (await db.execute(stmt)).one_or_none()

    return {
        "month": month,
        "n": row.n if row else 0,
        "avg_stress": round(float(row.avg_stress), 2) if row and row.avg_stress is not None else None,
        "avg_anxiety": round(float(row.avg_anxiety), 2) if row and row.avg_anxiety is not None else None,
        "avg_depression": round(float(row.avg_depression), 2) if row and row.avg_depression is not None else None,
        "avg_resilience": round(float(row.avg_resilience), 2) if row and row.avg_resilience is not None else None,
        "pct_high_risk": round(float(row.pct_high_risk), 1) if row and row.pct_high_risk is not None else None,
        "pct_requires_follow_up": round(float(row.pct_requires_follow_up), 1) if row and row.pct_requires_follow_up is not None else None,
    }
