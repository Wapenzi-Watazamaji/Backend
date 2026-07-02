import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_dep as get_db, get_facility_context, require_facility_admin, require_clinician
from app.models.user import User
from app.schemas.facility import (
    FacilityRegisterRequest, FacilityRegisterResponse,
    FacilityRead, FacilityUpdate, StaffMemberRead, AddStaffRequest,
    FacilityWithDistance, UpdateStaffRequest, BulkAssignRequest, FacilityStats
)
from app.schemas.profile import ProfileRead
from app.services import facility_service
from app.utils.exceptions import APIResponse, create_success_response

router = APIRouter()


@router.post("/register", response_model=APIResponse[FacilityRegisterResponse], status_code=status.HTTP_201_CREATED)
async def register_facility(
    req: FacilityRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await facility_service.register_facility(db, req)
    return create_success_response(message="Facility registered successfully", data=result)


@router.get("/nearby", response_model=APIResponse[list[FacilityWithDistance]])
async def get_nearby_facilities(
    lat: float,
    lng: float,
    radius_km: float = 50.0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facilities = await facility_service.get_nearby_facilities(db, lat, lng, radius_km, limit)
    return create_success_response(message="Nearby facilities fetched successfully", data=facilities)


@router.get("/current", response_model=APIResponse[FacilityRead])
async def get_facility(
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facility = await facility_service.get_facility(db, requester_facility_id)
    return create_success_response(message="Facility fetched successfully", data=facility)


@router.put("/current", response_model=APIResponse[FacilityRead])
async def update_facility(
    update_in: FacilityUpdate,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_facility_admin),
    db: AsyncSession = Depends(get_db),
):
    facility = await facility_service.update_facility(db, requester_facility_id, update_in)
    return create_success_response(message="Facility updated successfully", data=facility)


@router.get("/current/stats", response_model=APIResponse[FacilityStats])
async def get_facility_stats(
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_facility_admin),
    db: AsyncSession = Depends(get_db),
):
    stats = await facility_service.get_facility_stats(db, requester_facility_id)
    return create_success_response(message="Facility stats fetched successfully", data=stats)


@router.post("/staff", response_model=APIResponse[StaffMemberRead])
async def add_staff_member(
    req: AddStaffRequest,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_facility_admin),
    db: AsyncSession = Depends(get_db),
):
    staff = await facility_service.add_staff_member(db, requester_facility_id, req)
    return create_success_response(message="Staff member added successfully", data=staff)


@router.get("/staff", response_model=APIResponse[list[StaffMemberRead]])
async def get_facility_staff(
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_facility_admin),
    db: AsyncSession = Depends(get_db),
):
    staff_list = await facility_service.get_facility_staff(db, requester_facility_id)
    return create_success_response(message="Staff list fetched successfully", data=staff_list)


@router.get("/staff/{staff_id}", response_model=APIResponse[StaffMemberRead])
async def get_staff_member(
    staff_id: uuid.UUID,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_facility_admin),
    db: AsyncSession = Depends(get_db),
):
    staff = await facility_service.get_staff_member(db, requester_facility_id, staff_id)
    return create_success_response(message="Staff member fetched successfully", data=staff)


@router.put("/staff/{staff_id}", response_model=APIResponse[StaffMemberRead])
async def update_staff_member(
    staff_id: uuid.UUID,
    req: UpdateStaffRequest,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_facility_admin),
    db: AsyncSession = Depends(get_db),
):
    staff = await facility_service.update_staff_member(db, requester_facility_id, staff_id, req)
    return create_success_response(message="Staff member updated successfully", data=staff)


@router.post("/staff/{staff_id}/assign-patients", response_model=APIResponse[StaffMemberRead])
async def bulk_assign_patients(
    staff_id: uuid.UUID,
    req: BulkAssignRequest,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_facility_admin),
    db: AsyncSession = Depends(get_db),
):
    staff = await facility_service.bulk_assign_patients(db, requester_facility_id, staff_id, req)
    return create_success_response(message="Patients assigned successfully", data=staff)


@router.get("/staff/{staff_id}/patients", response_model=APIResponse[list[ProfileRead]])
async def get_staff_patients(
    staff_id: uuid.UUID,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_facility_admin),
    db: AsyncSession = Depends(get_db),
):
    patients = await facility_service.get_staff_patients(db, requester_facility_id, staff_id)
    return create_success_response(message="Assigned patients fetched successfully", data=patients)


@router.get("/clinician/my-patients", response_model=APIResponse[list[ProfileRead]])
async def get_my_patients(
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
):
    patients = await facility_service.get_my_patients(db, requester_facility_id, current_user.id)
    return create_success_response(message="My assigned patients fetched successfully", data=patients)
