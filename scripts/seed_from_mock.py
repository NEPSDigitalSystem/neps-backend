import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.models import (
    Participant,
    ConsentRecord,
    SurveyResponse,
    DistressScreening,
    Referral,
    WP6Session
)
from app.services.redcap_mock import RedCapMockClient


async def seed_database():
    print("🌱 Starting database seed...")
    
    # Initialize mock client
    client = RedCapMockClient()
    
    async with AsyncSessionLocal() as session:
        # ------------------------------
        # 1. Seed Participants
        # ------------------------------
        print("Seeding participants...")
        participants = client.get_participants()
        
        participant_map = {}  # record_id -> Participant object
        
        for p_data in participants:
            participant = Participant(
                record_id=p_data["record_id"],
                redcap_event_name=p_data.get("redcap_event_name"),
                country=p_data["country"],
                site=p_data["site"],
                school=p_data.get("school"),
                age=p_data.get("age"),
                date_of_birth=datetime.strptime(p_data["date_of_birth"], "%Y-%m-%d").date() if p_data.get("date_of_birth") else None,
                gender=p_data.get("gender"),
                grade_level=p_data.get("grade_level"),
                enrollment_date=datetime.strptime(p_data["enrollment_date"], "%Y-%m-%d").date() if p_data.get("enrollment_date") else None,
                cohort_status=p_data.get("cohort_status", "active"),
                phone_contact=p_data.get("phone_contact"),
                consent_status=p_data.get("consent_status", "pending"),
                redcap_data_access_group=p_data.get("redcap_data_access_group")
            )
            session.add(participant)
            participant_map[p_data["record_id"]] = participant
        
        await session.flush()  # Get the IDs
        
        # ------------------------------
        # 2. Seed Consent Records
        # ------------------------------
        print("Seeding consent records...")
        consent_records = []
        for p_data in participants:
            consent_data = client.get_consent_status(p_data["record_id"])
            if consent_data:
                consent_record = ConsentRecord(
                    participant_id=participant_map[p_data["record_id"]].id,
                    record_id=consent_data["record_id"],
                    consent_date=datetime.strptime(consent_data["consent_date"], "%Y-%m-%d").date() if consent_data.get("consent_date") else None,
                    consent_version=consent_data.get("consent_version", "v1.0"),
                    consent_status=consent_data.get("consent_status"),
                    guardian_consent=consent_data.get("guardian_consent"),
                    assent_status=consent_data.get("assent_status"),
                    consent_withdrawn=consent_data.get("consent_withdrawn", "0"),
                    withdrawal_reason=consent_data.get("withdrawal_reason"),
                    re_consent_required=consent_data.get("re_consent_required", "0"),
                    re_consent_date=datetime.strptime(consent_data["re_consent_date"], "%Y-%m-%d").date() if consent_data.get("re_consent_date") else None
                )
                consent_records.append(consent_record)
        
        session.add_all(consent_records)
        
        # ------------------------------
        # 3. Seed Survey Responses
        # ------------------------------
        print("Seeding survey responses...")
        survey_responses = []
        
        for record_id, responses in client._survey_responses.items():
            for r_data in responses:
                survey_response = SurveyResponse(
                    record_id=record_id,
                    redcap_event_name=r_data.get("redcap_event_name"),
                    month=r_data.get("month"),
                    survey_date=datetime.strptime(r_data["survey_date"], "%Y-%m-%d").date() if r_data.get("survey_date") else None,
                    survey_complete=r_data.get("survey_complete"),
                    perceived_stress_score=r_data.get("perceived_stress_score"),
                    mood_status=r_data.get("mood_status"),
                    anxiety_score=r_data.get("anxiety_score"),
                    depression_score=r_data.get("depression_score"),
                    sleep_quality=r_data.get("sleep_quality"),
                    daily_functioning=r_data.get("daily_functioning"),
                    fatigue_level=r_data.get("fatigue_level"),
                    school_attendance_days=r_data.get("school_attendance_days"),
                    social_isolation_score=r_data.get("social_isolation_score"),
                    coping_behaviours=r_data.get("coping_behaviours"),
                    substance_use=r_data.get("substance_use"),
                    suicidality_screening=r_data.get("suicidality_screening"),
                    self_esteem_score=r_data.get("self_esteem_score"),
                    loneliness_score=r_data.get("loneliness_score"),
                    risk_flag=r_data.get("risk_flag"),
                    requires_follow_up=r_data.get("requires_follow_up"),
                    redcap_repeat_instrument=r_data.get("redcap_repeat_instrument"),
                    redcap_repeat_instance=r_data.get("redcap_repeat_instance"),
                    # Comprehensive wave fields
                    examination_stress=r_data.get("examination_stress"),
                    academic_pressure=r_data.get("academic_pressure"),
                    homework_burden=r_data.get("homework_burden"),
                    school_climate=r_data.get("school_climate"),
                    bullying_exposure=r_data.get("bullying_exposure"),
                    harsh_discipline=r_data.get("harsh_discipline"),
                    educational_aspirations=r_data.get("educational_aspirations"),
                    fear_of_failure=r_data.get("fear_of_failure"),
                    teacher_support=r_data.get("teacher_support"),
                    counselling_access=r_data.get("counselling_access"),
                    household_assets=r_data.get("household_assets"),
                    food_insecurity=r_data.get("food_insecurity"),
                    economic_strain=r_data.get("economic_strain"),
                    employment_pressure=r_data.get("employment_pressure"),
                    financial_stress=r_data.get("financial_stress"),
                    digital_access=r_data.get("digital_access"),
                    household_instability=r_data.get("household_instability"),
                    internalised_stigma=r_data.get("internalised_stigma"),
                    community_stigma=r_data.get("community_stigma"),
                    family_stigma=r_data.get("family_stigma"),
                    school_stigma=r_data.get("school_stigma"),
                    mental_health_literacy=r_data.get("mental_health_literacy"),
                    help_seeking_intention=r_data.get("help_seeking_intention"),
                    help_seeking_behaviour=r_data.get("help_seeking_behaviour"),
                    awareness_of_services=r_data.get("awareness_of_services"),
                    resilience_score=r_data.get("resilience_score"),
                    social_support=r_data.get("social_support"),
                    family_connectedness=r_data.get("family_connectedness"),
                    peer_support=r_data.get("peer_support"),
                    community_connectedness=r_data.get("community_connectedness"),
                    religious_support=r_data.get("religious_support"),
                    school_belonging=r_data.get("school_belonging")
                )
                survey_responses.append(survey_response)
        
        session.add_all(survey_responses)
        
        # ------------------------------
        # 4. Seed Distress Screenings
        # ------------------------------
        print("Seeding distress screenings...")
        distress_screenings = []
        for s_data in client.get_distress_screenings():
            screening = DistressScreening(
                record_id=s_data["record_id"],
                screening_date=datetime.strptime(s_data["screening_date"], "%Y-%m-%d").date() if s_data.get("screening_date") else None,
                distress_score=s_data.get("distress_score"),
                suicidality_flag=s_data.get("suicidality_flag"),
                severity=s_data.get("severity"),
                trigger_form=s_data.get("trigger_form"),
                trigger_item=s_data.get("trigger_item"),
                assigned_responder=s_data.get("assigned_responder"),
                action_taken=s_data.get("action_taken"),
                referral_made=s_data.get("referral_made", "0"),
                referral_destination=s_data.get("referral_destination"),
                welfare_check_due=datetime.strptime(s_data["welfare_check_due"], "%Y-%m-%d").date() if s_data.get("welfare_check_due") else None,
                resolution_status=s_data.get("resolution_status", "open")
            )
            distress_screenings.append(screening)
        
        session.add_all(distress_screenings)
        
        # ------------------------------
        # 5. Seed WP6 Sessions
        # ------------------------------
        print("Seeding WP6 sessions...")
        wp6_sessions = []
        for record_id, sessions_data in client._wp6_sessions.items():
            for s_data in sessions_data:
                session_obj = WP6Session(
                    record_id=record_id,
                    session_number=s_data["session_number"],
                    session_date=datetime.strptime(s_data["session_date"], "%Y-%m-%d").date() if s_data.get("session_date") else None,
                    attendance=s_data.get("attendance"),
                    engagement_level=s_data.get("engagement_level"),
                    fidelity_score=s_data.get("fidelity_score"),
                    satisfaction_score=s_data.get("satisfaction_score"),
                    homework_completion=s_data.get("homework_completion"),
                    distress_pre=s_data.get("distress_pre"),
                    distress_post=s_data.get("distress_post")
                )
                wp6_sessions.append(session_obj)
        
        session.add_all(wp6_sessions)
        
        # ------------------------------
        # Commit everything!
        # ------------------------------
        await session.commit()
        print("✅ Database seeded successfully!")
        print(f"  - {len(participants)} participants")
        print(f"  - {len(consent_records)} consent records")
        print(f"  - {len(survey_responses)} survey responses")
        print(f"  - {len(distress_screenings)} distress screenings")
        print(f"  - {len(wp6_sessions)} WP6 sessions")


if __name__ == "__main__":
    asyncio.run(seed_database())
