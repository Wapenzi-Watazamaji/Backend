import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.labour import (
    LabourSession, LabourReading, LabourAlert, ResuscitationLog,
    LabourReadingType, AlertType, AlertSeverity,
)


async def create_session(db: AsyncSession, data: dict) -> LabourSession:
    obj = LabourSession(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_session_by_id(db: AsyncSession, session_id: uuid.UUID) -> LabourSession | None:
    stmt = select(LabourSession).where(LabourSession.id == session_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_session(db: AsyncSession, session: LabourSession, data: dict) -> LabourSession:
    for key, value in data.items():
        setattr(session, key, value)
    await db.flush()
    await db.refresh(session)
    return session


async def create_reading(db: AsyncSession, data: dict) -> LabourReading:
    obj = LabourReading(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_readings(
    db: AsyncSession,
    session_id: uuid.UUID,
    reading_type: Optional[LabourReadingType] = None,
) -> list[LabourReading]:
    stmt = select(LabourReading).where(LabourReading.session_id == session_id)
    if reading_type:
        stmt = stmt.where(LabourReading.type == reading_type)
    stmt = stmt.order_by(LabourReading.recorded_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_alert(db: AsyncSession, data: dict) -> LabourAlert:
    obj = LabourAlert(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_alerts(db: AsyncSession, session_id: uuid.UUID) -> list[LabourAlert]:
    stmt = (
        select(LabourAlert)
        .where(LabourAlert.session_id == session_id)
        .order_by(LabourAlert.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_alert_by_id(db: AsyncSession, alert_id: uuid.UUID) -> LabourAlert | None:
    stmt = select(LabourAlert).where(LabourAlert.id == alert_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_alert(db: AsyncSession, alert: LabourAlert, data: dict) -> LabourAlert:
    for key, value in data.items():
        setattr(alert, key, value)
    await db.flush()
    await db.refresh(alert)
    return alert


async def alert_exists(
    db: AsyncSession, session_id: uuid.UUID, alert_type: AlertType
) -> bool:
    stmt = select(LabourAlert).where(
        and_(
            LabourAlert.session_id == session_id,
            LabourAlert.type == alert_type,
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first() is not None


async def create_resuscitation_log(db: AsyncSession, data: dict) -> ResuscitationLog:
    obj = ResuscitationLog(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj
