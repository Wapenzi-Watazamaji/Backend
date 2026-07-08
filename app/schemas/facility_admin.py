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

class FacilityAdminOverviewWeekAtAGlance(BaseModel):
    ancVisitsCompleted: int
    ancVisitsScheduled: int
    deliveries: int
    referralsAccepted: int
    referralsSentOut: int
    postnatalFollowUpsDue: int

class FacilityAdminOverview(BaseModel):
    totalPatients: int
    patientsDeltaThisWeek: int
    unassignedPatientsCount: int
    activeCliniciansCount: int
    facilityWideAlertsCount: int
    thisWeekAtAGlance: FacilityAdminOverviewWeekAtAGlance

class ClinicianWorkload(BaseModel):
    clinicianId: uuid.UUID
    clinicianName: str
    specialty: Optional[str] = None
    assignedPatientCount: int
    maxCapacity: int

class StaffMember(BaseModel):
    userId: Optional[uuid.UUID] = None
    name: str
    role: str
    specialty: Optional[str] = None
    assignedPatients: int
    status: str
    email: Optional[str] = None

class StaffInvite(BaseModel):
    email: str
    role: str
    specialty: Optional[str] = None
