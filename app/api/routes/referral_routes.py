import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_current_user, require_roles, get_facility_context
from app.models.user import User, UserRole
from app.schemas.referral import ReferralCreate, ReferralUpdate, ReferralRead
from app.services import referral_service
from app.utils.exceptions import APIResponse, create_success_response

router = APIRouter(prefix="/referrals", tags=["Referrals"])

@router.post("", response_model=APIResponse[ReferralRead])
async def create_referral(
    req: ReferralCreate,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_roles(UserRole.CLINICIAN, UserRole.FACILITY_ADMIN)),
    db: AsyncSession = Depends(get_session)
):
    referral = await referral_service.create_referral(db, requester_facility_id, req)
    return create_success_response(message="Referral created successfully", data=referral)

@router.get("/inbox", response_model=APIResponse[list[ReferralRead]])
async def get_referral_inbox(
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_roles(UserRole.CLINICIAN, UserRole.FACILITY_ADMIN)),
    db: AsyncSession = Depends(get_session)
):
    referrals = await referral_service.get_facility_inbox(db, requester_facility_id)
    return create_success_response(message="Inbox fetched successfully", data=referrals)

@router.get("/outbox", response_model=APIResponse[list[ReferralRead]])
async def get_referral_outbox(
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_roles(UserRole.CLINICIAN, UserRole.FACILITY_ADMIN)),
    db: AsyncSession = Depends(get_session)
):
    referrals = await referral_service.get_facility_outbox(db, requester_facility_id)
    return create_success_response(message="Outbox fetched successfully", data=referrals)

@router.put("/{referral_id}", response_model=APIResponse[ReferralRead])
async def update_referral(
    referral_id: uuid.UUID,
    req: ReferralUpdate,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_roles(UserRole.CLINICIAN, UserRole.FACILITY_ADMIN)),
    db: AsyncSession = Depends(get_session)
):
    referral = await referral_service.update_referral_status(db, referral_id, requester_facility_id, req)
    return create_success_response(message="Referral updated successfully", data=referral)

@router.post("/{referral_id}/request-records-access", response_model=APIResponse[dict])
async def request_records_access(
    referral_id: uuid.UUID,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_roles(UserRole.CLINICIAN, UserRole.FACILITY_ADMIN)),
    db: AsyncSession = Depends(get_session)
):
    result = await referral_service.request_records_access(db, referral_id, requester_facility_id)
    return create_success_response(message=result["message"], data=result)
