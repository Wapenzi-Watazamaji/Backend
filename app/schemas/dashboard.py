import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel

class DashboardSummary(BaseModel):
    assignedPatientCount: int
    assignedPatientCountDeltaThisWeek: int
    activeAlertCount: int
    ancVisitsToday: int
    ancVisitsCompletedToday: int
    pendingReferralCount: int

class DashboardAlert(BaseModel):
    id: str
    patientUserId: uuid.UUID
    patientName: str
    type: str
    severity: str
    message: str
    sourceSubmissionId: Optional[uuid.UUID] = None
    createdAt: datetime
    acknowledgedAt: Optional[datetime] = None

class AncVisitToday(BaseModel):
    scheduledVisitId: uuid.UUID
    patientName: str
    scheduledAt: datetime
    purpose: Optional[str] = None
    status: str

class PatientDirectoryItem(BaseModel):
    userId: uuid.UUID
    fullName: str
    age: Optional[int] = None
    patientCode: Optional[str] = None
    phoneNumber: str
    stage: str
    stageDetail: str
    riskLevel: str
    assignedClinicianName: Optional[str] = None
    lastActivityAt: Optional[datetime] = None
    preferredFacilityName: Optional[str] = None

class TimelineItem(BaseModel):
    type: str
    isFlagged: bool
    title: str
    summary: str
    occurredAt: datetime
    sourceId: str
    actions: list[str] = []

class PregnancySummary(BaseModel):
    dueDate: date
    gestationalAge: str
    ancVisitsCompleted: int
    ancVisitsTotal: int
    lastBloodPressure: Optional[str] = None
    lastWeightKg: Optional[float] = None

class CareTeamMember(BaseModel):
    userId: uuid.UUID
    fullName: str
    role: str

class EmergencyContactInfo(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    phoneNumber: Optional[str] = None

class PatientOverview(BaseModel):
    patient: dict
    pregnancySummary: Optional[PregnancySummary] = None
    careTeam: list[CareTeamMember] = []
    emergencyContact: Optional[EmergencyContactInfo] = None
