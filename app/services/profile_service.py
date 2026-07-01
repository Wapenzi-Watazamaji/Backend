import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.profile import DoctorRequestStatus
from app.repositories import profile_repository, facility_repository
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileRead
from app.utils.exceptions import NotFoundError, PhoneAlreadyRegisteredError, ValidationError


async def create_profile(db: AsyncSession, user: User, profile_in: ProfileCreate) -> ProfileRead:
    existing = await profile_repository.get_by_user_id(db, user.id)
    if existing:
        raise ValidationError(message="Profile already exists. Use PUT /profile/me to update it.")

    profile = await profile_repository.create(db, user.id)

    update_data = profile_in.model_dump(exclude_unset=True)
    
    if "preferred_facility_id" in update_data and update_data["preferred_facility_id"]:
        facility = await facility_repository.get_by_id(db, update_data["preferred_facility_id"])
        if not facility:
            raise NotFoundError(message="The specified preferred facility does not exist")

    update_data = _flatten_emergency_contact(update_data)

    if update_data:
        profile = await profile_repository.update(db, profile, update_data)

    return ProfileRead.from_orm_with_contact(profile)


async def get_my_profile(db: AsyncSession, user: User) -> ProfileRead:
    profile = await profile_repository.get_by_user_id(db, user.id)
    if not profile:
        profile = await profile_repository.create(db, user.id)
    return ProfileRead.from_orm_with_contact(profile)


def _flatten_emergency_contact(data: dict) -> dict:
    if "emergency_contact" in data and data["emergency_contact"] is not None:
        ec = data.pop("emergency_contact")
        data["emergency_contact_name"] = ec.get("name")
        data["emergency_contact_relationship"] = ec.get("relationship")
        data["emergency_contact_phone"] = ec.get("phone")
    elif "emergency_contact" in data and data["emergency_contact"] is None:
        data.pop("emergency_contact")
        data["emergency_contact_name"] = None
        data["emergency_contact_relationship"] = None
        data["emergency_contact_phone"] = None
    return data


async def update_my_profile(db: AsyncSession, user: User, profile_in: ProfileUpdate) -> ProfileRead:
    profile = await profile_repository.get_by_user_id(db, user.id)
    if not profile:
        profile = await profile_repository.create(db, user.id)

    update_data = profile_in.model_dump(exclude_unset=True)
    
    if "preferred_facility_id" in update_data and update_data["preferred_facility_id"]:
        new_facility_id = update_data["preferred_facility_id"]
        # Only validate if it's actually changing
        if profile.preferred_facility_id != new_facility_id:
            facility = await facility_repository.get_by_id(db, new_facility_id)
            if not facility:
                raise NotFoundError(message="The specified preferred facility does not exist")
            
    update_data = _flatten_emergency_contact(update_data)
    profile = await profile_repository.update(db, profile, update_data)
    return ProfileRead.from_orm_with_contact(profile)


async def get_or_refresh_qr_token(db: AsyncSession, user: User, refresh: bool = False) -> dict:
    profile = await profile_repository.get_by_user_id(db, user.id)
    if not profile:
        profile = await profile_repository.create(db, user.id)

    if not profile.qr_passport_token or refresh:
        profile = await profile_repository.generate_qr_token(db, profile)

    return {"qr_passport_token": profile.qr_passport_token}


async def request_personal_doctor(db: AsyncSession, user: User, facility_id: uuid.UUID) -> ProfileRead:
    facility = await facility_repository.get_by_id(db, facility_id)
    if not facility:
        raise NotFoundError(message="The specified facility does not exist")

    profile = await profile_repository.get_by_user_id(db, user.id)
    if not profile:
        profile = await profile_repository.create(db, user.id)

    profile = await profile_repository.update(db, profile, {
        "personal_doctor_request_status": DoctorRequestStatus.PENDING,
    })
    return ProfileRead.from_orm_with_contact(profile)
