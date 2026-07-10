import uuid
from typing import TYPE_CHECKING
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Date, Integer, Float, ForeignKey, func, Enum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.cycle import FormSubmission
    from app.models.postpartum import BabyProfile


class PregnancyStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class PregnancyOutcome(str, PyEnum):
    LIVE_BIRTH = "LIVE_BIRTH"
    STILLBIRTH = "STILLBIRTH"
    MISCARRIAGE = "MISCARRIAGE"
    OTHER = "OTHER"


class VisitStatus(str, PyEnum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    MISSED = "MISSED"
    RESCHEDULED = "RESCHEDULED"


class RiskLevel(str, PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NutritionCategory(str, PyEnum):
    IRON = "IRON"
    FOLIC_ACID = "FOLIC_ACID"
    HYDRATION = "HYDRATION"
    FOODS_TO_AVOID = "FOODS_TO_AVOID"
    HEALTHY_SNACKS = "HEALTHY_SNACKS"


class PregnancyRecord(Base):
    __tablename__ = "pregnancy_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    last_menstrual_period: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_first_pregnancy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[PregnancyStatus] = mapped_column(
        Enum(PregnancyStatus, name="pregnancy_status_enum", create_type=False),
        nullable=False,
        default=PregnancyStatus.ACTIVE,
    )
    outcome: Mapped[PregnancyOutcome | None] = mapped_column(
        Enum(PregnancyOutcome, name="pregnancy_outcome_enum", create_type=False),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vitals_entries: Mapped[list["PregnancyVitalsEntry"]] = relationship("PregnancyVitalsEntry", back_populates="pregnancy", cascade="all, delete-orphan")
    scheduled_visits: Mapped[list["ScheduledVisit"]] = relationship("ScheduledVisit", back_populates="pregnancy", cascade="all, delete-orphan")
    risk_scores: Mapped[list["PregnancyRiskScore"]] = relationship("PregnancyRiskScore", back_populates="pregnancy", cascade="all, delete-orphan")
    babies: Mapped[list["BabyProfile"]] = relationship("BabyProfile", back_populates="pregnancy", foreign_keys="BabyProfile.pregnancy_id")


class CarePathwayTemplate(Base):
    __tablename__ = "care_pathway_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    milestones: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    visits: Mapped[list["ScheduledVisit"]] = relationship("ScheduledVisit", back_populates="pathway_template")


class PregnancyVitalsEntry(Base):
    __tablename__ = "pregnancy_vitals_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pregnancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pregnancy_records.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("form_submissions.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    flagged_reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    pregnancy: Mapped["PregnancyRecord"] = relationship("PregnancyRecord", back_populates="vitals_entries")
    submission: Mapped["FormSubmission"] = relationship("FormSubmission")
    feedback: Mapped[list["VitalsFeedback"]] = relationship("VitalsFeedback", back_populates="vitals_entry", cascade="all, delete-orphan")

    @property
    def answers(self) -> dict:
        return self.submission.answers if self.submission else {}


class VitalsFeedback(Base):
    __tablename__ = "vitals_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vitals_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pregnancy_vitals_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    clinician_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vitals_entry: Mapped["PregnancyVitalsEntry"] = relationship("PregnancyVitalsEntry", back_populates="feedback")


class ClinicalNote(Base):
    """A clinician note on a patient record.
    Optionally linked to a specific vitals entry (via vitals_entry_id).
    When vitals_entry_id is null, the note is a free-standing patient note.
    """
    __tablename__ = "clinical_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    clinician_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional link to a generic form submission (vitals, cycle, postpartum, etc.)
    submission_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("form_submissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ScheduledVisit(Base):
    __tablename__ = "scheduled_visits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pregnancy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pregnancy_records.id", ondelete="CASCADE"), nullable=True, index=True)
    baby_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("baby_profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    pathway_template_id: Mapped[str | None] = mapped_column(ForeignKey("care_pathway_templates.id"), nullable=True)
    milestone_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[VisitStatus] = mapped_column(
        Enum(VisitStatus, name="visit_status_enum", create_type=False),
        nullable=False,
        default=VisitStatus.SCHEDULED,
    )
    facility_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    pregnancy: Mapped["PregnancyRecord"] = relationship("PregnancyRecord", back_populates="scheduled_visits")
    pathway_template: Mapped["CarePathwayTemplate | None"] = relationship("CarePathwayTemplate", back_populates="visits")


class PregnancyRiskScore(Base):
    __tablename__ = "pregnancy_risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pregnancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pregnancy_records.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level_enum", create_type=False),
        nullable=False,
        default=RiskLevel.LOW,
    )
    factors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    clinician_override: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pregnancy: Mapped["PregnancyRecord"] = relationship("PregnancyRecord", back_populates="risk_scores")


class WeekInfo(Base):
    __tablename__ = "pregnancy_week_info"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    trimester: Mapped[int] = mapped_column(Integer, nullable=False)
    baby_size_comparison: Mapped[str] = mapped_column(String, nullable=False)
    development_note: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)


class NutritionGuidance(Base):
    __tablename__ = "nutrition_guidance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[NutritionCategory] = mapped_column(
        Enum(NutritionCategory, name="nutrition_category_enum", create_type=False),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    trimester_relevance: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    icon_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
