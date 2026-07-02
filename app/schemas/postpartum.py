import uuid
from datetime import date, datetime, time
from typing import Optional, List
from pydantic import BaseModel, field_validator

from app.models.postpartum import BabyGender, DeliveryType, EpdsRiskLevel, MilestoneCategory


# ------------------------------------------------------------------ #
# Baby Profile                                                        #
# ------------------------------------------------------------------ #

class BabyProfileCreate(BaseModel):
    name: str
    dateOfBirth: date
    timeOfBirth: Optional[str] = None          # "HH:MM"
    sex: Optional[BabyGender] = None
    birthWeightKg: Optional[float] = None
    birthLengthCm: Optional[float] = None
    deliveryType: Optional[DeliveryType] = None
    placeOfBirth: Optional[str] = None
    notes: Optional[str] = None
    pregnancyId: Optional[uuid.UUID] = None


class BabyProfileUpdate(BaseModel):
    name: Optional[str] = None
    sex: Optional[BabyGender] = None
    birthWeightKg: Optional[float] = None
    birthLengthCm: Optional[float] = None
    deliveryType: Optional[DeliveryType] = None
    placeOfBirth: Optional[str] = None
    notes: Optional[str] = None


class BabyProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    pregnancy_id: Optional[uuid.UUID] = None
    name: str
    date_of_birth: date
    time_of_birth: Optional[time] = None
    gender: Optional[BabyGender] = None
    delivery_type: Optional[DeliveryType] = None
    birth_weight_kg: Optional[float] = None
    birth_length_cm: Optional[float] = None
    place_of_birth: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Baby Milestone                                                      #
# ------------------------------------------------------------------ #

class BabyMilestoneCreate(BaseModel):
    category: MilestoneCategory
    title: str
    achievedAt: date
    note: Optional[str] = None
    photoUrl: Optional[str] = None


class BabyMilestoneRead(BaseModel):
    id: uuid.UUID
    baby_id: uuid.UUID
    user_id: uuid.UUID
    category: MilestoneCategory
    title: str
    achieved_at: date
    note: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Baby Vaccination                                                    #
# ------------------------------------------------------------------ #

class VaccinationRecordCreate(BaseModel):
    vaccineId: str
    givenAt: datetime
    facilityId: Optional[str] = None
    batchNumber: Optional[str] = None


class VaccinationRecordRead(BaseModel):
    id: uuid.UUID
    baby_id: uuid.UUID
    scheduled_visit_id: Optional[uuid.UUID] = None
    vaccine_id: str
    given_at: datetime
    facility_id: Optional[str] = None
    batch_number: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VaccinationScheduleItem(BaseModel):
    """Represents a single row in the GET /baby/vaccinations/schedule response."""
    id: uuid.UUID
    vaccineId: Optional[str] = None
    name: str
    ageMilestone: str
    status: str          # GIVEN | UPCOMING | OVERDUE
    scheduledAt: Optional[datetime] = None
    givenAt: Optional[datetime] = None


class MarkGivenRequest(BaseModel):
    givenAt: datetime
    facilityId: Optional[str] = None
    batchNumber: Optional[str] = None


# ------------------------------------------------------------------ #
# EPDS Screening — new spec shape                                     #
# ------------------------------------------------------------------ #

class EpdsAnswerItem(BaseModel):
    questionId: str        # "q1" … "q10"
    answerValue: int

    @field_validator("answerValue")
    @classmethod
    def validate_range(cls, v: int) -> int:
        if not (0 <= v <= 3):
            raise ValueError("answerValue must be between 0 and 3")
        return v


class EpdsSubmitRequest(BaseModel):
    responses: List[EpdsAnswerItem]


class EpdsScreeningRead(BaseModel):
    id: uuid.UUID
    totalScore: int
    suggestsSupportBeneficial: bool
    immediateConcernFlag: bool
    completedAt: datetime

    model_config = {"from_attributes": False}


class EpdsHistoryItem(BaseModel):
    id: uuid.UUID
    totalScore: int
    immediateConcernFlag: bool
    completedAt: datetime


class EpdsFlagStatus(BaseModel):
    isActive: bool


# ------------------------------------------------------------------ #
# Maternal Check-in                                                   #
# ------------------------------------------------------------------ #

class MaternalCheckinCreate(BaseModel):
    templateId: str
    answers: dict
    clientGeneratedId: Optional[str] = None
    clientCreatedAt: Optional[datetime] = None


class MaternalCheckinRead(BaseModel):
    """Thin wrapper — returns the underlying FormSubmission."""
    id: uuid.UUID
    template_id: uuid.UUID
    user_id: uuid.UUID
    context: str
    answers: dict
    client_generated_id: Optional[str] = None
    client_created_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Baby Vitals                                                         #
# ------------------------------------------------------------------ #

class BabyVitalsCreate(BaseModel):
    templateId: str
    answers: dict
    clientGeneratedId: Optional[str] = None
    clientCreatedAt: Optional[datetime] = None


class BabyAlertRead(BaseModel):
    id: str
    type: str
    message: str
    createdAt: datetime


# ------------------------------------------------------------------ #
# Postnatal Clinic Visit                                              #
# ------------------------------------------------------------------ #

class PostnatalVisitRead(BaseModel):
    id: uuid.UUID
    label: str
    scheduledAt: datetime
    covers: List[str]
    status: str

    model_config = {"from_attributes": False}


# ------------------------------------------------------------------ #
# Form Template (reused from pregnancy schemas)                       #
# ------------------------------------------------------------------ #

class FormTemplateRead(BaseModel):
    id: uuid.UUID
    slug: str
    context: str
    fields: dict
    version: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
