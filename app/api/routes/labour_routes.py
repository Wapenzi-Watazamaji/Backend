import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.labour import (
    LabourSessionCreate, LabourSessionClose, LabourSessionRead,
    DilationReadingCreate, FhrReadingCreate, MaternalBpReadingCreate,
    ContractionReadingCreate, LabourReadingRead,
    PartographRead, LabourAlertRead, AcknowledgeAlertResponse,
    EscalateAlertRequest, ResuscitationProtocolRead,
    ResuscitationLogCreate, ResuscitationLogRead,
)
from app.services import labour_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
    422: {"model": APIResponse[None], "description": "Validation Error"},
}


@router.post(
    "/sessions",
    response_model=APIResponse[LabourSessionRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Open a new labour session",
)
async def create_session(
    data: LabourSessionCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    session = await labour_service.create_session(db, current_user.id, data)
    return create_success_response(data=session)


@router.get(
    "/sessions/{session_id}",
    response_model=APIResponse[LabourSessionRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get a labour session",
)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    session = await labour_service.get_session(db, session_id)
    return create_success_response(data=session)


@router.put(
    "/sessions/{session_id}/close",
    response_model=APIResponse[LabourSessionRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Close a labour session",
)
async def close_session(
    session_id: uuid.UUID,
    data: LabourSessionClose,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    session = await labour_service.close_session(db, session_id, data)
    return create_success_response(data=session)


@router.post(
    "/sessions/{session_id}/readings/dilation",
    response_model=APIResponse[LabourReadingRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Log a cervical dilation reading",
)
async def add_dilation_reading(
    session_id: uuid.UUID,
    data: DilationReadingCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    reading = await labour_service.add_dilation_reading(db, session_id, data)
    return create_success_response(data=reading)


@router.post(
    "/sessions/{session_id}/readings/fhr",
    response_model=APIResponse[LabourReadingRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Log a fetal heart rate reading",
)
async def add_fhr_reading(
    session_id: uuid.UUID,
    data: FhrReadingCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    reading = await labour_service.add_fhr_reading(db, session_id, data)
    return create_success_response(data=reading)


@router.post(
    "/sessions/{session_id}/readings/maternal-vitals",
    response_model=APIResponse[LabourReadingRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Log maternal blood pressure",
)
async def add_maternal_bp_reading(
    session_id: uuid.UUID,
    data: MaternalBpReadingCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    reading = await labour_service.add_maternal_bp_reading(db, session_id, data)
    return create_success_response(data=reading)


@router.post(
    "/sessions/{session_id}/readings/contractions",
    response_model=APIResponse[LabourReadingRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Log a contraction reading",
)
async def add_contraction_reading(
    session_id: uuid.UUID,
    data: ContractionReadingCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    reading = await labour_service.add_contraction_reading(db, session_id, data)
    return create_success_response(data=reading)


@router.get(
    "/sessions/{session_id}/partograph",
    response_model=APIResponse[PartographRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get the full partograph data for a session",
)
async def get_partograph(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    data = await labour_service.get_partograph(db, session_id)
    return create_success_response(data=data)


@router.get(
    "/sessions/{session_id}/alerts",
    response_model=APIResponse[list[LabourAlertRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List alerts for a labour session",
)
async def list_alerts(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    alerts = await labour_service.list_alerts(db, session_id)
    return create_success_response(data=alerts)


@router.post(
    "/sessions/{session_id}/alerts/{alert_id}/acknowledge",
    response_model=APIResponse[LabourAlertRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Acknowledge a labour alert",
)
async def acknowledge_alert(
    session_id: uuid.UUID,
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    alert = await labour_service.acknowledge_alert(db, session_id, alert_id, current_user.id)
    return create_success_response(data=alert)


@router.post(
    "/sessions/{session_id}/alerts/{alert_id}/escalate",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Escalate a labour alert",
)
async def escalate_alert(
    session_id: uuid.UUID,
    alert_id: uuid.UUID,
    data: EscalateAlertRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    result = await labour_service.escalate_alert(db, session_id, alert_id, data.escalateTo)
    return create_success_response(data=result)


@router.get(
    "/resuscitation-protocol",
    response_model=APIResponse[ResuscitationProtocolRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get the WHO neonatal resuscitation protocol",
)
async def get_resuscitation_protocol(
    current_user: User = Depends(deps.get_current_user),
):
    protocol = labour_service.get_resuscitation_protocol()
    return create_success_response(data=protocol)


@router.post(
    "/sessions/{session_id}/resuscitation-log",
    response_model=APIResponse[ResuscitationLogRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Log a completed resuscitation step",
)
async def create_resuscitation_log(
    session_id: uuid.UUID,
    data: ResuscitationLogCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    log = await labour_service.create_resuscitation_log(db, session_id, data)
    return create_success_response(data=log)
