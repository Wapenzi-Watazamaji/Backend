import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.labour import (
    LabourSessionStatus, LabourOutcome, LabourDeliveryType,
    LabourReadingType, AlertType, AlertSeverity,
)


class LabourSessionCreate(BaseModel):
    pregnancyId: uuid.UUID
    facilityId: uuid.UUID
    activeLabourStartedAt: datetime


class LabourSessionClose(BaseModel):
    closedAt: datetime
    outcome: LabourOutcome
    deliveryType: LabourDeliveryType


class LabourSessionRead(BaseModel):
    id: uuid.UUID
    pregnancy_id: uuid.UUID
    facility_id: uuid.UUID
    clinician_id: uuid.UUID
    active_labour_started_at: datetime
    status: LabourSessionStatus
    outcome: Optional[LabourOutcome] = None
    delivery_type: Optional[LabourDeliveryType] = None
    closed_at: Optional[datetime] = None
    room: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LabourSessionRoomUpdate(BaseModel):
    room: str


class ActiveLabourSessionRead(BaseModel):
    id: uuid.UUID
    patientName: str
    room: Optional[str] = None
    hoursInLabour: float
    dilationCm: Optional[float] = None
    fhr: Optional[float] = None
    status: str
    assignedClinicianName: Optional[str] = None


class LabourAlertsSummary(BaseModel):
    activeLabourCount: int
    criticalAlertCount: int
    watchAlertCount: int
    recentAlerts: list['LabourAlertRead']



class DilationReadingCreate(BaseModel):
    value: float
    recordedAt: datetime


class FhrReadingCreate(BaseModel):
    value: float
    recordedAt: datetime


class MaternalBpReadingCreate(BaseModel):
    bloodPressureSystolic: int
    bloodPressureDiastolic: int
    recordedAt: datetime


class ContractionReadingCreate(BaseModel):
    frequencyPer10Min: int
    durationSeconds: int
    recordedAt: datetime


class LabourReadingRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    type: LabourReadingType
    value: Optional[float] = None
    meta: Optional[dict] = None
    recorded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class PartographDilationPoint(BaseModel):
    hoursElapsed: float
    value: float
    recordedAt: datetime


class PartographFhrPoint(BaseModel):
    hoursElapsed: float
    value: float
    recordedAt: datetime


class PartographAlertLine(BaseModel):
    startHour: float
    startCm: float
    slopeCmPerHour: float


class PartographRead(BaseModel):
    dilationReadings: list[PartographDilationPoint]
    fhrReadings: list[PartographFhrPoint]
    alertLine: PartographAlertLine
    actionLine: PartographAlertLine
    hasAlertLineCrossed: bool
    hasActionLineCrossed: bool


class LabourAlertRead(BaseModel):
    id: uuid.UUID
    type: AlertType
    severity: AlertSeverity
    message: str
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AcknowledgeAlertResponse(BaseModel):
    id: uuid.UUID
    acknowledged_at: datetime

    model_config = {"from_attributes": True}


class EscalateAlertRequest(BaseModel):
    escalateTo: str


class ResuscitationStepRead(BaseModel):
    order: int
    title: str
    timerSeconds: Optional[int] = None
    instructions: Optional[str] = None


class ResuscitationProtocolRead(BaseModel):
    steps: list[ResuscitationStepRead]


class ResuscitationLogCreate(BaseModel):
    stepOrder: int
    completedAt: datetime
    vitalsAtStep: Optional[dict] = None


class ResuscitationLogRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    step_order: int
    completed_at: datetime
    vitals_at_step: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}
