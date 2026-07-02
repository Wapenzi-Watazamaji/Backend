import uuid
from typing import TYPE_CHECKING
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Date, Integer, Float, ForeignKey, func, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON

from app.db.base import Base

if TYPE_CHECKING:
    from .user import User


class FormContext(str, PyEnum):
    CYCLE_ENTRY = "CYCLE_ENTRY"
    CYCLE_SYMPTOM = "CYCLE_SYMPTOM"
    PREGNANCY_VITALS = "PREGNANCY_VITALS"
    MATERNAL_CHECKIN = "MATERNAL_CHECKIN"
    BABY_VITALS = "BABY_VITALS"


class PbacItemType(str, PyEnum):
    PAD = "PAD"
    TAMPON = "TAMPON"
    CLOT = "CLOT"


class PbacSoakLevel(str, PyEnum):
    LIGHTLY_SOAKED = "LIGHTLY_SOAKED"
    MODERATELY_SOAKED = "MODERATELY_SOAKED"
    FULLY_SOAKED = "FULLY_SOAKED"


class HmbAcknowledgeAction(str, PyEnum):
    DISMISSED = "DISMISSED"
    TALK_TO_DOCTOR = "TALK_TO_DOCTOR"


class FormTemplate(Base):
    __tablename__ = "form_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
    context: Mapped[FormContext] = mapped_column(Enum(FormContext, name="form_context_enum", create_type=False), nullable=False)
    fields: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False, default="v1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    facility_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    submissions: Mapped[list["FormSubmission"]] = relationship("FormSubmission", back_populates="template")


class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("form_templates.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    context: Mapped[FormContext] = mapped_column(Enum(FormContext, name="form_context_enum", create_type=False), nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, nullable=False)
    client_generated_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    client_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    template: Mapped["FormTemplate"] = relationship("FormTemplate", back_populates="submissions")
    cycle_entry: Mapped["CycleEntry | None"] = relationship("CycleEntry", back_populates="submission", uselist=False)


class CycleEntry(Base):
    __tablename__ = "cycle_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("form_submissions.id", ondelete="CASCADE"), nullable=False, unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pbac_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    submission: Mapped["FormSubmission"] = relationship("FormSubmission", back_populates="cycle_entry")
    pbac_items: Mapped[list["PbacItem"]] = relationship("PbacItem", back_populates="cycle_entry", cascade="all, delete-orphan")


class PbacItem(Base):
    __tablename__ = "pbac_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cycle_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    item_type: Mapped[PbacItemType] = mapped_column(Enum(PbacItemType, name="pbac_item_type_enum", create_type=False), nullable=False)
    soak_level: Mapped[PbacSoakLevel | None] = mapped_column(Enum(PbacSoakLevel, name="pbac_soak_level_enum", create_type=False), nullable=True)
    point_value: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cycle_entry: Mapped["CycleEntry"] = relationship("CycleEntry", back_populates="pbac_items")


class HmbStatus(Base):
    __tablename__ = "hmb_statuses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_action: Mapped[HmbAcknowledgeAction | None] = mapped_column(
        Enum(HmbAcknowledgeAction, name="hmb_ack_action_enum", create_type=False), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
