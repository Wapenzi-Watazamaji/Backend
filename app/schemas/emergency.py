import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.emergency import EmergencyStatus

class EmergencyRequestCreate(BaseModel):
    facility_id: uuid.UUID
    location_lat: Optional[str] = None
    location_lng: Optional[str] = None
    notes: Optional[str] = None

class EmergencyRequestUpdate(BaseModel):
    status: EmergencyStatus

class EmergencyRequestRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    facility_id: uuid.UUID
    status: EmergencyStatus
    location_lat: Optional[str] = None
    location_lng: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
