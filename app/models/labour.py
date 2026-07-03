import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Integer, Float, ForeignKey, func, Enum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class LabourSessionStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class LabourOutcome(str, PyEnum):
    LIVE_BIRTH = "LIVE_BIRTH"
    STILLBIRTH = "STILLBIRTH"
    REFERRED = "REFERRED"
    OTHER = "OTHER"


class LabourDeliveryType(str, PyEnum):
    VAGINAL = "VAGINAL"
    C_SECTION = "C_SECTION"
    ASSISTED = "ASSISTED"


class LabourReadingType(str, PyEnum):
    DILATION = "DILATION"
    FHR = "FHR"
    MATERNAL_BP = "MATERNAL_BP"
    CONTRACTIONS = "CONTRACTIONS"


class AlertType(str, PyEnum):
    ACTION_LINE_CROSSED = "ACTION_LINE_CROSSED"
    FETAL_DISTRESS = "FETAL_DISTRESS"
    PPH_RISK = "PPH_RISK"
    PREECLAMPSIA_RISK = "PREECLAMPSIA_RISK"
    SEPSIS_RISK = "SEPSIS_RISK"


class AlertSeverity(str, PyEnum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


class LabourSession(Base):
    __tablename__ = "labour_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pregnancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pregnancy_records.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    clinician_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    active_labour_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[LabourSessionStatus] = mapped_column(
        Enum(LabourSessionStatus, name="labour_session_status_enum", create_type=False),
        nullable=False,
        default=LabourSessionStatus.ACTIVE,
    )
    outcome: Mapped[LabourOutcome | None] = mapped_column(
        Enum(LabourOutcome, name="labour_outcome_enum", create_type=False),
        nullable=True,
    )
    delivery_type: Mapped[LabourDeliveryType | None] = mapped_column(
        Enum(LabourDeliveryType, name="labour_delivery_type_enum", create_type=False),
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    readings: Mapped[list["LabourReading"]] = relationship("LabourReading", back_populates="session", cascade="all, delete-orphan")
    alerts: Mapped[list["LabourAlert"]] = relationship("LabourAlert", back_populates="session", cascade="all, delete-orphan")
    resuscitation_logs: Mapped[list["ResuscitationLog"]] = relationship("ResuscitationLog", back_populates="session", cascade="all, delete-orphan")


class LabourReading(Base):
    __tablename__ = "labour_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("labour_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[LabourReadingType] = mapped_column(
        Enum(LabourReadingType, name="labour_reading_type_enum", create_type=False),
        nullable=False,
        index=True,
    )
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["LabourSession"] = relationship("LabourSession", back_populates="readings")


class LabourAlert(Base):
    __tablename__ = "labour_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("labour_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="labour_alert_type_enum", create_type=False),
        nullable=False,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="labour_alert_severity_enum", create_type=False),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    escalated_to: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["LabourSession"] = relationship("LabourSession", back_populates="alerts")


class ResuscitationLog(Base):
    __tablename__ = "resuscitation_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("labour_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vitals_at_step: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["LabourSession"] = relationship("LabourSession", back_populates="resuscitation_logs")
