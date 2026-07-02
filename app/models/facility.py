import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Float, JSON, Enum as SQLEnum, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.staff import StaffMember

class FacilityType(str, enum.Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    MISSION = "MISSION"
    NGO = "NGO"

class FacilityStatus(str, enum.Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    SUSPENDED = "SUSPENDED"

class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[FacilityType] = mapped_column(SQLEnum(FacilityType, name="facility_type_enum", create_type=False), nullable=False)
    county: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[FacilityStatus] = mapped_column(SQLEnum(FacilityStatus, name="facility_status_enum", create_type=False), nullable=False, default=FacilityStatus.PENDING_VERIFICATION)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Store services as an array of strings (e.g. ["ANTENATAL_CARE", "DELIVERY", "NEONATAL_ICU"])
    services_offered: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    
    # Readiness state (e.g. bloodBankStocked, maternityBedsAvailable)
    readiness: Mapped[dict] = mapped_column(JSON, default=dict)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    staff_members: Mapped[list["StaffMember"]] = relationship("StaffMember", back_populates="facility")
