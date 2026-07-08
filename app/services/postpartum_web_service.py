import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.pregnancy import PregnancyRecord, PregnancyStatus
from app.models.postpartum import EpdsScreening, EpdsRiskLevel
from app.models.user import User
from app.models.profile import Profile
from app.schemas.postpartum_web import (
    PostpartumPatientList,
    PostpartumAlertsSummary,
    MaternalAlert,
    NewbornAlert
)


async def get_active_postpartum_patients(db: AsyncSession, facility_id: uuid.UUID) -> list[PostpartumPatientList]:
    # Postpartum patients are represented by PregnancyRecord where status is ENDED
    stmt = select(PregnancyRecord, User, Profile).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        Profile.preferred_facility_id == facility_id,
        PregnancyRecord.status == PregnancyStatus.ENDED
    )
    
    results = await db.execute(stmt)
    patients = []
    
    for pp, user, profile in results.all():
        # calculate days postpartum
        days = 0
        if pp.ended_at:
            days = (datetime.utcnow().date() - pp.ended_at.date()).days
            
        clinician_name = "Assigned Clinician" if profile.personal_doctor_id else None
            
        patients.append(PostpartumPatientList(
            patientUserId=user.id,
            patientName=user.full_name,
            dayPostpartum=max(0, days),
            babyName=None, # fetch from baby table if needed
            babySex=None,
            status="ACTIVE", # It's a postpartum patient
            assignedClinicianName=clinician_name
        ))
        
    return patients


async def get_postpartum_alerts_summary(db: AsyncSession, facility_id: uuid.UUID) -> PostpartumAlertsSummary:
    stmt = select(EpdsScreening, User).join(
        User, User.id == EpdsScreening.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        Profile.preferred_facility_id == facility_id,
        EpdsScreening.risk_level.in_([EpdsRiskLevel.HIGH, EpdsRiskLevel.SELF_HARM_RISK])
    ).order_by(desc(EpdsScreening.created_at))
    
    results = await db.execute(stmt)
    
    maternal_alerts = []
    newborn_alerts = []
    
    critical_count = 0
    watch_count = 0
    
    for alert, user in results.all():
        if alert.is_self_harm_flagged or alert.risk_level == EpdsRiskLevel.SELF_HARM_RISK:
            critical_count += 1
            sev = "CRITICAL"
        else:
            watch_count += 1
            sev = "WARNING"
            
        maternal_alerts.append(MaternalAlert(
            patientUserId=user.id,
            patientName=user.full_name,
            dayPostpartum=0,
            severity=sev,
            message=f"High EPDS Score: {alert.total_score}",
            createdAt=alert.created_at
        ))
            
    # Count total active postpartum patients
    stmt_count = select(func.count(PregnancyRecord.id)).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        Profile.preferred_facility_id == facility_id,
        PregnancyRecord.status == PregnancyStatus.ENDED
    )
    patient_count = await db.scalar(stmt_count) or 0
    
    return PostpartumAlertsSummary(
        postpartumPatientCount=patient_count,
        criticalAlertCount=critical_count,
        watchAlertCount=watch_count,
        maternalAlerts=maternal_alerts,
        newbornAlerts=newborn_alerts
    )
