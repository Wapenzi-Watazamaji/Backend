import uuid
from typing import TYPE_CHECKING
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Date, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class UserRole(str, PyEnum):
    USER = "USER"
    CLINICIAN = "CLINICIAN"
    FACILITY_ADMIN = "FACILITY_ADMIN"

class Gender(str, PyEnum):
    FEMALE = "FEMALE"
    MALE = "MALE"

class AccountType(str, PyEnum):
    FULL = "FULL"
    SMS_ONLY = "SMS_ONLY"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role_enum", create_type=False), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="account_type_enum", create_type=False), nullable=False, server_default="FULL")
    
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender, name="gender_enum", create_type=False), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String, default="en")
    county: Mapped[str | None] = mapped_column(String, nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    if TYPE_CHECKING:
        from .profile import Profile
        from .consent import Consent
        
    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consents: Mapped[list["Consent"]] = relationship("Consent", back_populates="user", cascade="all, delete-orphan")
