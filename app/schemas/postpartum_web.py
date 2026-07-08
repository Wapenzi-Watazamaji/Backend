import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class MaternalAlert(BaseModel):
    patientUserId: uuid.UUID
    patientName: str
    dayPostpartum: int
    severity: str
    message: str
    sourceSubmissionId: Optional[uuid.UUID] = None
    createdAt: datetime

class NewbornAlert(BaseModel):
    babyId: uuid.UUID
    babyName: str
    motherName: str
    dayOfLife: int
    severity: str
    message: str
    createdAt: datetime

class PostpartumAlertsSummary(BaseModel):
    postpartumPatientCount: int
    criticalAlertCount: int
    watchAlertCount: int
    maternalAlerts: list[MaternalAlert]
    newbornAlerts: list[NewbornAlert]

class PostpartumPatientList(BaseModel):
    patientUserId: uuid.UUID
    patientName: str
    dayPostpartum: int
    babyName: Optional[str] = None
    babySex: Optional[str] = None
    status: str
    assignedClinicianName: Optional[str] = None
