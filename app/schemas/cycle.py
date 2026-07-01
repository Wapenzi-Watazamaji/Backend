import uuid
from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

from app.models.cycle import FormContext, PbacItemType, PbacSoakLevel, HmbAcknowledgeAction


class FormTemplateRead(BaseModel):
    id: uuid.UUID
    slug: str
    context: FormContext
    fields: Any
    version: str
    is_active: bool
    facility_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FormSubmissionRead(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    user_id: uuid.UUID
    context: FormContext
    answers: Any
    client_generated_id: Optional[str] = None
    client_created_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CycleEntryCreate(BaseModel):
    startDate: date
    endDate: Optional[date] = None
    templateSlug: str
    answers: dict[str, Any]
    clientGeneratedId: Optional[str] = None
    clientCreatedAt: Optional[datetime] = None


class CycleEntryUpdate(BaseModel):
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    answers: Optional[dict[str, Any]] = None


class CycleEntryRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    submission_id: uuid.UUID
    start_date: date
    end_date: Optional[date] = None
    pbac_score: Optional[int] = None
    submission: FormSubmissionRead
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SymptomCreate(BaseModel):
    date: date
    templateSlug: str
    answers: dict[str, Any]
    clientGeneratedId: Optional[str] = None


class SymptomRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    submission_id: uuid.UUID
    date: date
    submission: FormSubmissionRead
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PbacItemCreate(BaseModel):
    date: date
    itemType: PbacItemType
    soakLevel: Optional[PbacSoakLevel] = None
    pointValue: int


class PbacItemRead(BaseModel):
    id: uuid.UUID
    cycle_entry_id: uuid.UUID
    date: date
    item_type: PbacItemType
    soak_level: Optional[PbacSoakLevel] = None
    point_value: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PbacScoreRead(BaseModel):
    entryId: uuid.UUID
    totalScore: int
    isHmbRisk: bool


class PredictionRead(BaseModel):
    nextPeriodPredictedDate: Optional[date]
    ovulationWindowStart: Optional[date]
    ovulationWindowEnd: Optional[date]
    averageCycleLengthDays: Optional[int]
    currentCycleDay: Optional[int]


class CycleLengthMonth(BaseModel):
    month: str
    averageLengthDays: int


class TrendInsight(BaseModel):
    type: str
    message: str


class TopSymptom(BaseModel):
    symptom: str
    count: int


class TrendRead(BaseModel):
    cycleLengthHistory: list[CycleLengthMonth]
    insights: list[TrendInsight]
    topSymptoms: list[TopSymptom]


class HmbStatusRead(BaseModel):
    isActive: bool
    triggeredAt: Optional[datetime] = None
    reasons: list[str] = []


class HmbAcknowledgeRequest(BaseModel):
    action: HmbAcknowledgeAction
