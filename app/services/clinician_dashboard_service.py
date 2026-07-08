import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import aliased

from app.models.user import User, UserRole
from app.models.profile import Profile
from app.models.pregnancy import PregnancyRecord, PregnancyRiskScore, ScheduledVisit, RiskLevel, PregnancyStatus, VisitStatus
from app.models.labour import LabourSession, LabourSessionStatus, LabourAlert
from app.models.postpartum import EpdsScreening, EpdsRiskLevel
from app.models.referral import Referral, ReferralStatus
from app.models.facility import Facility

from app.schemas.dashboard import (
    DashboardSummary,
    DashboardAlert,
    PatientDirectoryItem,
    TimelineItem,
    AncVisitToday
)


async def get_dashboard_summary(
    db: AsyncSession, 
    facility_id: uuid.UUID, 
    clinician_id: uuid.UUID, 
    target_date: Optional[date] = None
) -> DashboardSummary:
    if target_date is None:
        target_date = date.today()
        
    # assignedPatientCount
    stmt = select(func.count(User.id)).join(Profile, Profile.user_id == User.id).where(
        User.role == UserRole.MOTHER,
        Profile.personal_doctor_id == clinician_id
    )
    assigned_patient_count = await db.scalar(stmt) or 0
    
    # assignedPatientCountDeltaThisWeek
    seven_days_ago = target_date - timedelta(days=7)
    stmt_delta = select(func.count(User.id)).join(Profile, Profile.user_id == User.id).where(
        User.role == UserRole.MOTHER,
        Profile.personal_doctor_id == clinician_id,
        func.date(User.created_at) >= seven_days_ago
    )
    assigned_patient_count_delta = await db.scalar(stmt_delta) or 0
    
    # activeAlertCount
    stmt = select(func.count(LabourAlert.id)).join(
        LabourSession, LabourSession.id == LabourAlert.session_id
    ).join(
        PregnancyRecord, PregnancyRecord.id == LabourSession.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        LabourSession.facility_id == facility_id,
        LabourAlert.acknowledged_at == None,
        Profile.personal_doctor_id == clinician_id
    )
    labour_alerts_count = await db.scalar(stmt) or 0
    
    stmt = select(func.count(EpdsScreening.id)).join(
        User, User.id == EpdsScreening.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        Profile.preferred_facility_id == facility_id,
        EpdsScreening.risk_level.in_([EpdsRiskLevel.HIGH, EpdsRiskLevel.SELF_HARM_RISK]),
        Profile.personal_doctor_id == clinician_id
    )
    postpartum_alerts_count = await db.scalar(stmt) or 0
    
    # Check for missed ANC visits
    stmt_missed_anc = select(func.count(ScheduledVisit.id)).join(
        PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        func.date(ScheduledVisit.scheduled_at) < target_date,
        ScheduledVisit.status.in_([VisitStatus.SCHEDULED, VisitStatus.MISSED]),
        Profile.personal_doctor_id == clinician_id
    )
    missed_anc_alerts_count = await db.scalar(stmt_missed_anc) or 0
    
    total_alerts = labour_alerts_count + postpartum_alerts_count + missed_anc_alerts_count
    
    # ancVisitsToday
    stmt = select(func.count(ScheduledVisit.id)).join(
        PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        func.date(ScheduledVisit.scheduled_at) == target_date,
        ScheduledVisit.status == VisitStatus.SCHEDULED,
        Profile.personal_doctor_id == clinician_id
    )
    anc_visits_today = await db.scalar(stmt) or 0
    
    # ancVisitsCompletedToday
    stmt_completed = select(func.count(ScheduledVisit.id)).join(
        PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        func.date(ScheduledVisit.scheduled_at) == target_date,
        ScheduledVisit.status == VisitStatus.COMPLETED,
        Profile.personal_doctor_id == clinician_id
    )
    anc_visits_completed_today = await db.scalar(stmt_completed) or 0
    
    # pendingReferralCount
    stmt_referral = select(func.count(Referral.id)).join(
        User, User.id == Referral.patient_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        Referral.to_facility_id == facility_id,
        Referral.status == ReferralStatus.PENDING,
        Profile.personal_doctor_id == clinician_id
    )
    pending_referral_count = await db.scalar(stmt_referral) or 0
    
    return DashboardSummary(
        assignedPatientCount=assigned_patient_count,
        assignedPatientCountDeltaThisWeek=assigned_patient_count_delta,
        activeAlertCount=total_alerts,
        ancVisitsToday=anc_visits_today,
        ancVisitsCompletedToday=anc_visits_completed_today,
        pendingReferralCount=pending_referral_count
    )


async def get_unified_alerts(db: AsyncSession, facility_id: uuid.UUID, clinician_id: uuid.UUID) -> list[DashboardAlert]:
    alerts = []
    
    labour_stmt = select(LabourAlert, LabourSession, User).join(
        LabourSession, LabourSession.id == LabourAlert.session_id
    ).join(
        PregnancyRecord, PregnancyRecord.id == LabourSession.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        LabourSession.facility_id == facility_id,
        LabourAlert.acknowledged_at == None,
        Profile.personal_doctor_id == clinician_id
    ).order_by(desc(LabourAlert.created_at)).limit(50)
    
    labour_results = await db.execute(labour_stmt)
    for alert, session, user in labour_results.all():
        alerts.append(DashboardAlert(
            id=str(alert.id),
            patientUserId=user.id,
            patientName=user.full_name,
            type="LABOUR",
            severity=alert.severity.value,
            message=alert.message,
            createdAt=alert.created_at
        ))
        
    pp_stmt = select(EpdsScreening, User).join(
        User, User.id == EpdsScreening.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        Profile.preferred_facility_id == facility_id,
        EpdsScreening.risk_level.in_([EpdsRiskLevel.HIGH, EpdsRiskLevel.SELF_HARM_RISK]),
        Profile.personal_doctor_id == clinician_id
    ).order_by(desc(EpdsScreening.created_at)).limit(50)
    
    pp_results = await db.execute(pp_stmt)
    for screening, user in pp_results.all():
        alerts.append(DashboardAlert(
            id=str(screening.id),
            patientUserId=user.id,
            patientName=user.full_name,
            type="POSTPARTUM",
            severity="CRITICAL" if screening.is_self_harm_flagged else "WARNING",
            message=f"High risk EPDS screening score: {screening.total_score}",
            createdAt=screening.created_at
        ))
        
    target_date = date.today()
    missed_anc_stmt = select(ScheduledVisit, User).join(
        PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        func.date(ScheduledVisit.scheduled_at) < target_date,
        ScheduledVisit.status.in_([VisitStatus.SCHEDULED, VisitStatus.MISSED]),
        Profile.personal_doctor_id == clinician_id
    ).order_by(desc(ScheduledVisit.scheduled_at)).limit(50)
    
    missed_anc_results = await db.execute(missed_anc_stmt)
    for visit, user in missed_anc_results.all():
        alerts.append(DashboardAlert(
            id=str(visit.id),
            patientUserId=user.id,
            patientName=user.full_name,
            type="MISSED_VISIT",
            severity="WARNING",
            message=f"Missed scheduled ANC visit: {visit.label}",
            createdAt=visit.scheduled_at
        ))
        
    alerts.sort(key=lambda x: x.createdAt, reverse=True)
    return alerts[:50]


async def get_patient_directory(db: AsyncSession, facility_id: uuid.UUID, clinician_id: uuid.UUID, search_term: Optional[str] = None, tab: Optional[str] = None) -> list[PatientDirectoryItem]:
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
    
    if tab == "assigned":
        stmt = stmt.where(Profile.personal_doctor_id == clinician_id)
    elif tab == "unassigned":
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
    
    # We might need "high_risk" logic which is tricky because risk is in a different table.
    # We'll handle it below.
    
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
            continue # skip if filtering for high risk
            
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
            assignedClinicianName=assigned_clinician.full_name if assigned_clinician else None,
            lastActivityAt=user.updated_at,
            preferredFacilityName=facility.name if facility else None
        ))
        
    return directory


async def get_clinician_timeline(db: AsyncSession, facility_id: uuid.UUID, clinician_id: uuid.UUID) -> list[TimelineItem]:
    events = []
    
    visit_stmt = select(ScheduledVisit, User).join(
        PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        ScheduledVisit.status == VisitStatus.COMPLETED,
        Profile.personal_doctor_id == clinician_id
    ).order_by(desc(ScheduledVisit.updated_at)).limit(20)
    
    visit_res = await db.execute(visit_stmt)
    for visit, user in visit_res.all():
        events.append(TimelineItem(
            type="ANC_VISIT",
            isFlagged=False,
            title=f"ANC Visit Completed for {user.full_name}",
            summary=f"ANC Visit '{visit.label}' completed",
            occurredAt=visit.updated_at,
            sourceId=str(visit.id)
        ))
        
    events.sort(key=lambda x: x.occurredAt, reverse=True)
    return events[:50]


async def get_anc_visits_today(db: AsyncSession, facility_id: uuid.UUID, clinician_id: uuid.UUID, target_date: Optional[date] = None) -> list[AncVisitToday]:
    if target_date is None:
        target_date = date.today()
        
    stmt = select(ScheduledVisit, User).join(
        PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        ScheduledVisit.facility_id == facility_id,
        func.date(ScheduledVisit.scheduled_at) == target_date,
        Profile.personal_doctor_id == clinician_id
    ).order_by(ScheduledVisit.scheduled_at)
    
    results = await db.execute(stmt)
    visits = []
    for visit, user in results.all():
        visits.append(AncVisitToday(
            scheduledVisitId=visit.id,
            patientName=user.full_name,
            scheduledAt=visit.scheduled_at,
            purpose=visit.purpose or visit.label,
            status=visit.status.value
        ))
    return visits
