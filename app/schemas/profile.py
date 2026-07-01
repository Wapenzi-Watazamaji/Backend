import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.profile import CurrentStage, SharingPreference, NotificationPreference, CompanionPreference, DoctorRequestStatus


class EmergencyContact(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    phone: Optional[str] = None


class ProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    current_stage: Optional[CurrentStage] = None
    preferred_unit_ids: Optional[list[uuid.UUID]] = None
    emergency_sharing_preference: Optional[SharingPreference] = None
    notification_preference: Optional[NotificationPreference] = None
    emergency_contact: Optional[EmergencyContact] = None
    companion_preference: Optional[CompanionPreference] = None
    personal_doctor_id: Optional[uuid.UUID] = None
    personal_doctor_request_status: Optional[DoctorRequestStatus] = None
    qr_passport_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_contact(cls, profile) -> "ProfileRead":
        return cls(
            id=profile.id,
            user_id=profile.user_id,
            current_stage=profile.current_stage,
            preferred_unit_ids=profile.preferred_unit_ids,
            emergency_sharing_preference=profile.emergency_sharing_preference,
            notification_preference=profile.notification_preference,
            emergency_contact=EmergencyContact(
                name=profile.emergency_contact_name,
                relationship=profile.emergency_contact_relationship,
                phone=profile.emergency_contact_phone,
            ) if profile.emergency_contact_name else None,
            companion_preference=profile.companion_preference,
            personal_doctor_id=profile.personal_doctor_id,
            personal_doctor_request_status=profile.personal_doctor_request_status,
            qr_passport_token=profile.qr_passport_token,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


class ProfileUpdate(BaseModel):
    current_stage: Optional[CurrentStage] = None
    emergency_sharing_preference: Optional[SharingPreference] = None
    notification_preference: Optional[NotificationPreference] = None
    emergency_contact: Optional[EmergencyContact] = None
    companion_preference: Optional[CompanionPreference] = None
    preferred_unit_ids: Optional[list[uuid.UUID]] = None


class ProfileCreate(BaseModel):
    current_stage: Optional[CurrentStage] = None
    emergency_sharing_preference: Optional[SharingPreference] = None
    notification_preference: Optional[NotificationPreference] = None
    emergency_contact: Optional[EmergencyContact] = None
    companion_preference: Optional[CompanionPreference] = None
    preferred_unit_ids: Optional[list[uuid.UUID]] = None


class PersonalDoctorRequest(BaseModel):
    facility_id: uuid.UUID
