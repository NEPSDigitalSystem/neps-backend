
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    Enum,
    DateTime,
    Float,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.session import Base
import enum


class SurveyStatus(str, enum.Enum):
    COMPLETE = "2"
    UNVERIFIED = "1"
    INCOMPLETE = "0"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ReferralStatus(str, enum.Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SurveyResponse(Base):
    __tablename__ = "survey_responses"
    __table_args__ = {"schema": "neps_core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(String, nullable=False, index=True)
    redcap_event_name = Column(String, nullable=False)
    month = Column(Integer)
    survey_date = Column(Date)
    survey_complete = Column(Enum(SurveyStatus), default=SurveyStatus.INCOMPLETE)

    # Core WP4 psychosocial indicators
    perceived_stress_score = Column(Float)
    mood_status = Column(String)
    anxiety_score = Column(Float)
    depression_score = Column(Float)
    sleep_quality = Column(String)
    daily_functioning = Column(Float)
    fatigue_level = Column(String)

    # Educational
    school_attendance_days = Column(Integer)
    social_isolation_score = Column(Float)
    coping_behaviours = Column(String)
    substance_use = Column(String)

    # Safeguarding
    suicidality_screening = Column(String)
    self_esteem_score = Column(Float)
    loneliness_score = Column(Float)
    risk_flag = Column(String)
    requires_follow_up = Column(String)

    # REDCap metadata
    redcap_repeat_instrument = Column(String)
    redcap_repeat_instance = Column(String)

    # Comprehensive wave fields
    examination_stress = Column(Float)
    academic_pressure = Column(Float)
    homework_burden = Column(Float)
    school_climate = Column(String)
    bullying_exposure = Column(String)
    harsh_discipline = Column(String)
    educational_aspirations = Column(String)
    fear_of_failure = Column(Float)
    teacher_support = Column(Float)
    counselling_access = Column(String)
    household_assets = Column(Integer)
    food_insecurity = Column(String)
    economic_strain = Column(Float)
    employment_pressure = Column(String)
    financial_stress = Column(Float)
    digital_access = Column(String)
    household_instability = Column(String)
    internalised_stigma = Column(Float)
    community_stigma = Column(Float)
    family_stigma = Column(Float)
    school_stigma = Column(Float)
    mental_health_literacy = Column(Float)
    help_seeking_intention = Column(String)
    help_seeking_behaviour = Column(String)
    awareness_of_services = Column(String)
    resilience_score = Column(Float)
    social_support = Column(Float)
    family_connectedness = Column(Float)
    peer_support = Column(Float)
    community_connectedness = Column(Float)
    religious_support = Column(Float)
    school_belonging = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DistressScreening(Base):
    __tablename__ = "distress_screenings"
    __table_args__ = {"schema": "neps_core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(String, nullable=False, index=True)
    screening_date = Column(Date)
    distress_score = Column(Float)
    suicidality_flag = Column(String)
    severity = Column(Enum(RiskLevel))
    trigger_form = Column(String)
    trigger_item = Column(String)
    assigned_responder = Column(String)
    action_taken = Column(Text)
    referral_made = Column(String, default="0")
    referral_destination = Column(String)
    welfare_check_due = Column(Date)
    resolution_status = Column(String, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = {"schema": "neps_core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id = Column(String, unique=True, nullable=False)
    record_id = Column(String, nullable=False, index=True)
    initiation_date = Column(Date)
    destination = Column(String)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.INITIATED)
    notes = Column(Text)
    follow_up_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WP6Session(Base):
    __tablename__ = "wp6_sessions"
    __table_args__ = {"schema": "neps_core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(String, nullable=False, index=True)
    session_number = Column(Integer, nullable=False)
    session_date = Column(Date)
    attendance = Column(String)
    engagement_level = Column(Float)
    fidelity_score = Column(Float)
    satisfaction_score = Column(Float)
    homework_completion = Column(String)
    distress_pre = Column(Float)
    distress_post = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
