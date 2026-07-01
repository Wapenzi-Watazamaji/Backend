import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.facility import FacilityType, FacilityStatus
from app.models.staff import StaffRole, StaffStatus


class FacilityRead(BaseModel):
    id: uuid.UUID
    name: str
    type: FacilityType
    county: str
    address: str
    phone_number: str
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: FacilityStatus
    is_active: bool
    services_offered: list[str]
    readiness: dict
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FacilityCreate(BaseModel):
    name: str
    type: FacilityType
    county: str
    address: str
    phone_number: str
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    services_offered: Optional[list[str]] = []
    readiness: Optional[dict] = {}


class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    county: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    services_offered: Optional[list[str]] = None
    readiness: Optional[dict] = None


class AdminAccountCreate(BaseModel):
    full_name: str
    phone_number: str
    email: Optional[str] = None
    password: str


class FacilityRegisterRequest(BaseModel):
    facility: FacilityCreate
    admin_account: AdminAccountCreate


class StaffMemberRead(BaseModel):
    id: uuid.UUID
    facility_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    role: StaffRole
    specialty: Optional[str] = None
    assigned_patient_count: int
    status: StaffStatus
    invited_at: datetime
    joined_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StaffMembership(BaseModel):
    facility_id: uuid.UUID
    facility_name: str
    role: StaffRole
    status: StaffStatus


class AddStaffRequest(BaseModel):
    phone_number: str
    role: StaffRole
    specialty: Optional[str] = None


class FacilityRegisterResponse(BaseModel):
    facility: FacilityRead
    admin_user_id: uuid.UUID
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
