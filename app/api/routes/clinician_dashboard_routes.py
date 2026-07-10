import uuid
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary,
    DashboardAlert,
    PatientDirectoryItem,
    TimelineItem,
    AncVisitToday,
    PatientVitalsItem,
)
from app.schemas.labour import ActiveLabourSessionRead
from app.schemas.pregnancy import ClinicalNoteRead, ClinicalNoteCreateRequest
from app.services import clinician_dashboard_service
from app.services import labour_web_service
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


@router.put(
    "/alerts/{alert_id}/acknowledge",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Acknowledge a specific alert"
)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    result = await clinician_dashboard_service.acknowledge_alert(db, alert_id, current_user.id)
    return create_success_response(data=result)


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


@router.get(
    "/patients",
    response_model=APIResponse[List[PatientDirectoryItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get patients assigned to the authenticated clinician"
)
async def get_my_patients(
    search: Optional[str] = None,
    tab: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    patients = await clinician_dashboard_service.get_clinician_patients(db, facility_id, current_user.id, search, tab)
    return create_success_response(data=patients)


@router.get(
    "/patients/{patient_user_id}/overview",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get patient overview — pregnancy summary, care team, emergency contact"
)
async def get_patient_overview(
    patient_user_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    overview = await clinician_dashboard_service.get_patient_overview(db, patient_user_id, current_user.id)
    return create_success_response(data=overview)


@router.get(
    "/patients/{patient_user_id}/timeline",
    response_model=APIResponse[list[TimelineItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get patient cross-module timeline"
)
async def get_patient_timeline(
    patient_user_id: uuid.UUID,
    filter: Optional[str] = "ALL",
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    timeline = await clinician_dashboard_service.get_patient_timeline(
        db, patient_user_id, current_user.id, filter, page, page_size
    )
    return create_success_response(data=timeline)


@router.get(
    "/patients/{patient_user_id}/pregnancy-vitals",
    response_model=APIResponse[list[dict]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get patient pregnancy vitals (clinician read view)"
)
async def get_patient_pregnancy_vitals(
    patient_user_id: uuid.UUID,
    filter: Optional[str] = "ALL",
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    vitals = await clinician_dashboard_service.get_patient_pregnancy_vitals(
        db, patient_user_id, current_user.id, filter, page, page_size
    )
    return create_success_response(data=vitals)


@router.get(
    "/labour/active",
    response_model=APIResponse[list[ActiveLabourSessionRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="[Clinician] Active labour sessions — assigned patients only",
)
async def get_clinician_active_labour_sessions(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    """Returns active labour sessions only for patients assigned to the authenticated clinician.
    The facility admin's unscoped version lives at GET /api/v1/labour/active."""
    sessions = await labour_web_service.get_active_sessions_for_clinician(
        db, facility_id, current_user.id
    )
    return create_success_response(data=sessions)


@router.post(
    "/patients/{patient_user_id}/notes",
    response_model=APIResponse[ClinicalNoteRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Add a clinical note for a patient",
)
async def add_patient_clinical_note(
    patient_user_id: uuid.UUID,
    data: ClinicalNoteCreateRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    note = await clinician_dashboard_service.add_clinical_note(
        db, patient_user_id, current_user.id, data.message, data.submissionId
    )
    return create_success_response(data=note)


@router.get(
    "/patients/{patient_user_id}/notes",
    response_model=APIResponse[list[ClinicalNoteRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List clinical notes for a patient",
)
async def list_patient_clinical_notes(
    patient_user_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    notes = await clinician_dashboard_service.get_clinical_notes(db, patient_user_id)
    return create_success_response(data=notes)