import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.models.reminder import ReminderType
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderRead
from app.services import reminder_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    404: {"model": APIResponse[None], "description": "Not Found"},
}

@router.post(
    "",
    response_model=APIResponse[ReminderRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Create a reminder"
)
async def create_reminder(
    reminder_in: ReminderCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    reminder = await reminder_service.create_reminder(db, current_user.id, reminder_in)
    return create_success_response(data=reminder)

@router.get(
    "",
    response_model=APIResponse[List[ReminderRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List reminders"
)
async def list_reminders(
    upcoming_only: Optional[bool] = Query(False, alias="upcomingOnly"),
    reminder_type: Optional[ReminderType] = Query(None, alias="type"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    reminders = await reminder_service.list_reminders(
        db, current_user.id, upcoming_only=upcoming_only, reminder_type=reminder_type
    )
    return create_success_response(data=reminders)

@router.put(
    "/{reminder_id}",
    response_model=APIResponse[ReminderRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Update reminder due time"
)
async def update_reminder(
    reminder_id: uuid.UUID,
    reminder_in: ReminderUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    reminder = await reminder_service.update_reminder(db, reminder_id, current_user.id, reminder_in)
    return create_success_response(data=reminder)

@router.put(
    "/{reminder_id}/mark-done",
    response_model=APIResponse[ReminderRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Mark reminder as completed"
)
async def mark_reminder_done(
    reminder_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    reminder = await reminder_service.mark_reminder_done(db, reminder_id, current_user.id)
    return create_success_response(data=reminder)

@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Delete reminder"
)
async def delete_reminder(
    reminder_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    await reminder_service.delete_reminder(db, reminder_id, current_user.id)
    return None
