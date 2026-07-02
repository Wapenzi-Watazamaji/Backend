import uuid
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class ReferralReason(str, enum.Enum):
    EMERGENCY_COMPLICATION = "EMERGENCY_COMPLICATION"
    SPECIALIST_CARE = "SPECIALIST_CARE"
    LACK_OF_EQUIPMENT = "LACK_OF_EQUIPMENT"
    PATIENT_PREFERENCE = "PATIENT_PREFERENCE"
    OTHER = "OTHER"

class ReferralPriority(str, enum.Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"

class ReferralStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED = "ARRIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sending_facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    receiving_facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    reason: Mapped[ReferralReason] = mapped_column(SQLEnum(ReferralReason, name="referral_reason_enum", create_type=False), nullable=False)
    priority: Mapped[ReferralPriority] = mapped_column(SQLEnum(ReferralPriority, name="referral_priority_enum", create_type=False), nullable=False)
    status: Mapped[ReferralStatus] = mapped_column(SQLEnum(ReferralStatus, name="referral_status_enum", create_type=False), nullable=False, default=ReferralStatus.PENDING)
    
    clinical_notes: Mapped[str] = mapped_column(Text, nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    sending_facility = relationship("Facility", foreign_keys=[sending_facility_id])
    receiving_facility = relationship("Facility", foreign_keys=[receiving_facility_id])
