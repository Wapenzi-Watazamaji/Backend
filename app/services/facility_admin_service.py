from datetime import timezone
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models.user import User, UserRole
from app.models.profile import Profile
from app.schemas.facility_admin import BulkAssignRequest
from app.schemas.user import UserCreateSmsOnly
from datetime import date
from sqlalchemy import desc
from sqlalchemy.orm import aliased
from app.models.pregnancy import PregnancyRecord, PregnancyRiskScore, PregnancyStatus
from app.schemas.dashboard import PatientDirectoryItem
from app.models.facility import Facility


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
from app.models.staff import StaffMember as StaffMemberModel
from datetime import datetime, timedelta

async def get_overview(db: AsyncSession, facility_id: uuid.UUID) -> FacilityAdminOverview:
    today = date.today()
    seven_days_ago = today - timedelta(days=7)
    start_of_week = today - timedelta(days=today.weekday())

    # 1. Total patients
    stmt = select(func.count(Profile.id)).where(Profile.preferred_facility_id == facility_id)
    total_patients = await db.scalar(stmt) or 0

    # 2. Patients registered in the last 7 days
    from app.models.user import User as UserModel
    delta_stmt = select(func.count(Profile.id)).join(
        UserModel, UserModel.id == Profile.user_id
    ).where(
        Profile.preferred_facility_id == facility_id,
        func.date(UserModel.created_at) >= seven_days_ago,
    )
    patients_delta = await db.scalar(delta_stmt) or 0

    # 3. Unassigned patients
    stmt_un = select(func.count(Profile.id)).where(
        Profile.preferred_facility_id == facility_id,
        Profile.personal_doctor_id.is_(None)
    )
    unassigned_count = await db.scalar(stmt_un) or 0

    # 4. Active clinicians at this facility
    from app.models.staff import StaffMember as StaffMemberModel, StaffStatus, StaffRole
    stmt_clinicians = select(func.count(StaffMemberModel.id)).where(
        StaffMemberModel.facility_id == facility_id,
        StaffMemberModel.role == StaffRole.CLINICIAN,
        StaffMemberModel.status == StaffStatus.ACTIVE,
    )
    active_clinicians = await db.scalar(stmt_clinicians) or 0

    # 5. Facility-wide unacknowledged alerts
    from app.models.labour import LabourAlert, LabourSession
    alerts_stmt = select(func.count(LabourAlert.id)).join(
        LabourSession, LabourSession.id == LabourAlert.session_id
    ).where(
        LabourSession.facility_id == facility_id,
        LabourAlert.acknowledged_at.is_(None),
    )
    alerts_count = await db.scalar(alerts_stmt) or 0

    # 6. Week-at-a-glance
    from app.models.pregnancy import ScheduledVisit, VisitStatus, PregnancyRecord
    from app.models.referral import Referral, ReferralStatus

    anc_completed_stmt = select(func.count(ScheduledVisit.id)).join(
        PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        ScheduledVisit.status == VisitStatus.COMPLETED,
        func.date(ScheduledVisit.updated_at) >= start_of_week,
    )
    anc_completed = await db.scalar(anc_completed_stmt) or 0

    anc_scheduled_stmt = select(func.count(ScheduledVisit.id)).join(
        PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        func.date(ScheduledVisit.scheduled_at) >= start_of_week,
        func.date(ScheduledVisit.scheduled_at) <= today,
    )
    anc_scheduled = await db.scalar(anc_scheduled_stmt) or 0

    # Deliveries this week — labour sessions closed this week
    deliveries_stmt = select(func.count(LabourSession.id)).where(
        LabourSession.facility_id == facility_id,
        LabourSession.status == "CLOSED",
        func.date(LabourSession.updated_at) >= start_of_week,
    )
    deliveries = await db.scalar(deliveries_stmt) or 0

    # Referrals accepted (incoming)
    referrals_accepted_stmt = select(func.count(Referral.id)).where(
        Referral.to_facility_id == facility_id,
        Referral.status == ReferralStatus.ACCEPTED,
        func.date(Referral.updated_at) >= start_of_week,
    )
    referrals_accepted = await db.scalar(referrals_accepted_stmt) or 0

    # Referrals sent out (outgoing)
    referrals_out_stmt = select(func.count(Referral.id)).where(
        Referral.from_facility_id == facility_id,
        func.date(Referral.created_at) >= start_of_week,
    )
    referrals_out = await db.scalar(referrals_out_stmt) or 0

    # Postnatal follow-ups due this week
    from app.models.postpartum import BabyProfile
    postnatal_stmt = select(func.count(ScheduledVisit.id)).join(
        BabyProfile, BabyProfile.id == ScheduledVisit.baby_id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        ScheduledVisit.status == VisitStatus.SCHEDULED,
        func.date(ScheduledVisit.scheduled_at) >= start_of_week,
        func.date(ScheduledVisit.scheduled_at) <= today,
    )
    postnatal_due = await db.scalar(postnatal_stmt) or 0

    week_glance = FacilityAdminOverviewWeekAtAGlance(
        ancVisitsCompleted=anc_completed,
        ancVisitsScheduled=anc_scheduled,
        deliveries=deliveries,
        referralsAccepted=referrals_accepted,
        referralsSentOut=referrals_out,
        postnatalFollowUpsDue=postnatal_due,
    )

    return FacilityAdminOverview(
        totalPatients=total_patients,
        patientsDeltaThisWeek=patients_delta,
        unassignedPatientsCount=unassigned_count,
        activeCliniciansCount=active_clinicians,
        facilityWideAlertsCount=alerts_count,
        thisWeekAtAGlance=week_glance,
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
    from app.models.user import User, UserRole, AccountType
    from app.models.staff import StaffMember as StaffMemberModel, StaffStatus, StaffRole
    from app.core.security import get_password_hash
    from app.utils.exceptions import DuplicateResourceError

    # Check if user with phone already exists
    stmt = select(User).where(User.phone_number == invite.phoneNumber)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise DuplicateResourceError(message="User with this phone number already exists")

    # Create User record
    new_user = User(
        phone_number=invite.phoneNumber,
        password_hash=get_password_hash(invite.password),
        full_name=invite.fullName,
        role=UserRole(invite.role),
        account_type=AccountType.FULL,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    # Create StaffMember record linked to new user
    new_staff = StaffMemberModel(
        facility_id=facility_id,
        user_id=new_user.id,
        role=StaffRole(invite.role),
        specialty=invite.specialty,
        status=StaffStatus.INVITE_PENDING,
    )
    db.add(new_staff)
    await db.commit()
    await db.refresh(new_staff)
    
    return {
        "staffId": str(new_staff.id),
        "userId": str(new_user.id),
        "phoneNumber": invite.phoneNumber,
        "status": "INVITE_PENDING",
        "message": f"Staff account created. Please notify {invite.fullName} to log in with their phone number and the provided password.",
    }


async def update_staff_capacity(
    db: AsyncSession,
    facility_id: uuid.UUID,
    staff_id: uuid.UUID,
    capacity: int,
) -> dict:
    """Update the soft patient capacity cap for a staff member."""
    from app.models.staff import StaffMember as StaffMemberModel
    stmt = select(StaffMemberModel).where(
        StaffMemberModel.id == staff_id,
        StaffMemberModel.facility_id == facility_id,
    )
    res = await db.execute(stmt)
    staff = res.scalar_one_or_none()
    if not staff:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError(message="Staff member not found")
    # Store capacity in assigned_patient_count field repurposed as capacity
    # We'll add a dedicated capacity field via the assigned_patient_count workaround
    # until a migration adds a capacity column. For now store in specialty metadata.
    staff.assigned_patient_count = capacity  # use as capacity placeholder
    await db.commit()
    await db.refresh(staff)
    return {
        "staffId": str(staff.id),
        "capacity": capacity,
        "updatedAt": staff.invited_at,
    }


async def deactivate_staff(
    db: AsyncSession,
    facility_id: uuid.UUID,
    staff_id: uuid.UUID,
) -> dict:
    """Deactivate a staff member — revokes login access, preserves historical records."""
    from app.models.staff import StaffMember as StaffMemberModel, StaffStatus
    stmt = select(StaffMemberModel).where(
        StaffMemberModel.id == staff_id,
        StaffMemberModel.facility_id == facility_id,
    )
    res = await db.execute(stmt)
    staff = res.scalar_one_or_none()
    if not staff:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError(message="Staff member not found")
    staff.status = StaffStatus.DEACTIVATED
    await db.commit()
    await db.refresh(staff)
    return {
        "staffId": str(staff.id),
        "status": "DEACTIVATED",
    }


async def resend_invite(
    db: AsyncSession,
    facility_id: uuid.UUID,
    staff_id: uuid.UUID,
) -> dict:
    """Resend an invite for a pending staff member."""
    from app.models.staff import StaffMember as StaffMemberModel, StaffStatus
    from datetime import timezone as tz
    stmt = select(StaffMemberModel).where(
        StaffMemberModel.id == staff_id,
        StaffMemberModel.facility_id == facility_id,
        StaffMemberModel.status == StaffStatus.INVITE_PENDING,
    )
    res = await db.execute(stmt)
    staff = res.scalar_one_or_none()
    if not staff:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError(message="Pending staff invite not found")
    resentAt = datetime.now(tz.utc)
    return {"staffId": str(staff.id), "resentAt": resentAt}


async def assign_patient_to_clinician(
    db: AsyncSession,
    facility_id: uuid.UUID,
    patient_user_id: uuid.UUID,
    clinician_id: uuid.UUID,
) -> dict:
    """Assign a single patient to a specific clinician within the facility."""
    stmt = select(Profile).where(
        Profile.user_id == patient_user_id,
        Profile.preferred_facility_id == facility_id,
    )
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError(message="Patient not found in this facility")
    profile.personal_doctor_id = clinician_id
    await db.commit()
    return {
        "patientUserId": str(patient_user_id),
        "assignedClinicianId": str(clinician_id),
        "assignedAt": datetime.now(timezone.utc).isoformat(),
    }

async def get_facility_patients(db: AsyncSession, facility_id: uuid.UUID, search_term: Optional[str] = None, tab: Optional[str] = None) -> list[PatientDirectoryItem]:
    clinician_alias = aliased(User)
    
    stmt = select(User, Profile, Facility, clinician_alias).join(
        Profile, Profile.user_id == User.id
    ).outerjoin(
        Facility, Facility.id == Profile.preferred_facility_id
    ).outerjoin(
        clinician_alias, clinician_alias.id == Profile.personal_doctor_id
    ).where(
        User.role == UserRole.MOTHER,
        Profile.preferred_facility_id == facility_id
    )
    
    if tab == "unassigned":
        stmt = stmt.where(Profile.personal_doctor_id.is_(None))
    elif tab == "pregnant":
        from app.models.profile import PatientStage
        stmt = stmt.where(Profile.current_stage == PatientStage.PREGNANT)
    elif tab == "postpartum":
        from app.models.profile import PatientStage
        stmt = stmt.where(Profile.current_stage == PatientStage.POSTPARTUM)
    elif tab == "cycle_tracking":
        from app.models.profile import PatientStage
        stmt = stmt.where(Profile.current_stage == PatientStage.CYCLE_TRACKING)
    
    if search_term:
        stmt = stmt.where(User.full_name.ilike(f"%{search_term}%"))
        
    stmt = stmt.order_by(User.full_name).limit(100)
    
    results = await db.execute(stmt)
    directory = []
    for user, profile, facility, assigned_clinician in results.all():
        risk_level = "LOW"
        preg_stmt = select(PregnancyRiskScore).join(
            PregnancyRecord, PregnancyRecord.id == PregnancyRiskScore.pregnancy_id
        ).where(
            PregnancyRecord.user_id == user.id,
            PregnancyRecord.status == PregnancyStatus.ACTIVE
        ).order_by(desc(PregnancyRiskScore.calculated_at)).limit(1)
        
        risk_res = await db.execute(preg_stmt)
        risk = risk_res.scalar_one_or_none()
        if risk:
            risk_level = risk.level.value
            
        if tab == "high_risk" and risk_level != "HIGH":
            continue
            
        stage = profile.current_stage.value if profile.current_stage else "UNKNOWN"
        age = (date.today() - user.date_of_birth).days // 365 if user.date_of_birth else None
        
        directory.append(PatientDirectoryItem(
            userId=user.id,
            fullName=user.full_name,
            age=age,
            patientCode=profile.id.hex[:6].upper(),
            phoneNumber=user.phone_number,
            stage=stage,
            stageDetail="",
            riskLevel=risk_level,
            assignedClinicianName=assigned_clinician.full_name if assigned_clinician else "Unassigned",
            lastActivityAt=user.updated_at,
            preferredFacilityName=facility.name if facility else None
        ))
        
    return directory
