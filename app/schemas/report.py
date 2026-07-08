import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.report import ReportType, ReportFormat, ReportStatus

class ReportCreate(BaseModel):
    type: ReportType
    dateRangeStart: Optional[date] = None
    dateRangeEnd: Optional[date] = None
    format: ReportFormat


class ReportRead(BaseModel):
    id: uuid.UUID
    facility_id: uuid.UUID
    type: ReportType
    date_range_start: date | None = None
    date_range_end: date | None = None
    format: ReportFormat
    status: ReportStatus
    file_url: Optional[str] = None
    generated_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PopulationSnapshot(BaseModel):
    totalPregnancies: int
    highRiskCount: int
    mediumRiskCount: int
    lowRiskCount: int
    trimesterBreakdown: dict[str, int]
    postpartumCount: int
    snapshotDate: date
