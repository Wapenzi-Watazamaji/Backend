import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole, AccountType
from app.models.staff import StaffMember, StaffRole, StaffStatus
from app.models.facility import FacilityStatus
from app.repositories import facility_repository, user_repository
from app.schemas.facility import (
    FacilityCreate, FacilityUpdate, FacilityRead,
    FacilityRegisterRequest, FacilityRegisterResponse, StaffMembership, AddStaffRequest,
    StaffMemberRead
)
from app.core.security import get_password_hash, create_access_token, create_refresh_token
from app.utils.exceptions import ValidationError, PhoneAlreadyRegisteredError, NotFoundError, ForbiddenError


async def register_facility(db: AsyncSession, req: FacilityRegisterRequest) -> FacilityRegisterResponse:
    # Check for duplicate phone on the admin account
    existing_user = await user_repository.get_by_phone_number(db, req.admin_account.phone_number)
    if existing_user:
        raise PhoneAlreadyRegisteredError(
            message="A user with this phone number already exists",
            fields={"phone_number": "Already in use"}
        )

    # Check for duplicate facility email
    if req.facility.email:
        existing_facility = await facility_repository.get_by_email(db, req.facility.email)
        if existing_facility:
            raise ValidationError(
                message="A facility with this email is already registered",
                fields={"email": "Already in use"}
            )

    # Create facility
    facility_data = req.facility.model_dump()
    facility_data["status"] = FacilityStatus.PENDING_VERIFICATION
    facility = await facility_repository.create(db, facility_data)

    # Create admin user
    user_data = {
        "phone_number": req.admin_account.phone_number,
        "full_name": req.admin_account.full_name,
        "role": UserRole.FACILITY_ADMIN,
        "account_type": AccountType.FULL,
        "password_hash": get_password_hash(req.admin_account.password),
    }
    admin_user = await user_repository.create(db, user_data)

    # Create staff membership linking user to facility
    staff = StaffMember(
        facility_id=facility.id,
        user_id=admin_user.id,
        role=StaffRole.FACILITY_ADMIN,
        status=StaffStatus.ACTIVE,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(staff)
    await db.flush()

    access_token = create_access_token(subject=str(admin_user.id))
    refresh_token = create_refresh_token(subject=str(admin_user.id))

    return FacilityRegisterResponse(
        facility=FacilityRead.model_validate(facility),
        admin_user_id=admin_user.id,
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def get_facility(db: AsyncSession, facility_id: uuid.UUID) -> FacilityRead:
    facility = await facility_repository.get_by_id(db, facility_id)
    if not facility:
        raise NotFoundError(message="Facility not found")
    return FacilityRead.model_validate(facility)


async def update_facility(db: AsyncSession, facility_id: uuid.UUID, update_in: FacilityUpdate) -> FacilityRead:
    facility = await facility_repository.get_by_id(db, facility_id)
    if not facility:
        raise NotFoundError(message="Facility not found")
    updated = await facility_repository.update(db, facility, update_in.model_dump(exclude_unset=True))
    return FacilityRead.model_validate(updated)


async def get_staff_memberships(db: AsyncSession, user_id: uuid.UUID) -> list[StaffMembership]:
    from sqlalchemy import select
    from app.models.staff import StaffMember
    from app.models.facility import Facility

    result = await db.execute(
        select(StaffMember, Facility)
        .join(Facility, StaffMember.facility_id == Facility.id)
        .where(StaffMember.user_id == user_id, StaffMember.status == StaffStatus.ACTIVE)
    )
    rows = result.all()
    return [
        StaffMembership(
            facility_id=staff.facility_id,
            facility_name=facility.name,
            role=staff.role,
            status=staff.status,
        )
        for staff, facility in rows
    ]


async def add_staff_member(db: AsyncSession, facility_id: uuid.UUID, req: AddStaffRequest) -> StaffMemberRead:
    facility = await facility_repository.get_by_id(db, facility_id)
    if not facility:
        raise NotFoundError(message="Facility not found")

    from app.repositories import staff_repository
    
    # See if the user exists
    user = await user_repository.get_by_phone_number(db, req.phone_number)
    
    # Check if they are already staff here
    if user:
        existing_staff = await staff_repository.get_by_user_and_facility(db, user.id, facility_id)
        if existing_staff:
            raise ValidationError(
                message="This user is already a staff member at this facility",
                fields={"phone_number": "Already a staff member"}
            )
            
    # Create staff record
    # If user doesn't exist yet, user_id will be None. The frontend or SMS system can invite them to sign up.
    staff_data = {
        "facility_id": facility_id,
        "user_id": user.id if user else None,
        "role": req.role,
        "specialty": req.specialty,
        "status": StaffStatus.ACTIVE if user else StaffStatus.INVITE_PENDING,
        "joined_at": datetime.now(timezone.utc) if user else None,
        "invited_at": datetime.now(timezone.utc)
    }
    
    staff = await staff_repository.create(db, staff_data)
    
    from app.schemas.facility import StaffMemberRead
    return StaffMemberRead.model_validate(staff)


async def get_facility_staff(db: AsyncSession, facility_id: uuid.UUID) -> list[StaffMemberRead]:
    from app.repositories import staff_repository
    from app.schemas.facility import StaffMemberRead
    
    staff_list = await staff_repository.get_by_facility(db, facility_id)
    return [StaffMemberRead.model_validate(s) for s in staff_list]
