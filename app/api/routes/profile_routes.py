from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_dep as get_db
from app.models.user import User
from app.schemas.profile import ProfileRead, ProfileCreate, ProfileUpdate, PersonalDoctorRequest
from app.services import profile_service
from app.utils.exceptions import APIResponse, create_success_response

router = APIRouter()


@router.post("/me", response_model=APIResponse[ProfileRead], status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_in: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await profile_service.create_profile(db, current_user, profile_in)
    return create_success_response(message="Profile created successfully", data=profile)


@router.get("/me", response_model=APIResponse[ProfileRead])
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await profile_service.get_my_profile(db, current_user)
    return create_success_response(message="Profile fetched successfully", data=profile)


@router.put("/me", response_model=APIResponse[ProfileRead])
async def update_my_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await profile_service.update_my_profile(db, current_user, profile_in)
    return create_success_response(message="Profile updated successfully", data=profile)


@router.get("/me/qr", response_model=APIResponse[dict])
async def get_qr_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await profile_service.get_or_refresh_qr_token(db, current_user, refresh=False)
    return create_success_response(message="QR passport token retrieved", data=data)


@router.post("/me/qr/refresh", response_model=APIResponse[dict])
async def refresh_qr_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await profile_service.get_or_refresh_qr_token(db, current_user, refresh=True)
    return create_success_response(message="QR passport token refreshed successfully", data=data)


@router.post("/me/personal-doctor-request", response_model=APIResponse[ProfileRead])
async def request_personal_doctor(
    body: PersonalDoctorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await profile_service.request_personal_doctor(db, current_user, body.facility_id)
    return create_success_response(message="Personal doctor request submitted successfully", data=profile)

from app.services import consent_service
from app.schemas.consent import ConsentRead

@router.get("/me/consents", response_model=APIResponse[list[ConsentRead]])
async def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    consents = await consent_service.get_my_consents(db, current_user.id)
    return create_success_response(message="Consents fetched successfully", data=consents)

@router.put("/me/consents/{grantee_id}/revoke", response_model=APIResponse[ConsentRead])
async def revoke_consent(
    grantee_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    consent = await consent_service.revoke_consent(db, current_user.id, grantee_id)
    return create_success_response(message="Consent revoked successfully", data=consent)
