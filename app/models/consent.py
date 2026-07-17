import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

if TYPE_CHECKING:
    from .user import User

class ConsentType(str, PyEnum):
    ASK_EVERYTIME = "ASK_EVERYTIME"
    AUTO_SHARE = "AUTO_SHARE"
    FACILITY_AUTO_SHARE = "FACILITY_AUTO_SHARE"

class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    consent_type: Mapped[ConsentType] = mapped_column(Enum(ConsentType, name="consent_type_enum", create_type=False), nullable=False)
    
    grantee_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    grantee_name: Mapped[str | None] = mapped_column(String, nullable=True)
    
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="consents")