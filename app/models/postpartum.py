import uuid
from datetime import datetime, date, time
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Date, Time, Float, ForeignKey, func, Enum, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


# ------------------------------------------------------------------ #
# Enums                                                               #
# ------------------------------------------------------------------ #

class BabyGender(str, PyEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class DeliveryType(str, PyEnum):
    VAGINAL = "VAGINAL"
    C_SECTION = "C_SECTION"


class EpdsRiskLevel(str, PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    SELF_HARM_RISK = "SELF_HARM_RISK"


class MilestoneCategory(str, PyEnum):
    GROWTH = "GROWTH"
    MOVEMENT = "MOVEMENT"
    FEEDING = "FEEDING"
    SLEEP = "SLEEP"
    FIRST_MOMENTS = "FIRST_MOMENTS"


# ------------------------------------------------------------------ #
# Baby Profile                                                        #
# ------------------------------------------------------------------ #

class BabyProfile(Base):
    __tablename__ = "baby_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    pregnancy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pregnancy_records.id", ondelete="SET NULL"), nullable=True, index=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    time_of_birth: Mapped[time | None] = mapped_column(Time, nullable=True)
    gender: Mapped[BabyGender | None] = mapped_column(
        Enum(BabyGender, name="baby_gender_enum", create_type=False),
        nullable=True,
    )
    delivery_type: Mapped[DeliveryType | None] = mapped_column(
        Enum(DeliveryType, name="delivery_type_enum", create_type=False),
        nullable=True,
    )
    birth_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    birth_length_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(String, nullable=True)  # facility_id or free text
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    milestones: Mapped[list["BabyMilestone"]] = relationship("BabyMilestone", back_populates="baby", cascade="all, delete-orphan")
    vaccination_records: Mapped[list["BabyVaccinationRecord"]] = relationship("BabyVaccinationRecord", back_populates="baby", cascade="all, delete-orphan")


# ------------------------------------------------------------------ #
# Baby Milestone                                                      #
# ------------------------------------------------------------------ #

class BabyMilestone(Base):
    __tablename__ = "baby_milestones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    baby_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("baby_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    category: Mapped[MilestoneCategory] = mapped_column(
        Enum(MilestoneCategory, name="milestone_category_enum", create_type=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    achieved_at: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    baby: Mapped["BabyProfile"] = relationship("BabyProfile", back_populates="milestones")


# ------------------------------------------------------------------ #
# Baby Vaccination Record                                             #
# ------------------------------------------------------------------ #

class BabyVaccinationRecord(Base):
    """Stores a single administered vaccination event, linked to a ScheduledVisit."""
    __tablename__ = "baby_vaccination_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    baby_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("baby_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    # Links to the ScheduledVisit row that represents this vaccine slot
    scheduled_visit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scheduled_visits.id", ondelete="SET NULL"), nullable=True, index=True)
    vaccine_id: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "vac_bcg"
    given_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    facility_id: Mapped[str | None] = mapped_column(String, nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    baby: Mapped["BabyProfile"] = relationship("BabyProfile", back_populates="vaccination_records")


# ------------------------------------------------------------------ #
# EPDS Screening                                                      #
# ------------------------------------------------------------------ #

class EpdsScreening(Base):
    __tablename__ = "epds_screenings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    answers: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    q10_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_self_harm_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_level: Mapped[EpdsRiskLevel] = mapped_column(
        Enum(EpdsRiskLevel, name="epds_risk_level_enum", create_type=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
