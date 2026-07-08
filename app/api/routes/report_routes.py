import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead, PopulationSnapshot
from app.services import report_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
}

@router.get(
    "/population-snapshot", 
    response_model=APIResponse[PopulationSnapshot],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get population snapshot"
)
async def get_population_snapshot(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    snapshot = await report_service.get_population_snapshot(db, facility_id)
    return create_success_response(data=snapshot)


@router.post(
    "/", 
    response_model=APIResponse[ReportRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Generate a report"
)
async def generate_report(
    req: ReportCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    report = await report_service.generate_report_async(db, facility_id, current_user.id, req)
    return create_success_response(data=report)


@router.get(
    "/", 
    response_model=APIResponse[List[ReportRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List generated reports"
)
async def list_reports(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context)
):
    reports = await report_service.list_reports(db, facility_id, limit, offset)
    return create_success_response(data=reports)


@router.get(
    "/{report_id}/download", 
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get report download URL"
)
async def download_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician)
):
    url = await report_service.download_report(db, report_id)
    if not url:
        raise HTTPException(status_code=404, detail="Report not found or not ready")
    return create_success_response(data={"downloadUrl": url})
