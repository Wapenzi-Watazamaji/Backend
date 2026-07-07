import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.education import EducationContent, EducationEvent, ContentCategory

async def get_content_by_id(db: AsyncSession, content_id: uuid.UUID) -> EducationContent | None:
    stmt = select(EducationContent).where(EducationContent.id == content_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_content_list(
    db: AsyncSession, 
    facility_id: uuid.UUID, 
    category: ContentCategory | None = None,
    skip: int = 0,
    limit: int = 100
) -> Sequence[EducationContent]:
    stmt = select(EducationContent).where(EducationContent.facility_id == facility_id)
    if category:
        stmt = stmt.where(EducationContent.category == category)
    stmt = stmt.offset(skip).limit(limit).order_by(EducationContent.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_event_by_id(db: AsyncSession, event_id: uuid.UUID) -> EducationEvent | None:
    stmt = select(EducationEvent).where(EducationEvent.id == event_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_events_list(db: AsyncSession, facility_id: uuid.UUID) -> Sequence[EducationEvent]:
    stmt = select(EducationEvent).where(EducationEvent.facility_id == facility_id).order_by(EducationEvent.event_date.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_content(db: AsyncSession, content_id: uuid.UUID) -> bool:
    stmt = delete(EducationContent).where(EducationContent.id == content_id)
    result = await db.execute(stmt)
    return result.rowcount > 0

async def delete_event(db: AsyncSession, event_id: uuid.UUID) -> bool:
    stmt = delete(EducationEvent).where(EducationEvent.id == event_id)
    result = await db.execute(stmt)
    return result.rowcount > 0
