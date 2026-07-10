import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update

from app.models.labour import LabourSession, LabourAlert, LabourSessionStatus
from app.models.pregnancy import PregnancyRecord
from app.models.user import User
from app.models.profile import Profile
from app.schemas.labour import ActiveLabourSessionRead, LabourAlertsSummary, LabourAlertRead, LabourSessionRoomUpdate


async def get_active_sessions(db: AsyncSession, facility_id: uuid.UUID) -> list[ActiveLabourSessionRead]:
    """All active sessions for a facility — facility admin view."""
    stmt = select(LabourSession, User, Profile).join(
        PregnancyRecord, PregnancyRecord.id == LabourSession.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        LabourSession.facility_id == facility_id,
        LabourSession.status == LabourSessionStatus.ACTIVE
    )
    return await _build_active_sessions(db, stmt)


async def get_active_sessions_for_clinician(
    db: AsyncSession,
    facility_id: uuid.UUID,
    clinician_id: uuid.UUID,
) -> list[ActiveLabourSessionRead]:
    """Active sessions scoped to the authenticated clinician's assigned patients only."""
    stmt = select(LabourSession, User, Profile).join(
        PregnancyRecord, PregnancyRecord.id == LabourSession.pregnancy_id
    ).join(
        User, User.id == PregnancyRecord.user_id
    ).join(
        Profile, Profile.user_id == User.id
    ).where(
        LabourSession.facility_id == facility_id,
        LabourSession.status == LabourSessionStatus.ACTIVE,
        Profile.personal_doctor_id == clinician_id,
    )
    return await _build_active_sessions(db, stmt)


async def _build_active_sessions(db: AsyncSession, stmt) -> list[ActiveLabourSessionRead]:
    """Shared row-to-schema mapping for active session queries."""
    results = await db.execute(stmt)
    sessions = []

    for session, user, profile in results.all():
        hours_in_labour = 0.0
        if session.active_labour_started_at:
            delta = datetime.utcnow().replace(tzinfo=None) - session.active_labour_started_at.replace(tzinfo=None)
            hours_in_labour = round(delta.total_seconds() / 3600, 1)

        sessions.append(ActiveLabourSessionRead(
            id=session.id,
            patientName=user.full_name,
            room=session.room,
            hoursInLabour=max(0.0, hours_in_labour),
            dilationCm=None,  # populated from latest dilation reading if needed
            fhr=None,
            status=session.status.value,
            assignedClinicianName=None  # can join User again on personal_doctor_id if needed
        ))

    return sessions


async def get_alerts_summary(db: AsyncSession, facility_id: uuid.UUID) -> LabourAlertsSummary:
    # Get active session count
    stmt_count = select(func.count(LabourSession.id)).where(
        LabourSession.facility_id == facility_id,
        LabourSession.status == LabourSessionStatus.ACTIVE
    )
    active_count = await db.scalar(stmt_count) or 0
    
    # Get unacknowledged alerts
    stmt = select(LabourAlert).join(
        LabourSession, LabourSession.id == LabourAlert.session_id
    ).where(
        LabourSession.facility_id == facility_id,
        LabourAlert.acknowledged_at == None
    ).order_by(desc(LabourAlert.created_at))
    
    results = await db.execute(stmt)
    alerts = results.scalars().all()
    
    critical_count = sum(1 for a in alerts if a.severity.value == "CRITICAL")
    watch_count = sum(1 for a in alerts if a.severity.value == "WARNING")
    
    recent = [LabourAlertRead.model_validate(a) for a in alerts[:50]]
    
    return LabourAlertsSummary(
        activeLabourCount=active_count,
        criticalAlertCount=critical_count,
        watchAlertCount=watch_count,
        recentAlerts=recent
    )


async def update_room_assignment(db: AsyncSession, session_id: uuid.UUID, req: LabourSessionRoomUpdate) -> bool:
    stmt = (
        update(LabourSession)
        .where(LabourSession.id == session_id)
        .values(room=req.room)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
