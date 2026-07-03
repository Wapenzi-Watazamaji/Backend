import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.models.referral import ReferralStatus
from app.schemas.referral import (
    ReferralCreate, ReferralRead, ReferralRejectRequest, ReferralPatientSummary,
)
from app.services import referral_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
    422: {"model": APIResponse[None], "description": "Validation Error"},
}


@router.post(
    "",
    response_model=APIResponse[ReferralRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Create a referral or emergency request",
)
async def create_referral(
    data: ReferralCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    referral = await referral_service.create_referral(db, current_user.id, data)
    return create_success_response(data=referral)


@router.get(
    "/{referral_id}",
    response_model=APIResponse[ReferralRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get a referral by ID",
)
async def get_referral(
    referral_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    referral = await referral_service.get_referral(db, referral_id)
    return create_success_response(data=referral)


@router.get(
    "",
    response_model=APIResponse[list[ReferralRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List referrals with optional filters",
)
async def list_referrals(
    status: Optional[ReferralStatus] = Query(None),
    facilityId: Optional[uuid.UUID] = Query(None),
    direction: Optional[str] = Query(None, description="INCOMING or OUTGOING"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    referrals = await referral_service.list_referrals(
        db,
        facility_id=facilityId,
        status=status,
        direction=direction,
        page=page,
        page_size=pageSize,
    )
    return create_success_response(data=referrals)


@router.put(
    "/{referral_id}/accept",
    response_model=APIResponse[ReferralRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Accept a referral",
)
async def accept_referral(
    referral_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    referral = await referral_service.accept_referral(db, referral_id)
    return create_success_response(data=referral)


@router.put(
    "/{referral_id}/reject",
    response_model=APIResponse[ReferralRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Reject a referral",
)
async def reject_referral(
    referral_id: uuid.UUID,
    data: ReferralRejectRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    referral = await referral_service.reject_referral(db, referral_id, data)
    return create_success_response(data=referral)


@router.put(
    "/{referral_id}/complete",
    response_model=APIResponse[ReferralRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Mark a referral as completed",
)
async def complete_referral(
    referral_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    referral = await referral_service.complete_referral(db, referral_id)
    return create_success_response(data=referral)


@router.get(
    "/{referral_id}/patient-summary",
    response_model=APIResponse[ReferralPatientSummary],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get the condensed patient summary for a referral",
)
async def get_patient_summary(
    referral_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    summary = await referral_service.get_patient_summary(db, referral_id)
    return create_success_response(data=summary)
