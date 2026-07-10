import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.utils.exceptions import APIResponse, create_success_response
from app.schemas.medical_history import (
    MedicalHistoryRecordRead, MedicalHistoryRecordCreate, MedicalHistoryRecordUpdate,
    MedicalHistoryCustomFieldRead, MedicalHistoryCustomFieldCreate
)
from app.services import medical_history_service

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
    409: {"model": APIResponse[None], "description": "Conflict"},
    422: {"model": APIResponse[None], "description": "Validation Error"},
}

@router.get(
    "/patients/{user_id}/medical-history",
    response_model=APIResponse[MedicalHistoryRecordRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get patient's medical history record",
)
async def get_patient_medical_history(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    # Could check permissions here to ensure the clinician has access to the patient
    record = await medical_history_service.get_medical_history(db, user_id)
    return create_success_response(data=record)

@router.post(
    "/patients/{user_id}/medical-history",
    response_model=APIResponse[MedicalHistoryRecordRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Create patient's medical history record",
)
async def create_patient_medical_history(
    user_id: uuid.UUID,
    data_in: MedicalHistoryRecordCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    record = await medical_history_service.create_medical_history(db, user_id, current_user.id, data_in)
    return create_success_response(data=record)

@router.put(
    "/patients/{user_id}/medical-history",
    response_model=APIResponse[MedicalHistoryRecordRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Update patient's medical history record",
)
async def update_patient_medical_history(
    user_id: uuid.UUID,
    data_in: MedicalHistoryRecordUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    record = await medical_history_service.update_medical_history(db, user_id, current_user.id, data_in)
    return create_success_response(data=record)

@router.get(
    "/facility/medical-history-fields",
    response_model=APIResponse[list[MedicalHistoryCustomFieldRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List medical history custom fields for facility",
)
async def get_facility_medical_history_fields(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    fields = await medical_history_service.get_custom_fields(db, facility_id)
    return create_success_response(data=fields)

@router.post(
    "/facility/medical-history-fields",
    response_model=APIResponse[MedicalHistoryCustomFieldRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Define a new medical history custom field",
)
async def create_facility_medical_history_field(
    data_in: MedicalHistoryCustomFieldCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    field = await medical_history_service.create_custom_field(db, facility_id, current_user.id, data_in)
    return create_success_response(data=field)

@router.get(
    "/profile/medical-history",
    response_model=APIResponse[MedicalHistoryRecordRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get my medical history (Patient)",
)
async def get_my_medical_history(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    record = await medical_history_service.get_medical_history(db, current_user.id)
    return create_success_response(data=record)
