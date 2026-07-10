import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.models.user import User
from app.schemas.facility_admin import (
    BulkAssignRequest,
    FacilityAdminOverview,
    PatientUnassignedRead,
    ClinicianWorkload,
    StaffMember,
    StaffInvite,
    StaffCapacityUpdate,
    AssignClinicianRequest,
)
from app.schemas.user import UserCreateSmsOnly, UserRead
from app.schemas.dashboard import PatientDirectoryItem
from app.services import facility_admin_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
}


# ---------------------------------------------------------------------------
# Patient enrollment & assignment
# ---------------------------------------------------------------------------

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


@router.put(
    "/patients/{patient_user_id}/assign-clinician",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Assign a single patient to a specific clinician"
)
async def assign_patient_to_clinician(
    patient_user_id: uuid.UUID,
    body: AssignClinicianRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    res = await facility_admin_service.assign_patient_to_clinician(
        db, facility_id, patient_user_id, body.clinicianId
    )
    return create_success_response(data=res)


@router.get(
    "/patients",
    response_model=APIResponse[List[PatientDirectoryItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get facility-wide patient directory"
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


# ---------------------------------------------------------------------------
# Admin overview / analytics
# ---------------------------------------------------------------------------

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
    "/clinician-workloads",
    response_model=APIResponse[List[ClinicianWorkload]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List clinicians and their patient workloads"
)
async def get_clinician_workloads(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    workloads = await facility_admin_service.get_clinician_workloads(db, facility_id)
    return create_success_response(data=workloads)


# ---------------------------------------------------------------------------
# Staff management
# ---------------------------------------------------------------------------

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
    "/register-staff",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Manually register a new staff member"
)
async def invite_staff(
    invite: StaffInvite,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    res = await facility_admin_service.invite_staff(db, facility_id, invite)
    return create_success_response(data=res)


@router.post(
    "/staff/{staff_id}/resend-invite",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Resend invite to a pending staff member"
)
async def resend_staff_invite(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    res = await facility_admin_service.resend_invite(db, facility_id, staff_id)
    return create_success_response(data=res)


@router.put(
    "/staff/{staff_id}/capacity",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Update a staff member's patient capacity cap"
)
async def update_staff_capacity(
    staff_id: uuid.UUID,
    body: StaffCapacityUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    res = await facility_admin_service.update_staff_capacity(db, facility_id, staff_id, body.capacity)
    return create_success_response(data=res)


@router.put(
    "/staff/{staff_id}/deactivate",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Deactivate a staff member"
)
async def deactivate_staff(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_facility_admin),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    res = await facility_admin_service.deactivate_staff(db, facility_id, staff_id)
    return create_success_response(data=res)