import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class ReferralReason(str, PyEnum):
    HEAVY_BLEEDING = "HEAVY_BLEEDING"
    SEVERE_PAIN = "SEVERE_PAIN"
    REDUCED_FETAL_MOVEMENT = "REDUCED_FETAL_MOVEMENT"
    LABOUR_STARTED = "LABOUR_STARTED"
    SOMETHING_FEELS_WRONG = "SOMETHING_FEELS_WRONG"
    ROUTINE_TRANSFER = "ROUTINE_TRANSFER"
    SPECIALIST_REFERRAL = "SPECIALIST_REFERRAL"


class ReferralStatus(str, PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_facility_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    from_facility_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    reason: Mapped[ReferralReason] = mapped_column(
        Enum(ReferralReason, name="referral_reason_enum", create_type=False),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_emergency: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    offline_queued: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    client_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, name="referral_status_enum", create_type=False),
        nullable=False,
        default=ReferralStatus.PENDING,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    patient: Mapped["User"] = relationship("User", foreign_keys=[patient_id])
