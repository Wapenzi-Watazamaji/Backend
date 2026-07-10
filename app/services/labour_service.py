import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.labour import (
    LabourSession, LabourReading, LabourAlert, ResuscitationLog,
    LabourSessionStatus, LabourReadingType, AlertType, AlertSeverity,
)
from app.repositories import labour_repository
from app.utils.exceptions import NotFoundError, ForbiddenError, ValidationError


WHO_ALERT_LINE_SLOPE = 1.0
WHO_ACTION_LINE_OFFSET_HOURS = 4.0
ACTIVE_LABOUR_MIN_DILATION_CM = 4.0

RESUSCITATION_PROTOCOL = [
    {"order": 1, "title": "Dry, warm, and position the baby", "timerSeconds": None, "instructions": None},
    {"order": 2, "title": "Assess breathing and heart rate", "timerSeconds": None, "instructions": None},
    {"order": 3, "title": "Begin positive pressure ventilation", "timerSeconds": 30, "instructions": "Ventilate at 40-60 breaths per minute. Reassess heart rate after 30 seconds."},
    {"order": 4, "title": "Reassess heart rate", "timerSeconds": None, "instructions": None},
    {"order": 5, "title": "Chest compressions, if indicated", "timerSeconds": 60, "instructions": "3 compressions to 1 ventilation, at a rate of 120 events per minute."},
    {"order": 6, "title": "Consider escalation", "timerSeconds": None, "instructions": None},
]


def _hours_elapsed(start: datetime, point: datetime) -> float:
    delta = point - start
    return round(delta.total_seconds() / 3600, 2)


def _compute_partograph(session: LabourSession, readings: list[LabourReading]) -> dict:
    start = session.active_labour_started_at
    dilation_readings = [r for r in readings if r.type == LabourReadingType.DILATION]
    fhr_readings = [r for r in readings if r.type == LabourReadingType.FHR]

    first_dilation = dilation_readings[0] if dilation_readings else None
    start_cm = first_dilation.value if first_dilation else ACTIVE_LABOUR_MIN_DILATION_CM

    alert_line = {
        "startHour": 0.0,
        "startCm": start_cm,
        "slopeCmPerHour": WHO_ALERT_LINE_SLOPE,
    }
    action_line = {
        "startHour": WHO_ACTION_LINE_OFFSET_HOURS,
        "startCm": start_cm,
        "slopeCmPerHour": WHO_ALERT_LINE_SLOPE,
    }

    has_alert_crossed = False
    has_action_crossed = False

    dilation_points = []
    for r in dilation_readings:
        hours = _hours_elapsed(start, r.recorded_at)
        expected_alert = start_cm + (hours * WHO_ALERT_LINE_SLOPE)
        expected_action = start_cm + (max(0.0, hours - WHO_ACTION_LINE_OFFSET_HOURS) * WHO_ALERT_LINE_SLOPE)

        if r.value < expected_alert:
            has_alert_crossed = True
        if hours > WHO_ACTION_LINE_OFFSET_HOURS and r.value < expected_action:
            has_action_crossed = True

        dilation_points.append({"hoursElapsed": hours, "value": r.value, "recordedAt": r.recorded_at})

    fhr_points = [
        {"hoursElapsed": _hours_elapsed(start, r.recorded_at), "value": r.value, "recordedAt": r.recorded_at}
        for r in fhr_readings
    ]

    return {
        "dilationReadings": dilation_points,
        "fhrReadings": fhr_points,
        "alertLine": alert_line,
        "actionLine": action_line,
        "hasAlertLineCrossed": has_alert_crossed,
        "hasActionLineCrossed": has_action_crossed,
    }


async def _check_and_raise_alerts(
    db: AsyncSession,
    session: LabourSession,
    readings: list[LabourReading],
) -> None:
    partograph = _compute_partograph(session, readings)

    if partograph["hasActionLineCrossed"]:
        exists = await labour_repository.alert_exists(db, session.id, AlertType.ACTION_LINE_CROSSED)
        if not exists:
            await labour_repository.create_alert(db, {
                "session_id": session.id,
                "type": AlertType.ACTION_LINE_CROSSED,
                "severity": AlertSeverity.CRITICAL,
                "message": "Labour progress is now 4 hours behind the expected rate",
            })
    elif partograph["hasAlertLineCrossed"]:
        exists = await labour_repository.alert_exists(db, session.id, AlertType.ACTION_LINE_CROSSED)
        if not exists:
            await labour_repository.create_alert(db, {
                "session_id": session.id,
                "type": AlertType.ACTION_LINE_CROSSED,
                "severity": AlertSeverity.WARNING,
                "message": "Labour progress has crossed the WHO alert line — monitor closely",
            })

    fhr_readings = [r for r in readings if r.type == LabourReadingType.FHR]
    if fhr_readings:
        latest_fhr = fhr_readings[-1].value
        if latest_fhr < 110 or latest_fhr > 160:
            exists = await labour_repository.alert_exists(db, session.id, AlertType.FETAL_DISTRESS)
            if not exists:
                await labour_repository.create_alert(db, {
                    "session_id": session.id,
                    "type": AlertType.FETAL_DISTRESS,
                    "severity": AlertSeverity.CRITICAL,
                    "message": f"Fetal heart rate of {latest_fhr} bpm is outside normal range (110–160 bpm)",
                })

    bp_readings = [r for r in readings if r.type == LabourReadingType.MATERNAL_BP]
    if bp_readings:
        latest_bp = bp_readings[-1]
        systolic = latest_bp.meta.get("systolic") if latest_bp.meta else None
        if systolic and systolic >= 140:
            exists = await labour_repository.alert_exists(db, session.id, AlertType.PREECLAMPSIA_RISK)
            if not exists:
                await labour_repository.create_alert(db, {
                    "session_id": session.id,
                    "type": AlertType.PREECLAMPSIA_RISK,
                    "severity": AlertSeverity.CRITICAL,
                    "message": f"Maternal systolic blood pressure of {systolic} mmHg indicates pre-eclampsia risk",
                })


async def _get_active_session(db: AsyncSession, session_id: uuid.UUID) -> LabourSession:
    session = await labour_repository.get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError(message="Labour session not found")
    return session


async def create_session(
    db: AsyncSession, clinician_id: uuid.UUID, data
) -> LabourSession:
    session = await labour_repository.create_session(db, {
        "pregnancy_id": data.pregnancyId,
        "facility_id": data.facilityId,
        "clinician_id": clinician_id,
        "active_labour_started_at": data.activeLabourStartedAt,
        "status": LabourSessionStatus.ACTIVE,
        "room": data.room,
    })
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> LabourSession:
    return await _get_active_session(db, session_id)


async def close_session(
    db: AsyncSession, session_id: uuid.UUID, data
) -> LabourSession:
    session = await _get_active_session(db, session_id)
    if session.status == LabourSessionStatus.CLOSED:
        raise ValidationError(message="Labour session is already closed")

    updated = await labour_repository.update_session(db, session, {
        "status": LabourSessionStatus.CLOSED,
        "outcome": data.outcome,
        "delivery_type": data.deliveryType,
        "closed_at": data.closedAt,
    })
    await db.commit()
    await db.refresh(updated)
    return updated


async def add_dilation_reading(
    db: AsyncSession, session_id: uuid.UUID, data
) -> LabourReading:
    session = await _get_active_session(db, session_id)

    reading = await labour_repository.create_reading(db, {
        "session_id": session.id,
        "type": LabourReadingType.DILATION,
        "value": data.value,
        "recorded_at": data.recordedAt,
    })

    all_readings = await labour_repository.list_readings(db, session.id)
    await _check_and_raise_alerts(db, session, all_readings)

    await db.commit()
    await db.refresh(reading)
    return reading


async def add_fhr_reading(
    db: AsyncSession, session_id: uuid.UUID, data
) -> LabourReading:
    session = await _get_active_session(db, session_id)

    reading = await labour_repository.create_reading(db, {
        "session_id": session.id,
        "type": LabourReadingType.FHR,
        "value": data.value,
        "recorded_at": data.recordedAt,
    })

    all_readings = await labour_repository.list_readings(db, session.id)
    await _check_and_raise_alerts(db, session, all_readings)

    await db.commit()
    await db.refresh(reading)
    return reading


async def add_maternal_bp_reading(
    db: AsyncSession, session_id: uuid.UUID, data
) -> LabourReading:
    session = await _get_active_session(db, session_id)

    reading = await labour_repository.create_reading(db, {
        "session_id": session.id,
        "type": LabourReadingType.MATERNAL_BP,
        "value": float(data.bloodPressureSystolic),
        "meta": {
            "systolic": data.bloodPressureSystolic,
            "diastolic": data.bloodPressureDiastolic,
        },
        "recorded_at": data.recordedAt,
    })

    all_readings = await labour_repository.list_readings(db, session.id)
    await _check_and_raise_alerts(db, session, all_readings)

    await db.commit()
    await db.refresh(reading)
    return reading


async def add_contraction_reading(
    db: AsyncSession, session_id: uuid.UUID, data
) -> LabourReading:
    session = await _get_active_session(db, session_id)

    reading = await labour_repository.create_reading(db, {
        "session_id": session.id,
        "type": LabourReadingType.CONTRACTIONS,
        "value": float(data.frequencyPer10Min),
        "meta": {
            "frequencyPer10Min": data.frequencyPer10Min,
            "durationSeconds": data.durationSeconds,
        },
        "recorded_at": data.recordedAt,
    })
    await db.commit()
    await db.refresh(reading)
    return reading


async def get_partograph(db: AsyncSession, session_id: uuid.UUID) -> dict:
    session = await _get_active_session(db, session_id)
    readings = await labour_repository.list_readings(db, session.id)
    return _compute_partograph(session, readings)


async def list_alerts(db: AsyncSession, session_id: uuid.UUID) -> list[LabourAlert]:
    await _get_active_session(db, session_id)
    return await labour_repository.list_alerts(db, session_id)


async def acknowledge_alert(
    db: AsyncSession,
    session_id: uuid.UUID,
    alert_id: uuid.UUID,
    clinician_id: uuid.UUID,
) -> LabourAlert:
    await _get_active_session(db, session_id)
    alert = await labour_repository.get_alert_by_id(db, alert_id)
    if not alert or alert.session_id != session_id:
        raise NotFoundError(message="Alert not found")

    updated = await labour_repository.update_alert(db, alert, {
        "acknowledged_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        "acknowledged_by": clinician_id,
    })
    await db.commit()
    await db.refresh(updated)
    return updated


async def escalate_alert(
    db: AsyncSession,
    session_id: uuid.UUID,
    alert_id: uuid.UUID,
    escalate_to: str,
) -> dict:
    await _get_active_session(db, session_id)
    alert = await labour_repository.get_alert_by_id(db, alert_id)
    if not alert or alert.session_id != session_id:
        raise NotFoundError(message="Alert not found")

    await labour_repository.update_alert(db, alert, {"escalated_to": escalate_to})
    await db.commit()
    return {"referralId": None, "escalatedTo": escalate_to}


def get_resuscitation_protocol() -> dict:
    return {"steps": RESUSCITATION_PROTOCOL}


async def create_resuscitation_log(
    db: AsyncSession, session_id: uuid.UUID, data
) -> ResuscitationLog:
    await _get_active_session(db, session_id)

    log = await labour_repository.create_resuscitation_log(db, {
        "session_id": session_id,
        "step_order": data.stepOrder,
        "completed_at": data.completedAt,
        "vitals_at_step": data.vitalsAtStep,
    })
    await db.commit()
    await db.refresh(log)
    return log
