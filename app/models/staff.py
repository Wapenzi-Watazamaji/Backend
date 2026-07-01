import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.facility import Facility
    from app.models.user import User

class StaffStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INVITE_PENDING = "INVITE_PENDING"
    DEACTIVATED = "DEACTIVATED"

class StaffRole(str, enum.Enum):
    CLINICIAN = "CLINICIAN"
    FACILITY_ADMIN = "FACILITY_ADMIN"

class StaffMember(Base):
    __tablename__ = "staff_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    role: Mapped[StaffRole] = mapped_column(SQLEnum(StaffRole, name="staff_role_enum", create_type=False), nullable=False)
    specialty: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_patient_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[StaffStatus] = mapped_column(SQLEnum(StaffStatus, name="staff_status_enum", create_type=False), nullable=False, default=StaffStatus.INVITE_PENDING)
    
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    facility: Mapped["Facility"] = relationship("Facility", back_populates="staff_members")
    user: Mapped["User"] = relationship("User")
