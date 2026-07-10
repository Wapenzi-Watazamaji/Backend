import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from app.models.medical_history import FieldType

class MedicationItem(BaseModel):
    name: str
    dose: str
    frequency: str

class SurgicalHistoryItem(BaseModel):
    procedure: str
    year: str

class MedicalHistoryCustomFieldBase(BaseModel):
    key: str
    label: str
    type: FieldType
    options: Optional[List[str]] = None

class MedicalHistoryCustomFieldCreate(MedicalHistoryCustomFieldBase):
    pass

class MedicalHistoryCustomFieldRead(MedicalHistoryCustomFieldBase):
    id: uuid.UUID
    facility_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MedicalHistoryRecordBase(BaseModel):
    blood_type: Optional[str] = None
    rh_factor: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    current_medications: Optional[List[MedicationItem]] = None
    surgical_history: Optional[List[SurgicalHistoryItem]] = None
    previous_pregnancies: int = 0
    previous_outcomes: Optional[List[str]] = None
    family_history: Optional[List[str]] = None
    custom_fields: Optional[dict[str, Any]] = None

class MedicalHistoryRecordCreate(MedicalHistoryRecordBase):
    pass

class MedicalHistoryRecordUpdate(MedicalHistoryRecordBase):
    pass

class MedicalHistoryRecordRead(MedicalHistoryRecordBase):
    id: uuid.UUID
    patient_user_id: uuid.UUID
    created_by: uuid.UUID
    last_updated_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
