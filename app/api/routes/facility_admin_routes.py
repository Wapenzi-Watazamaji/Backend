import uuid

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
