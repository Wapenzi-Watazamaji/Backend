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
    StaffMemberRead, FacilityWithDistance, UpdateStaffRequest, BulkAssignRequest, FacilityStats
)
from app.schemas.profile import ProfileRead
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




async def get_facility_staff(db: AsyncSession, facility_id: uuid.UUID) -> list[StaffMemberRead]:
    from app.repositories import staff_repository
    from app.schemas.facility import StaffMemberRead
    
    staff_list = await staff_repository.get_by_facility(db, facility_id)
    return [StaffMemberRead.model_validate(s) for s in staff_list]


async def get_staff_member(db: AsyncSession, facility_id: uuid.UUID, staff_id: uuid.UUID) -> StaffMemberRead:
    from app.repositories import staff_repository
    staff = await staff_repository.get_by_id(db, staff_id)
    if not staff or staff.facility_id != facility_id:
        raise NotFoundError(message="Staff member not found in this facility")
    return StaffMemberRead.model_validate(staff)


async def update_staff_member(db: AsyncSession, facility_id: uuid.UUID, staff_id: uuid.UUID, req: UpdateStaffRequest) -> StaffMemberRead:
    from app.repositories import staff_repository
    staff = await staff_repository.get_by_id(db, staff_id)
    if not staff or staff.facility_id != facility_id:
        raise NotFoundError(message="Staff member not found in this facility")
    
    update_data = req.model_dump(exclude_unset=True)
    updated_staff = await staff_repository.update(db, staff, update_data)
    return StaffMemberRead.model_validate(updated_staff)


async def get_nearby_facilities(db: AsyncSession, lat: float, lng: float, radius_km: float = 50.0, limit: int = 20) -> list[FacilityWithDistance]:
    from sqlalchemy import select, func, literal_column
    from app.models.facility import Facility

    # Haversine formula for distance in km:
    # 6371 * acos(cos(radians(lat1)) * cos(radians(lat2)) * cos(radians(lon2) - radians(lon1)) + sin(radians(lat1)) * sin(radians(lat2)))
    distance_expr = (
        6371 * func.acos(
            func.cos(func.radians(lat)) * func.cos(func.radians(Facility.latitude)) *
            func.cos(func.radians(Facility.longitude) - func.radians(lng)) +
            func.sin(func.radians(lat)) * func.sin(func.radians(Facility.latitude))
        )
    ).label("distance_km")

    stmt = (
        select(Facility, distance_expr)
        .where(
            Facility.latitude.isnot(None), 
            Facility.longitude.isnot(None), 
            Facility.is_active == True,
            (
                6371 * func.acos(
                    func.cos(func.radians(lat)) * func.cos(func.radians(Facility.latitude)) *
                    func.cos(func.radians(Facility.longitude) - func.radians(lng)) +
                    func.sin(func.radians(lat)) * func.sin(func.radians(Facility.latitude))
                )
            ) <= radius_km
        )
        .order_by(distance_expr)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()
    
    nearby_facilities = []
    for facility, distance_km in rows:
        facility_dict = FacilityRead.model_validate(facility).model_dump()
        facility_dict["distance_km"] = distance_km
        nearby_facilities.append(FacilityWithDistance(**facility_dict))
        
    return nearby_facilities


async def bulk_assign_patients(db: AsyncSession, facility_id: uuid.UUID, staff_id: uuid.UUID, req: BulkAssignRequest) -> StaffMemberRead:
    from app.repositories import staff_repository
    from app.models.profile import Profile, DoctorRequestStatus
    from sqlalchemy import select
    from collections import Counter
    
    # Verify staff exists and is in the facility
    staff = await staff_repository.get_by_id(db, staff_id)
    if not staff or staff.facility_id != facility_id:
        raise NotFoundError(message="Staff member not found in this facility")
        
    # Find all profiles
    stmt = select(Profile).where(Profile.id.in_(req.patient_profile_ids))
    result = await db.execute(stmt)
    profiles = result.scalars().all()
    
    # Identify previous doctors to decrement their counts
    old_doctor_ids = [p.personal_doctor_id for p in profiles if p.personal_doctor_id is not None and p.personal_doctor_id != staff_id]
    old_doc_counts = Counter(old_doctor_ids)
    for old_doc_id, count in old_doc_counts.items():
        old_staff = await staff_repository.get_by_id(db, old_doc_id)
        if old_staff:
            old_staff.assigned_patient_count = max(0, old_staff.assigned_patient_count - count)
            db.add(old_staff)
            
    # Update the profiles
    new_assignments_count = 0
    for profile in profiles:
        if profile.personal_doctor_id != staff_id:
            profile.personal_doctor_id = staff_id
            profile.personal_doctor_request_status = DoctorRequestStatus.ASSIGNED
            new_assignments_count += 1
            db.add(profile)
            
    # Update the new staff member's count
    staff.assigned_patient_count += new_assignments_count
    db.add(staff)
    
    await db.commit()
    await db.refresh(staff)
    
    return StaffMemberRead.model_validate(staff)


async def get_staff_patients(db: AsyncSession, facility_id: uuid.UUID, staff_id: uuid.UUID) -> list[ProfileRead]:
    from app.repositories import staff_repository
    from app.models.profile import Profile
    from sqlalchemy import select
    
    # Verify staff exists and is in the facility
    staff = await staff_repository.get_by_id(db, staff_id)
    if not staff or staff.facility_id != facility_id:
        raise NotFoundError(message="Staff member not found in this facility")
        
    stmt = select(Profile).where(Profile.personal_doctor_id == staff_id)
    result = await db.execute(stmt)
    profiles = result.scalars().all()
    
    return [ProfileRead.from_orm_with_contact(p) for p in profiles]


async def get_my_patients(db: AsyncSession, facility_id: uuid.UUID, user_id: uuid.UUID) -> list[ProfileRead]:
    from app.repositories import staff_repository
    from app.models.profile import Profile
    from sqlalchemy import select
    
    staff = await staff_repository.get_by_user_and_facility(db, user_id, facility_id)
    if not staff:
        raise NotFoundError(message="Staff member record not found for the current user in this facility")
        
    stmt = select(Profile).where(Profile.personal_doctor_id == staff.id)
    result = await db.execute(stmt)
    profiles = result.scalars().all()
    
    return [ProfileRead.from_orm_with_contact(p) for p in profiles]


async def get_facility_stats(db: AsyncSession, facility_id: uuid.UUID) -> FacilityStats:
    from app.models.staff import StaffMember
    from app.models.emergency import EmergencyRequest, EmergencyStatus
    from sqlalchemy import select, func
    
    # Total staff
    stmt_staff = select(func.count(StaffMember.id)).where(StaffMember.facility_id == facility_id)
    total_staff = await db.scalar(stmt_staff) or 0
    
    # Staff on duty
    stmt_on_duty = select(func.count(StaffMember.id)).where(
        StaffMember.facility_id == facility_id, 
        StaffMember.is_on_duty == True
    )
    staff_on_duty = await db.scalar(stmt_on_duty) or 0
    
    # Total assigned patients
    stmt_patients = select(func.sum(StaffMember.assigned_patient_count)).where(StaffMember.facility_id == facility_id)
    total_assigned_patients = await db.scalar(stmt_patients) or 0
    
    # Pending emergencies
    stmt_emergencies = select(func.count(EmergencyRequest.id)).where(
        EmergencyRequest.facility_id == facility_id,
        EmergencyRequest.status == EmergencyStatus.PENDING
    )
    pending_emergencies = await db.scalar(stmt_emergencies) or 0
    
    return FacilityStats(
        total_staff=total_staff,
        staff_on_duty=staff_on_duty,
        total_assigned_patients=total_assigned_patients,
        pending_emergencies=pending_emergencies
    )
