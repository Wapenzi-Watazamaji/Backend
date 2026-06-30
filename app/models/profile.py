import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, func, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .user import User

def generate_profile_id() -> str:
    return f"prf_{uuid.uuid4().hex[:8]}"

class CurrentStage(str, PyEnum):
    PREGNANT = "PREGNANT"
    POSTPARTUM = "POSTPARTUM"
    NOT_PREGNANT = "NOT_PREGNANT"

class SharingPreference(str, PyEnum):
    ASK_FIRST = "ASK_FIRST"
    ALWAYS_SHARE = "ALWAYS_SHARE"
    NEVER_SHARE = "NEVER_SHARE"

class ContactPreference(str, PyEnum):
    BOTH = "BOTH"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"

class DoctorRequestStatus(str, PyEnum):
    ASSIGNED = "ASSIGNED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"

class CompanionPreference(str, PyEnum):
    AI_DOC = "AI_DOC"
    PERSONAL_DOCTOR = "PERSONAL_DOCTOR"
    BOTH = "BOTH"
    NONE = "NONE"
   

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_profile_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    
    current_stage: Mapped[CurrentStage | None] = mapped_column(Enum(CurrentStage, name="current_stage_enum", create_type=False), nullable=True)
    preferred_unit_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    
    emergency_sharing_preference: Mapped[SharingPreference | None] = mapped_column(Enum(SharingPreference, name="sharing_pref_enum", create_type=False), nullable=True)
    contact_preference: Mapped[ContactPreference | None] = mapped_column(Enum(ContactPreference, name="contact_pref_enum", create_type=False), nullable=True)
    
    emergency_contact_name: Mapped[str | None] = mapped_column(String, nullable=True)
    emergency_contact_relationship: Mapped[str | None] = mapped_column(String, nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String, nullable=True)

    companion_preference: Mapped[CompanionPreference | None] = mapped_column(Enum(CompanionPreference, name="companion_pref_enum", create_type=False), nullable=True)

    personal_doctor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    personal_doctor_request_status: Mapped[DoctorRequestStatus | None] = mapped_column(Enum(DoctorRequestStatus, name="doctor_req_status_enum", create_type=False), nullable=True)
    qr_passport_token: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="profile")
