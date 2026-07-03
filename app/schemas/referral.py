import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.referral import ReferralReason, ReferralStatus


class ReferralCreate(BaseModel):
    toFacilityId: uuid.UUID
    fromFacilityId: uuid.UUID
    reason: ReferralReason
    notes: Optional[str] = None
    isEmergency: bool = False
    offlineQueued: bool = False
    clientCreatedAt: Optional[datetime] = None


class ReferralRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    to_facility_id: uuid.UUID
    from_facility_id: uuid.UUID
    reason: ReferralReason
    notes: Optional[str] = None
    is_emergency: bool
    status: ReferralStatus
    rejection_reason: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReferralRejectRequest(BaseModel):
    reason: str


class ReferralPatientSummary(BaseModel):
    patient: dict
    gestationalAgeWeeks: Optional[int] = None
    activeRiskFlags: list[str]
    reasonForVisit: str
    recentVitals: Optional[dict] = None
    allergies: list[str]
    emergencyContact: Optional[dict] = None
