import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from app.models.referral import ReferralReason, ReferralPriority, ReferralStatus

class ReferralCreate(BaseModel):
    patient_id: uuid.UUID
    receiving_facility_id: uuid.UUID
    reason: ReferralReason
    priority: ReferralPriority
    clinical_notes: str

class ReferralUpdate(BaseModel):
    status: ReferralStatus
    rejection_reason: Optional[str] = None

class ReferralRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    sending_facility_id: uuid.UUID
    receiving_facility_id: uuid.UUID
    reason: ReferralReason
    priority: ReferralPriority
    status: ReferralStatus
    clinical_notes: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
