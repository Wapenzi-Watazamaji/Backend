from app.schemas.dashboard import LandingSummary
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


async def get_clinician_patients(
    db: AsyncSession,
    facility_id: uuid.UUID,
    clinician_id: uuid.UUID,
    search_term: Optional[str] = None,
    tab: Optional[str] = None
) -> list[PatientDirectoryItem]:
    """Returns ONLY patients whose personal_doctor_id matches the authenticated clinician."""
    clinician_alias = aliased(User)

    stmt = select(User, Profile, Facility, clinician_alias).join(
        Profile, Profile.user_id == User.id
    ).outerjoin(
        Facility, Facility.id == Profile.preferred_facility_id
    ).outerjoin(
        clinician_alias, clinician_alias.id == Profile.personal_doctor_id
    ).where(
        User.role == UserRole.MOTHER,
        Profile.preferred_facility_id == facility_id,
        Profile.personal_doctor_id == clinician_id  # always enforced
    )

    # Stage-based tab filtering (assignment is already locked to this clinician)
    if tab == "pregnant":
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


async def acknowledge_alert(
    db: AsyncSession,
    alert_id: uuid.UUID,
    clinician_id: uuid.UUID,
) -> dict:
    """Acknowledge a labour alert by id — scoped to clinician's patients."""
    from datetime import timezone as tz
    stmt = select(LabourAlert).where(LabourAlert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError(message="Alert not found")

    alert.acknowledged_at = datetime.now(tz.utc)
    await db.commit()
    await db.refresh(alert)
    return {
        "id": str(alert.id),
        "acknowledgedAt": alert.acknowledged_at,
    }


async def get_patient_overview(
    db: AsyncSession,
    patient_user_id: uuid.UUID,
    clinician_id: uuid.UUID,
) -> dict:
    """Return patient overview: user+profile, pregnancy summary, care team, emergency contact."""
    from app.models.pregnancy import PregnancyRecord, PregnancyStatus, ScheduledVisit, VisitStatus, PregnancyVitalsEntry
    from sqlalchemy import func as sql_func

    # Fetch patient user + profile
    stmt = select(User, Profile).join(Profile, Profile.user_id == User.id).where(User.id == patient_user_id)
    res = await db.execute(stmt)
    row = res.one_or_none()
    if not row:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError(message="Patient not found")
    user, profile = row

    patient_dict = {
        "userId": str(user.id),
        "fullName": user.full_name,
        "phoneNumber": user.phone_number,
        "dateOfBirth": user.date_of_birth.isoformat() if user.date_of_birth else None,
        "stage": profile.current_stage.value if profile.current_stage else "UNKNOWN",
    }

    # Pregnancy summary
    pregnancy_summary = None
    preg_stmt = select(PregnancyRecord).where(
        PregnancyRecord.user_id == patient_user_id,
        PregnancyRecord.status == PregnancyStatus.ACTIVE,
    ).order_by(desc(PregnancyRecord.created_at)).limit(1)
    preg_res = await db.execute(preg_stmt)
    pregnancy = preg_res.scalar_one_or_none()

    if pregnancy:
        today = date.today()
        gestational_days = (today - pregnancy.last_menstrual_period).days
        weeks = gestational_days // 7
        days = gestational_days % 7

        # ANC visits
        total_stmt = select(func.count(ScheduledVisit.id)).where(
            ScheduledVisit.pregnancy_id == pregnancy.id
        )
        completed_stmt = select(func.count(ScheduledVisit.id)).where(
            ScheduledVisit.pregnancy_id == pregnancy.id,
            ScheduledVisit.status == VisitStatus.COMPLETED,
        )
        total_anc = await db.scalar(total_stmt) or 0
        completed_anc = await db.scalar(completed_stmt) or 0

        # Last vitals (BP and weight from latest submission)
        vitals_stmt = select(PregnancyVitalsEntry).where(
            PregnancyVitalsEntry.pregnancy_id == pregnancy.id
        ).order_by(desc(PregnancyVitalsEntry.created_at)).limit(1)
        vitals_res = await db.execute(vitals_stmt)
        latest_vitals = vitals_res.scalar_one_or_none()
        last_bp = None
        last_weight = None
        if latest_vitals and latest_vitals.submission:
            answers = latest_vitals.submission.answers
            systolic = answers.get("systolicBP")
            diastolic = answers.get("diastolicBP")
            if systolic and diastolic:
                last_bp = f"{systolic}/{diastolic}"
            last_weight = answers.get("weightKg")

        pregnancy_summary = {
            "dueDate": pregnancy.due_date.isoformat(),
            "gestationalAge": f"{weeks} weeks, {days} days",
            "ancVisitsCompleted": completed_anc,
            "ancVisitsTotal": total_anc,
            "lastBloodPressure": last_bp,
            "lastWeightKg": last_weight,
        }

    # Care team — assigned clinician
    care_team = []
    if profile.personal_doctor_id:
        doc_stmt = select(User).where(User.id == profile.personal_doctor_id)
        doc_res = await db.execute(doc_stmt)
        doc = doc_res.scalar_one_or_none()
        if doc:
            care_team.append({
                "userId": str(doc.id),
                "fullName": doc.full_name,
                "role": "Assigned clinician",
            })

    # Emergency contact
    emergency_contact = None
    if profile.emergency_contact_name:
        emergency_contact = {
            "name": profile.emergency_contact_name,
            "relationship": profile.emergency_contact_relationship,
            "phoneNumber": profile.emergency_contact_phone,
        }

    return {
        "patient": patient_dict,
        "pregnancySummary": pregnancy_summary,
        "careTeam": care_team,
        "emergencyContact": emergency_contact,
    }


async def get_patient_timeline(
    db: AsyncSession,
    patient_user_id: uuid.UUID,
    clinician_id: uuid.UUID,
    filter_type: Optional[str] = "ALL",
    page: int = 1,
    page_size: int = 20,
) -> list[TimelineItem]:
    """Cross-module timeline for a single patient: visits, vitals submissions, labour events."""
    from app.models.pregnancy import PregnancyRecord, PregnancyVitalsEntry, ScheduledVisit
    from app.models.labour import LabourSession, LabourReading

    events: list[TimelineItem] = []

    # ANC Visits
    if filter_type in ("ALL", "VISITS"):
        visit_stmt = select(ScheduledVisit).join(
            PregnancyRecord, PregnancyRecord.id == ScheduledVisit.pregnancy_id
        ).where(
            PregnancyRecord.user_id == patient_user_id,
        ).order_by(desc(ScheduledVisit.updated_at)).limit(50)

        visit_res = await db.execute(visit_stmt)
        for visit in visit_res.scalars().all():
            events.append(TimelineItem(
                type="SCHEDULED_VISIT",
                isFlagged=visit.status.value == "MISSED",
                title=f"ANC Visit — {visit.label}",
                summary=visit.summary or f"Scheduled ANC visit: {visit.label}",
                occurredAt=visit.updated_at,
                sourceId=str(visit.id),
            ))

    # Vitals / Form Submissions
    if filter_type in ("ALL", "VITALS", "FLAGS"):
        from app.models.cycle import FormSubmission, FormContext
        sub_stmt = select(FormSubmission).where(
            FormSubmission.user_id == patient_user_id,
            FormSubmission.context.in_([
                FormContext.PREGNANCY_VITALS,
                FormContext.MATERNAL_CHECKIN,
            ]),
        ).order_by(desc(FormSubmission.created_at)).limit(50)

        sub_res = await db.execute(sub_stmt)
        for sub in sub_res.scalars().all():
            # Check if vitals entry is flagged
            vitals_stmt = select(PregnancyVitalsEntry).where(
                PregnancyVitalsEntry.submission_id == sub.id
            )
            vr = await db.execute(vitals_stmt)
            vitals_entry = vr.scalar_one_or_none()
            is_flagged = vitals_entry.is_flagged if vitals_entry else False

            if filter_type == "FLAGS" and not is_flagged:
                continue

            events.append(TimelineItem(
                type="FORM_SUBMISSION",
                isFlagged=is_flagged,
                title="Vitals / Check-in submitted",
                summary=f"Patient submitted a {sub.context.value.replace('_', ' ').title()} form",
                occurredAt=sub.created_at,
                sourceId=str(sub.id),
                actions=["RESPOND"] if is_flagged else [],
            ))

    # Labour Events
    if filter_type in ("ALL",):
        from app.models.pregnancy import PregnancyRecord
        lab_stmt = select(LabourSession).join(
            PregnancyRecord, PregnancyRecord.id == LabourSession.pregnancy_id
        ).where(
            PregnancyRecord.user_id == patient_user_id
        ).order_by(desc(LabourSession.created_at)).limit(10)

        lab_res = await db.execute(lab_stmt)
        for session in lab_res.scalars().all():
            events.append(TimelineItem(
                type="LABOUR_EVENT",
                isFlagged=session.status.value in ("CLOSED",) and session.outcome is not None,
                title=f"Labour Session — {session.status.value}",
                summary=f"Labour session {'completed' if session.status.value == 'CLOSED' else 'active'}",
                occurredAt=session.created_at,
                sourceId=str(session.id),
            ))

    events.sort(key=lambda e: e.occurredAt, reverse=True)
    offset = (page - 1) * page_size
    return events[offset: offset + page_size]


async def get_patient_pregnancy_vitals(
    db: AsyncSession,
    patient_user_id: uuid.UUID,
    clinician_id: uuid.UUID,
    filter_type: Optional[str] = "ALL",
    page: int = 1,
    page_size: int = 20,
) -> list[dict]:
    """Return pregnancy vitals submissions for a patient as a clinician read view."""
    from app.models.pregnancy import PregnancyVitalsEntry, PregnancyRecord
    from app.models.cycle import FormSubmission, FormContext

    stmt = select(FormSubmission, PregnancyVitalsEntry).outerjoin(
        PregnancyVitalsEntry, PregnancyVitalsEntry.submission_id == FormSubmission.id
    ).where(
        FormSubmission.user_id == patient_user_id,
        FormSubmission.context.in_([
            FormContext.PREGNANCY_VITALS,
            FormContext.MATERNAL_CHECKIN,
        ]),
    )

    if filter_type == "FLAGGED":
        stmt = stmt.where(PregnancyVitalsEntry.is_flagged == True)
    elif filter_type == "VITALS_ONLY":
        stmt = stmt.where(FormSubmission.context == FormContext.PREGNANCY_VITALS)
    elif filter_type == "SYMPTOMS_ONLY":
        stmt = stmt.where(FormSubmission.context == FormContext.MATERNAL_CHECKIN)

    stmt = stmt.order_by(desc(FormSubmission.created_at))
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    res = await db.execute(stmt)
    results = []
    for sub, vitals_entry in res.all():
        feedback_count = 0
        if vitals_entry:
            from sqlalchemy import select as sel
            from app.models.pregnancy import VitalsFeedback
            fb_stmt = sel(func.count(VitalsFeedback.id)).where(
                VitalsFeedback.vitals_entry_id == vitals_entry.id
            )
            feedback_count = await db.scalar(fb_stmt) or 0

        results.append({
            "submissionId": sub.id,
            "submittedAt": sub.created_at,
            "answers": sub.answers,
            "isFlagged": vitals_entry.is_flagged if vitals_entry else False,
            "flaggedReasons": vitals_entry.flagged_reasons if vitals_entry else [],
            "feedbackCount": feedback_count,
        })

    return results


async def get_landing_summary(
    db: AsyncSession,
    user_id: uuid.UUID,
    facility_id: Optional[uuid.UUID] = None,
) -> dict:
    """Post-login landing summary — alert count, active labour sessions, pending referrals."""
    # Active alert count — labour alerts for this clinician
    alert_stmt = select(func.count(LabourAlert.id)).join(
        LabourSession, LabourSession.id == LabourAlert.session_id
    ).join(
        PregnancyRecord, PregnancyRecord.id == LabourSession.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        LabourAlert.acknowledged_at.is_(None),
        Profile.personal_doctor_id == user_id,
    )
    if facility_id:
        alert_stmt = alert_stmt.where(LabourSession.facility_id == facility_id)
    active_alert_count = await db.scalar(alert_stmt) or 0

    # Active labour sessions
    lab_stmt = select(func.count(LabourSession.id)).join(
        PregnancyRecord, PregnancyRecord.id == LabourSession.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        LabourSession.status.in_(["ACTIVE"]),
        Profile.personal_doctor_id == user_id,
    )
    if facility_id:
        lab_stmt = lab_stmt.where(LabourSession.facility_id == facility_id)
    active_labour_count = await db.scalar(lab_stmt) or 0

    # Pending referrals to the facility
    pending_referrals = 0
    if facility_id:
        from app.models.referral import Referral, ReferralStatus
        ref_stmt = select(func.count(Referral.id)).where(
            Referral.to_facility_id == facility_id,
            Referral.status == ReferralStatus.PENDING,
        )
        pending_referrals = await db.scalar(ref_stmt) or 0

    return LandingSummary(
        activeAlertCount=active_alert_count,
        activeLabourSessionsCount=active_labour_count,
        pendingReferralsCount=pending_referrals,
    )


async def add_clinical_note(
    db: AsyncSession,
    patient_user_id: uuid.UUID,
    clinician_id: uuid.UUID,
    message: str,
    submission_id: Optional[uuid.UUID] = None,
):
    from app.repositories import pregnancy_repository
    data = {
        "patient_user_id": patient_user_id,
        "clinician_id": clinician_id,
        "message": message,
        "submission_id": submission_id,
    }
    return await pregnancy_repository.create_clinical_note(db, data)


async def get_clinical_notes(
    db: AsyncSession, patient_user_id: uuid.UUID
):
    from app.repositories import pregnancy_repository
    return await pregnancy_repository.list_clinical_notes_for_patient(db, patient_user_id)
