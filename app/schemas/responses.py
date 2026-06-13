from pydantic import BaseModel
from typing import Dict, Union, Optional

class RootResponse(BaseModel):
    message: str
    app_name: str
    app_env: str
    redcap_mock_enabled: bool

class ErrorResponse(BaseModel):
    detail: str

class ParticipantResponse(BaseModel):
    record_id: str
    redcap_event_name: str
    country: str
    site: str
    school: str
    age: int
    date_of_birth: str
    gender: str
    grade_level: Union[str, int]
    enrollment_date: str
    cohort_status: str
    phone_contact: str
    consent_status: str
    redcap_data_access_group: str
    redcap_repeat_instrument: str
    redcap_repeat_instance: str

class ConsentStatusResponse(BaseModel):
    record_id: str
    consent_date: str
    consent_version: str
    consent_status: str
    guardian_consent: str
    assent_status: str
    consent_withdrawn: str
    withdrawal_reason: str
    re_consent_required: str
    re_consent_date: str

class ReferralResponse(BaseModel):
    referral_id: str
    record_id: str
    initiation_date: str
    destination: str
    status: str
    notes: str
    follow_up_date: str

class DistressScreeningResponse(BaseModel):
    record_id: str
    screening_date: str
    distress_score: float
    suicidality_flag: str
    severity: str
    trigger_form: str
    trigger_item: str
    assigned_responder: str
    action_taken: str
    referral_made: str
    referral_destination: str
    welfare_check_due: str
    resolution_status: str

class WP6SessionResponse(BaseModel):
    record_id: str
    session_number: int
    session_date: str
    attendance: str
    engagement_level: float
    fidelity_score: float
    satisfaction_score: float
    homework_completion: str
    distress_pre: float
    distress_post: float

class SurveyResponseBase(BaseModel):
    record_id: str
    redcap_event_name: str
    survey_complete: str
    redcap_repeat_instrument: str
    redcap_repeat_instance: str

class MonthlySurveyResponse(SurveyResponseBase):
    month: int
    survey_date: str
    perceived_stress_score: float
    mood_status: str
    anxiety_score: float
    depression_score: float
    sleep_quality: str
    daily_functioning: float
    fatigue_level: str
    school_attendance_days: int
    social_isolation_score: float
    coping_behaviours: str
    substance_use: str
    suicidality_screening: str
    self_esteem_score: float
    loneliness_score: float
    risk_flag: str
    requires_follow_up: str

class HealthCheckDependency(BaseModel):
    status: str
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    used_percent: Optional[float] = None

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    service: str
    dependencies: Dict[str, HealthCheckDependency]

class RedcapStatsResponse(BaseModel):
    total_participants: int
    by_country: Dict[str, int]
    active_cohort: int
    total_surveys: int
    high_risk_flags: int
    open_referrals: int
    wp6_enrolled: int