import uuid
from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel, model_validator

from app.models.pregnancy import PregnancyStatus, PregnancyOutcome, VisitStatus, RiskLevel, NutritionCategory


class PregnancyStartRequest(BaseModel):
    dateInputType: str
    lastMenstrualPeriod: Optional[date] = None
    dueDate: Optional[date] = None
    isFirstPregnancy: bool = False

    @model_validator(mode="after")
    def check_date_fields(self):
        if self.dateInputType == "LMP" and not self.lastMenstrualPeriod:
            raise ValueError("lastMenstrualPeriod is required when dateInputType is LMP")
        if self.dateInputType == "DUE_DATE" and not self.dueDate:
            raise ValueError("dueDate is required when dateInputType is DUE_DATE")
        if self.dateInputType not in ("LMP", "DUE_DATE"):
            raise ValueError("dateInputType must be 'LMP' or 'DUE_DATE'")
        return self


class PregnancyUpdateRequest(BaseModel):
    dueDate: date


class PregnancyEndRequest(BaseModel):
    endedAt: datetime
    outcome: PregnancyOutcome


class PregnancyRecordRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    last_menstrual_period: date
    due_date: date
    is_first_pregnancy: bool
    status: PregnancyStatus
    outcome: Optional[PregnancyOutcome] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WeekInfoRead(BaseModel):
    weekNumber: int
    trimester: int
    babySizeComparison: str
    developmentNote: str
    imageUrl: Optional[str] = None


class VitalsCreateRequest(BaseModel):
    templateSlug: str
    answers: dict[str, Any]
    clientGeneratedId: Optional[str] = None
    clientCreatedAt: Optional[datetime] = None


class VitalsUpdateRequest(BaseModel):
    answers: dict[str, Any]


class VitalsEntryRead(BaseModel):
    id: uuid.UUID
    pregnancy_id: uuid.UUID
    submission_id: uuid.UUID
    is_flagged: bool
    flagged_reasons: list[str]
    answers: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def extract_answers(cls, obj):
        if hasattr(obj, "submission") and obj.submission and not isinstance(obj, dict):
            return {
                "id": obj.id,
                "pregnancy_id": obj.pregnancy_id,
                "submission_id": obj.submission_id,
                "is_flagged": obj.is_flagged,
                "flagged_reasons": obj.flagged_reasons,
                "answers": obj.submission.answers,
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
            }
        return obj


class FormTemplateRead(BaseModel):
    id: uuid.UUID
    slug: str
    context: str
    fields: dict
    version: str
    is_active: bool

    model_config = {"from_attributes": True}


class FeedbackCreateRequest(BaseModel):
    message: str


class FeedbackRead(BaseModel):
    id: uuid.UUID
    vitals_entry_id: uuid.UUID
    clinician_id: uuid.UUID
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class VisitRead(BaseModel):
    id: uuid.UUID
    pathway_template_id: Optional[str] = None
    milestone_order: Optional[int] = None
    label: str
    scheduled_at: datetime
    status: VisitStatus
    facility_id: Optional[uuid.UUID] = None
    purpose: Optional[str] = None
    summary: Optional[str] = None

    model_config = {"from_attributes": True}


class ManualVisitCreateRequest(BaseModel):
    scheduledAt: datetime
    facilityId: Optional[uuid.UUID] = None
    purpose: str


class VisitUpdateRequest(BaseModel):
    status: Optional[VisitStatus] = None
    summary: Optional[str] = None
    scheduledAt: Optional[datetime] = None


class NutritionGuidanceRead(BaseModel):
    id: uuid.UUID
    category: NutritionCategory
    title: str
    summary: str
    trimester_relevance: list[int]
    icon_url: Optional[str] = None

    model_config = {"from_attributes": True}


class RiskFactor(BaseModel):
    label: str
    weight: int
    severity: str
    description: str


class ClinicianOverride(BaseModel):
    level: RiskLevel
    reason: str
    overriddenBy: str
    overriddenAt: datetime


class RiskScoreOverrideRequest(BaseModel):
    level: RiskLevel
    reason: str


class RiskScoreRead(BaseModel):
    score: int
    level: RiskLevel
    calculatedAt: datetime
    clinicianOverride: Optional[ClinicianOverride] = None
    factors: list[RiskFactor]

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_fields(cls, obj):
        if hasattr(obj, "calculated_at") and not isinstance(obj, dict):
            override = None
            if obj.clinician_override:
                override = obj.clinician_override
            return {
                "score": obj.score,
                "level": obj.level,
                "calculatedAt": obj.calculated_at,
                "clinicianOverride": override,
                "factors": obj.factors,
            }
        return obj


class RiskScoreHistoryItem(BaseModel):
    calculatedAt: datetime
    score: int
    level: RiskLevel

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_fields(cls, obj):
        if hasattr(obj, "calculated_at") and not isinstance(obj, dict):
            return {"calculatedAt": obj.calculated_at, "score": obj.score, "level": obj.level}
        return obj
