import uuid
import enum
from datetime import datetime, date
from sqlalchemy import String, Date, DateTime, Enum as SQLEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class ReportType(str, enum.Enum):
    MONTHLY_FACILITY_SUMMARY = "MONTHLY_FACILITY_SUMMARY"
    ANC_ATTENDANCE = "ANC_ATTENDANCE"
    REFERRAL_ACTIVITY = "REFERRAL_ACTIVITY"
    RISK_FLAG_SUMMARY = "RISK_FLAG_SUMMARY"
    MOH_RMNCAH_SUBMISSION = "MOH_RMNCAH_SUBMISSION"

class ReportFormat(str, enum.Enum):
    PDF = "PDF"
    CSV = "CSV"
    EXCEL = "EXCEL"

class ReportStatus(str, enum.Enum):
    GENERATING = "GENERATING"
    READY = "READY"
    FAILED = "FAILED"

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[ReportType] = mapped_column(SQLEnum(ReportType, name="report_type_enum", create_type=False), nullable=False)
    date_range_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_range_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    format: Mapped[ReportFormat] = mapped_column(SQLEnum(ReportFormat, name="report_format_enum", create_type=False), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(SQLEnum(ReportStatus, name="report_status_enum", create_type=False), nullable=False, default=ReportStatus.GENERATING)
    file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
