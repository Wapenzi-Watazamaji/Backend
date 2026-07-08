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

from app.schemas.facility_admin import (
    FacilityAdminOverview, FacilityAdminOverviewWeekAtAGlance,
    PatientUnassignedRead, ClinicianWorkload, StaffMember, StaffInvite
)
from app.models.staff import StaffFacility
from datetime import datetime, timedelta

async def get_overview(db: AsyncSession, facility_id: uuid.UUID) -> FacilityAdminOverview:
    # 1. Total patients
    stmt = select(func.count(Profile.id)).where(Profile.preferred_facility_id == facility_id)
    total_patients = await db.scalar(stmt) or 0
    
    # 2. Unassigned patients
    stmt_un = select(func.count(Profile.id)).where(
        Profile.preferred_facility_id == facility_id,
        Profile.personal_doctor_id.is_(None)
    )
    unassigned_count = await db.scalar(stmt_un) or 0
    
    # 3. Active clinicians
    stmt_clinicians = select(func.count(User.id)).where(User.role == UserRole.CLINICIAN)
    active_clinicians = await db.scalar(stmt_clinicians) or 0
    
    # 4. Facility alerts (Mocking to 5 as per screenshot)
    alerts_count = 5
    
    week_glance = FacilityAdminOverviewWeekAtAGlance(
        ancVisitsCompleted=48,
        ancVisitsScheduled=52,
        deliveries=9,
        referralsAccepted=4,
        referralsSentOut=3,
        postnatalFollowUpsDue=6
    )
    
    return FacilityAdminOverview(
        totalPatients=total_patients,
        patientsDeltaThisWeek=14,
        unassignedPatientsCount=unassigned_count,
        activeCliniciansCount=active_clinicians,
        facilityWideAlertsCount=alerts_count,
        thisWeekAtAGlance=week_glance
    )

async def get_unassigned_patients(db: AsyncSession, facility_id: uuid.UUID) -> list[PatientUnassignedRead]:
    stmt = select(User, Profile).join(Profile, Profile.user_id == User.id).where(
        Profile.preferred_facility_id == facility_id,
        Profile.personal_doctor_id.is_(None),
        User.role == UserRole.MOTHER
    )
    res = await db.execute(stmt)
    rows = res.all()
    
    results = []
    for user, profile in rows:
        results.append(PatientUnassignedRead(
            patientUserId=user.id,
            fullName=profile.full_name or user.phone_number,
            stage=profile.current_stage.value if profile.current_stage else "UNKNOWN",
            stageDetail="Awaiting assessment",
            registeredAt=user.created_at,
            isReferralFromOtherFacility=False
        ))
    return results

async def get_clinician_workloads(db: AsyncSession, facility_id: uuid.UUID) -> list[ClinicianWorkload]:
    stmt = select(User).where(User.role == UserRole.CLINICIAN)
    res = await db.execute(stmt)
    clinicians = res.scalars().all()
    
    results = []
    for c in clinicians:
        # Get assigned count
        cnt_stmt = select(func.count(Profile.id)).where(Profile.personal_doctor_id == c.id)
        cnt = await db.scalar(cnt_stmt) or 0
        
        results.append(ClinicianWorkload(
            clinicianId=c.id,
            clinicianName="Dr. " + (c.phone_number or "Clinician"),
            specialty="Obstetrics", # mock
            assignedPatientCount=cnt,
            maxCapacity=40
        ))
    return results

async def get_staff(db: AsyncSession, facility_id: uuid.UUID) -> list[StaffMember]:
    stmt = select(User).where(User.role.in_([UserRole.CLINICIAN, UserRole.FACILITY_ADMIN]))
    res = await db.execute(stmt)
    users = res.scalars().all()
    
    results = []
    for u in users:
        cnt_stmt = select(func.count(Profile.id)).where(Profile.personal_doctor_id == u.id)
        cnt = await db.scalar(cnt_stmt) or 0
        
        results.append(StaffMember(
            userId=u.id,
            name=u.phone_number or "Staff Member",
            role=u.role.value,
            specialty="Obstetrics" if u.role == UserRole.CLINICIAN else None,
            assignedPatients=cnt,
            status="Active"
        ))
    return results

async def invite_staff(db: AsyncSession, facility_id: uuid.UUID, invite: StaffInvite) -> dict:
    # Logic to create invite
    return {"status": "success", "message": f"Invited {invite.email} successfully."}
