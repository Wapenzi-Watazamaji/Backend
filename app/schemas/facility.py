import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

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


class FacilityWithDistance(FacilityRead):
    distance_km: float


class FacilityCreate(BaseModel):
    name: str
    type: FacilityType
    county: str
    address: str
    phone_number: str
    email: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude must be between -90 and 90")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude must be between -180 and 180")
    services_offered: Optional[list[str]] = []
    readiness: Optional[dict] = {}


class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    county: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude must be between -90 and 90")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude must be between -180 and 180")
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
    is_on_duty: bool
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


class UpdateStaffRequest(BaseModel):
    role: Optional[StaffRole] = None
    specialty: Optional[str] = None
    status: Optional[StaffStatus] = None
    is_on_duty: Optional[bool] = None


class BulkAssignRequest(BaseModel):
    patient_profile_ids: list[uuid.UUID]


class FacilityRegisterResponse(BaseModel):
    facility: FacilityRead
    admin_user_id: uuid.UUID
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class FacilityStats(BaseModel):
    total_staff: int
    staff_on_duty: int
    total_assigned_patients: int
    pending_emergencies: int
