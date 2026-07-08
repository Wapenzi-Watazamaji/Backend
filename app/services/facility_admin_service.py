import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User, UserRole
from app.models.profile import Profile
from app.schemas.facility_admin import BulkAssignRequest
from app.schemas.user import UserCreateSmsOnly


async def enroll_patient_manually(db: AsyncSession, facility_id: uuid.UUID, clinician_id: uuid.UUID, user_in: UserCreateSmsOnly) -> User:
    from app.services.user_service import register_sms_only
    new_user = await register_sms_only(db, user_in)
    
    stmt = select(Profile).where(Profile.user_id == new_user.id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    
    if profile:
        profile.preferred_facility_id = facility_id
        profile.personal_doctor_id = clinician_id
    else:
        profile = Profile(
            user_id=new_user.id,
            preferred_facility_id=facility_id,
            personal_doctor_id=clinician_id
        )
        db.add(profile)
        
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def bulk_reassign_patients(db: AsyncSession, facility_id: uuid.UUID, req: BulkAssignRequest) -> int:
    stmt = (
        update(Profile)
        .where(
            Profile.user_id.in_(req.patientUserIds),
            Profile.preferred_facility_id == facility_id
        )
        .values(personal_doctor_id=req.clinicianId)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
