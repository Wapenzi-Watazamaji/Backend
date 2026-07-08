import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary,
    DashboardAlert,
    PatientDirectoryItem,
    TimelineItem,
    AncVisitToday
)
from app.services import clinician_dashboard_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
}

@router.get(
    "/summary", 
    response_model=APIResponse[DashboardSummary],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get dashboard summary stats"
)
async def get_summary(
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    summary = await clinician_dashboard_service.get_dashboard_summary(db, facility_id, current_user.id, target_date)
    return create_success_response(data=summary)


@router.get(
    "/alerts", 
    response_model=APIResponse[list[DashboardAlert]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get unified alerts feed"
)
async def get_alerts(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    alerts = await clinician_dashboard_service.get_unified_alerts(db, facility_id, current_user.id)
    return create_success_response(data=alerts)


@router.get(
    "/directory", 
    response_model=APIResponse[list[PatientDirectoryItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get patient directory"
)
async def get_directory(
    search: Optional[str] = None,
    tab: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    directory = await clinician_dashboard_service.get_patient_directory(db, facility_id, current_user.id, search, tab)
    return create_success_response(data=directory)


@router.get(
    "/timeline", 
    response_model=APIResponse[list[TimelineItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get facility timeline"
)
async def get_timeline(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    timeline = await clinician_dashboard_service.get_clinician_timeline(db, facility_id, current_user.id)
    return create_success_response(data=timeline)


@router.get(
    "/anc-visits-today", 
    response_model=APIResponse[list[AncVisitToday]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get today's ANC visits schedule"
)
async def get_anc_visits_today(
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    visits = await clinician_dashboard_service.get_anc_visits_today(db, facility_id, current_user.id, target_date)
    return create_success_response(data=visits)
