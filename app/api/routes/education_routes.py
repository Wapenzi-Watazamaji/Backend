import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_dep as get_db, get_facility_context, require_clinician
from app.models.user import User
from app.models.education import ContentCategory
from app.schemas.education import (
    EducationContentCreate, EducationContentUpdate, EducationContentRead,
    EducationEventCreate, EducationEventUpdate, EducationEventRead
)
from app.services import education_service
from app.utils.exceptions import APIResponse, create_success_response

router = APIRouter(prefix="/education", tags=["Education & Community"])

@router.post("/content", response_model=APIResponse[EducationContentRead], status_code=status.HTTP_201_CREATED)
async def create_content(
    req: EducationContentCreate,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
):
    content = await education_service.create_content(db, requester_facility_id, req)
    return create_success_response(message="Content created successfully", data=content)

@router.get("/content", response_model=APIResponse[list[EducationContentRead]])
async def list_content(
    facility_id: uuid.UUID | None = Query(None, description="Optional facility ID to filter by"),
    category: ContentCategory | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contents = await education_service.list_content(db, facility_id, category, skip, limit)
    return create_success_response(message="Content fetched successfully", data=contents)

@router.get("/content/{content_id}", response_model=APIResponse[EducationContentRead])
async def get_content(
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await education_service.get_content(db, content_id)
    return create_success_response(message="Content fetched successfully", data=content)

@router.put("/content/{content_id}", response_model=APIResponse[EducationContentRead])
async def update_content(
    content_id: uuid.UUID,
    req: EducationContentUpdate,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
):
    content = await education_service.update_content(db, requester_facility_id, content_id, req)
    return create_success_response(message="Content updated successfully", data=content)

@router.delete("/content/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: uuid.UUID,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
):
    await education_service.delete_content(db, requester_facility_id, content_id)
    return None

@router.post("/events", response_model=APIResponse[EducationEventRead], status_code=status.HTTP_201_CREATED)
async def create_event(
    req: EducationEventCreate,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_clinician),
    db: AsyncSession = Depends(get_db),
):
    event = await education_service.create_event(db, requester_facility_id, req)
    return create_success_response(message="Event created successfully", data=event)

@router.get("/events", response_model=APIResponse[list[EducationEventRead]])
async def list_events(
    facility_id: uuid.UUID | None = Query(None, description="Optional facility ID to filter by"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    events = await education_service.list_events(db, facility_id)
    return create_success_response(message="Events fetched successfully", data=events)

@router.get("/events/{event_id}", response_model=APIResponse[EducationEventRead])
async def get_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event = await education_service.get_event(db, event_id)
    return create_success_response(message="Event fetched successfully", data=event)

@router.get("/feed", response_model=APIResponse[list[Dict[str, Any]]])
async def get_feed(
    facility_id: uuid.UUID | None = Query(None, description="Optional facility ID to filter by"),
    filter_type: str = Query("all", description="Filter feed by 'all', 'content', or 'events'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    feed = await education_service.get_feed(db, facility_id, filter_type)
    return create_success_response(message="Feed fetched successfully", data=feed)