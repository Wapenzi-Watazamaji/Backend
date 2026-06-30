import uuid
from typing import TYPE_CHECKING
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Date, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

def generate_user_id() -> str:
    return f"usr_{uuid.uuid4().hex[:8]}"

class UserRole(str, PyEnum):
    MOTHER = "MOTHER"
    CLINICIAN = "CLINICIAN"
    FACILITY_ADMIN = "FACILITY_ADMIN"

class Gender(str, PyEnum):
    FEMALE = "FEMALE"
    MALE = "MALE"

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_user_id)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role_enum", create_type=False), nullable=False)
    
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
        
    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
