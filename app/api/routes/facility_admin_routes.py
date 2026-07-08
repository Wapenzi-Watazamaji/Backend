import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.models.user import User
from app.schemas.facility_admin import BulkAssignRequest
from app.schemas.user import UserCreateSmsOnly, UserRead
from app.services import facility_admin_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
}

@router.post(
    "/enroll-patient", 
    response_model=APIResponse[UserRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Enroll patient manually via SMS"
)
async def enroll_patient(
    user_in: UserCreateSmsOnly,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    user = await facility_admin_service.enroll_patient_manually(db, facility_id, current_user.id, user_in)
    return create_success_response(data=user)

@router.post(
    "/bulk-reassign", 
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Bulk reassign patients to a clinician"
)
async def bulk_reassign(
    req: BulkAssignRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    count = await facility_admin_service.bulk_reassign_patients(db, facility_id, req)
    return create_success_response(data={"status": "success", "reassignedCount": count})

from app.schemas.facility_admin import (
    FacilityAdminOverview, PatientUnassignedRead, 
    ClinicianWorkload, StaffMember, StaffInvite
)
from typing import List

@router.get(
    "/overview",
    response_model=APIResponse[FacilityAdminOverview],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get facility admin overview dashboard stats"
)
async def get_overview(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    overview = await facility_admin_service.get_overview(db, facility_id)
    return create_success_response(data=overview)

@router.get(
    "/unassigned-patients",
    response_model=APIResponse[List[PatientUnassignedRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List unassigned patients"
)
async def get_unassigned_patients(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    patients = await facility_admin_service.get_unassigned_patients(db, facility_id)
    return create_success_response(data=patients)

@router.get(
    "/clinician-workloads",
    response_model=APIResponse[List[ClinicianWorkload]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List clinicians and their workloads"
)
async def get_clinician_workloads(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    workloads = await facility_admin_service.get_clinician_workloads(db, facility_id)
    return create_success_response(data=workloads)

@router.get(
    "/staff",
    response_model=APIResponse[List[StaffMember]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List facility staff"
)
async def get_staff(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    staff = await facility_admin_service.get_staff(db, facility_id)
    return create_success_response(data=staff)

@router.post(
    "/invite-staff",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Invite new staff member"
)
async def invite_staff(
    invite: StaffInvite,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    res = await facility_admin_service.invite_staff(db, facility_id, invite)
    return create_success_response(data=res)

from app.schemas.dashboard import PatientDirectoryItem

@router.get(
    "/patients",
    response_model=APIResponse[List[PatientDirectoryItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get facility wide patient directory"
)
async def get_patients(
    search: Optional[str] = None,
    tab: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    patients = await facility_admin_service.get_facility_patients(db, facility_id, search, tab)
    return create_success_response(data=patients)