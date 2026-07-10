import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, ForeignKey, DateTime, func, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.facility import Facility

class FieldType(str, PyEnum):
    BOOLEAN = "BOOLEAN"
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    SINGLE_SELECT = "SINGLE_SELECT"
    MULTI_SELECT = "MULTI_SELECT"

class MedicalHistoryCustomField(Base):
    __tablename__ = "medical_history_custom_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[FieldType] = mapped_column(Enum(FieldType, name="field_type_enum", create_type=False), nullable=False)
    options: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    facility: Mapped["Facility"] = relationship("Facility")
    creator: Mapped["User"] = relationship("User")


class MedicalHistoryRecord(Base):
    __tablename__ = "medical_history_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_updated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    blood_type: Mapped[str | None] = mapped_column(String, nullable=True)
    rh_factor: Mapped[str | None] = mapped_column(String, nullable=True)
    allergies: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    chronic_conditions: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    current_medications: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    surgical_history: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    
    previous_pregnancies: Mapped[int] = mapped_column(Integer, default=0)
    previous_outcomes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    family_history: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    patient: Mapped["User"] = relationship("User", foreign_keys=[patient_user_id])
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    updater: Mapped["User"] = relationship("User", foreign_keys=[last_updated_by])
