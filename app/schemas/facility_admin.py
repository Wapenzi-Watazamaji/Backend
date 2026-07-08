import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models.user import Gender, AccountType
from app.models.profile import CurrentStage
from app.models.cycle import FormContext

class PatientManualRegister(BaseModel):
    fullName: str
    phoneNumber: str
    dateOfBirth: date
    gender: Gender
    accountType: AccountType
    currentStage: CurrentStage
    facilityId: uuid.UUID

class PatientUnassignedRead(BaseModel):
    patientUserId: uuid.UUID
    fullName: str
    stage: str
    stageDetail: str
    registeredAt: datetime
    isReferralFromOtherFacility: bool
    referralFromFacilityName: Optional[str] = None

class BulkAssignRequest(BaseModel):
    patientUserIds: list[uuid.UUID]
    clinicianId: uuid.UUID

class FormField(BaseModel):
    key: str
    label: str
    type: str
    unit: Optional[str] = None
    required: bool = False
    options: Optional[list[str]] = None
    flaggingOptions: Optional[list[str]] = None

class FormTemplateCreateOverride(BaseModel):
    context: FormContext
    facilityId: uuid.UUID
    basedOnTemplateId: uuid.UUID
    additionalFields: list[FormField]
