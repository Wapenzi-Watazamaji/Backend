import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, Any, Dict

from app.models.education import EducationContent, EducationEvent, ContentCategory
from app.schemas.education import (
    EducationContentCreate, EducationContentUpdate, EducationContentRead,
    EducationEventCreate, EducationEventUpdate, EducationEventRead
)
from app.repositories import education_repository
from app.utils.exceptions import NotFoundError

async def create_content(db: AsyncSession, facility_id: uuid.UUID, req: EducationContentCreate) -> EducationContentRead:
    content = EducationContent(**req.model_dump(), facility_id=facility_id)
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return EducationContentRead.model_validate(content)

async def get_content(db: AsyncSession, content_id: uuid.UUID) -> EducationContentRead:
    content = await education_repository.get_content_by_id(db, content_id)
    if not content:
        raise NotFoundError(message="Education content not found")
    return EducationContentRead.model_validate(content)

async def list_content(
    db: AsyncSession, 
    facility_id: uuid.UUID | None = None, 
    category: ContentCategory | None = None,
    skip: int = 0,
    limit: int = 100
) -> list[EducationContentRead]:
    contents = await education_repository.get_content_list(db, facility_id, category, skip, limit)
    return [EducationContentRead.model_validate(c) for c in contents]

async def update_content(db: AsyncSession, facility_id: uuid.UUID, content_id: uuid.UUID, req: EducationContentUpdate) -> EducationContentRead:
    content = await education_repository.get_content_by_id(db, content_id)
    if not content or content.facility_id != facility_id:
        raise NotFoundError(message="Education content not found in this facility")
        
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
        
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return EducationContentRead.model_validate(content)

async def delete_content(db: AsyncSession, facility_id: uuid.UUID, content_id: uuid.UUID) -> None:
    content = await education_repository.get_content_by_id(db, content_id)
    if not content or content.facility_id != facility_id:
        raise NotFoundError(message="Education content not found in this facility")
        
    await education_repository.delete_content(db, content_id)
    await db.commit()

async def create_event(db: AsyncSession, facility_id: uuid.UUID, req: EducationEventCreate) -> EducationEventRead:
    event = EducationEvent(**req.model_dump(), facility_id=facility_id)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return EducationEventRead.model_validate(event)

async def get_event(db: AsyncSession, event_id: uuid.UUID) -> EducationEventRead:
    event = await education_repository.get_event_by_id(db, event_id)
    if not event:
        raise NotFoundError(message="Education event not found")
    return EducationEventRead.model_validate(event)

async def list_events(db: AsyncSession, facility_id: uuid.UUID | None = None) -> list[EducationEventRead]:
    events = await education_repository.get_events_list(db, facility_id)
    return [EducationEventRead.model_validate(e) for e in events]

async def get_feed(db: AsyncSession, facility_id: uuid.UUID | None = None, filter_type: str = "all") -> list[Dict[str, Any]]:
    # Simple feed generator combining content and events
    feed = []
    
    if filter_type in ["all", "content"]:
        contents = await education_repository.get_content_list(db, facility_id, limit=50)
        for c in contents:
            item = EducationContentRead.model_validate(c).model_dump()
            item["type"] = "CONTENT"
            feed.append(item)
            
    if filter_type in ["all", "events"]:
        events = await education_repository.get_events_list(db, facility_id)
        for e in events:
            item = EducationEventRead.model_validate(e).model_dump()
            item["type"] = "EVENT"
            feed.append(item)
        
    # Sort by created_at descending (approximate)
    feed.sort(key=lambda x: x["created_at"], reverse=True)
    return feed
