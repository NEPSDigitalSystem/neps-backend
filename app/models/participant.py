
from sqlalchemy import Column, String, Integer, Date, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.session import Base
import enum


class ConsentStatus(str, enum.Enum):
    CONSENTED = "consented"
    PENDING = "pending"
    WITHDRAWN = "withdrawn"
    ASSENT_ONLY = "assent_only"


class CohortStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    WITHDRAWN = "withdrawn"


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = {"schema": "neps_core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(String, unique=True, nullable=False, index=True)
    redcap_event_name = Column(String)
    country = Column(String, nullable=False, index=True)
    site = Column(String, nullable=False, index=True)
    school = Column(String)
    age = Column(Integer)
    date_of_birth = Column(Date)
    gender = Column(String)
    grade_level = Column(String)
    enrollment_date = Column(Date)
    cohort_status = Column(Enum(CohortStatus), default=CohortStatus.ACTIVE)
    phone_contact = Column(String)
    consent_status = Column(Enum(ConsentStatus), default=ConsentStatus.PENDING)
    redcap_data_access_group = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    __table_args__ = {"schema": "neps_core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), nullable=False)
    record_id = Column(String, nullable=False)
    consent_date = Column(Date)
    consent_version = Column(String)
    consent_status = Column(Enum(ConsentStatus))
    guardian_consent = Column(String)
    assent_status = Column(String)
    consent_withdrawn = Column(String, default="0")
    withdrawal_reason = Column(String)
    re_consent_required = Column(String, default="0")
    re_consent_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
