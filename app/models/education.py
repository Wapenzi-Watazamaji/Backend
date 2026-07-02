import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class ContentCategory(str, enum.Enum):
    HYDRATION = "HYDRATION"
    NUTRITION = "NUTRITION"
    EXERCISE = "EXERCISE"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    GENERAL = "GENERAL"

class EducationContent(Base):
    __tablename__ = "education_content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[ContentCategory] = mapped_column(SQLEnum(ContentCategory, name="content_category_enum", create_type=False), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    target_stages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    facility = relationship("Facility")

class EducationEvent(Base):
    __tablename__ = "education_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    facility = relationship("Facility")
