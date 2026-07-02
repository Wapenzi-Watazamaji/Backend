import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.models.cycle import FormContext
from typing import Any
from app.schemas.cycle import (
    FormTemplateRead, FormTemplateCreate, FormTemplateUpdate, CycleEntryCreate, CycleEntryUpdate, CycleEntryRead,
    SymptomCreate, FormSubmissionRead, PbacItemCreate, PbacItemRead, PbacScoreRead,
    PredictionRead, TrendRead, HmbStatusRead, HmbAcknowledgeRequest,
)
from app.services import cycle_service
from app.repositories import cycle_repository
from app.utils.exceptions import create_success_response, APIResponse, NotFoundError, ForbiddenError

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    404: {"model": APIResponse[None], "description": "Not Found"},
    422: {"model": APIResponse[None], "description": "Validation Error"},
}


@router.get("/entries/form-template", response_model=APIResponse[FormTemplateRead], responses=STANDARD_ERROR_RESPONSES)
async def get_cycle_entry_form_template(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    facility_id: Optional[uuid.UUID] = Query(None, description="Preferred facility ID to get a customized template"),
):
    template = await cycle_repository.get_active_form_template(db, FormContext.CYCLE_ENTRY, facility_id=facility_id)
    if not template:
        raise NotFoundError(message="No active form template found for CYCLE_ENTRY")
    return create_success_response(data=template)

@router.post("/form-templates", response_model=APIResponse[FormTemplateRead], status_code=status.HTTP_201_CREATED, responses=STANDARD_ERROR_RESPONSES)
async def create_form_template(
    template_in: FormTemplateCreate,
    requester_facility_id: uuid.UUID = Depends(deps.get_facility_context),
    current_user: User = Depends(deps.require_facility_admin),
    db: AsyncSession = Depends(deps.get_db),
):
    template_data = template_in.model_dump()
    template_data["facility_id"] = requester_facility_id
    
    # Deactivate older versions for this facility and context if needed
    # Or just let them coexist. For simplicity, just create.
    template = await cycle_repository.create_form_template(db, template_data)
    return create_success_response(data=template, message="Form template created successfully")


@router.put("/form-templates/{template_id}", response_model=APIResponse[FormTemplateRead], responses=STANDARD_ERROR_RESPONSES)
async def update_form_template(
    template_id: uuid.UUID,
    template_in: FormTemplateUpdate,
    requester_facility_id: uuid.UUID = Depends(deps.get_facility_context),
    current_user: User = Depends(deps.require_facility_admin),
    db: AsyncSession = Depends(deps.get_db),
):
    template = await cycle_repository.get_form_template_by_id(db, template_id)
    if not template:
        raise NotFoundError(message="Form template not found")
        
    if template.facility_id != requester_facility_id:
        raise ForbiddenError(message="You can only update form templates for your own facility")
        
    update_data = template_in.model_dump(exclude_unset=True)
    updated_template = await cycle_repository.update_form_template(db, template, update_data)
    return create_success_response(data=updated_template, message="Form template updated successfully")


@router.post("/entries", response_model=APIResponse[CycleEntryRead], status_code=status.HTTP_201_CREATED, responses=STANDARD_ERROR_RESPONSES)
async def create_cycle_entry(
    entry_in: CycleEntryCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    entry = await cycle_service.create_cycle_entry(db, current_user.id, entry_in)
    return create_success_response(data=entry)


@router.get("/entries", response_model=APIResponse[list[CycleEntryRead]], responses=STANDARD_ERROR_RESPONSES)
async def list_cycle_entries(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    entries, total = await cycle_service.list_cycle_entries(db, current_user.id, from_date, to_date, page, pageSize)
    meta = {"page": page, "pageSize": pageSize, "total": total, "totalPages": -(-total // pageSize)}
    return create_success_response(data=entries, meta=meta)


@router.get("/entries/{entry_id}", response_model=APIResponse[CycleEntryRead], responses=STANDARD_ERROR_RESPONSES)
async def get_cycle_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    entry = await cycle_service.get_cycle_entry(db, entry_id, current_user.id)
    return create_success_response(data=entry)


@router.put("/entries/{entry_id}", response_model=APIResponse[CycleEntryRead], responses=STANDARD_ERROR_RESPONSES)
async def update_cycle_entry(
    entry_id: uuid.UUID,
    entry_in: CycleEntryUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    entry = await cycle_service.update_cycle_entry(db, entry_id, current_user.id, entry_in)
    return create_success_response(data=entry)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, responses=STANDARD_ERROR_RESPONSES)
async def delete_cycle_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    await cycle_service.delete_cycle_entry(db, entry_id, current_user.id)


@router.post("/entries/{entry_id}/pbac-items", response_model=APIResponse[PbacItemRead], status_code=status.HTTP_201_CREATED, responses=STANDARD_ERROR_RESPONSES)
async def add_pbac_item(
    entry_id: uuid.UUID,
    item_in: PbacItemCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    item = await cycle_service.add_pbac_item(db, entry_id, current_user.id, item_in)
    return create_success_response(data=item)


@router.get("/entries/{entry_id}/pbac-items", response_model=APIResponse[list[PbacItemRead]], responses=STANDARD_ERROR_RESPONSES)
async def list_pbac_items(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    items = await cycle_service.list_pbac_items(db, entry_id, current_user.id)
    return create_success_response(data=items)


@router.get("/entries/{entry_id}/pbac-score", response_model=APIResponse[PbacScoreRead], responses=STANDARD_ERROR_RESPONSES)
async def get_pbac_score(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    score_data = await cycle_service.get_pbac_score(db, entry_id, current_user.id)
    return create_success_response(data=score_data)


@router.get("/symptoms/form-template", response_model=APIResponse[FormTemplateRead], responses=STANDARD_ERROR_RESPONSES)
async def get_symptom_form_template(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    facility_id: Optional[uuid.UUID] = Query(None, description="Preferred facility ID to get a customized template"),
):
    template = await cycle_repository.get_active_form_template(db, FormContext.CYCLE_SYMPTOM, facility_id=facility_id)
    if not template:
        raise NotFoundError(message="No active form template found for CYCLE_SYMPTOM")
    return create_success_response(data=template)


@router.post("/symptoms", response_model=APIResponse[FormSubmissionRead], status_code=status.HTTP_201_CREATED, responses=STANDARD_ERROR_RESPONSES)
async def create_symptom(
    symptom_in: SymptomCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    submission = await cycle_service.create_symptom(db, current_user.id, symptom_in)
    return create_success_response(data=submission)


@router.get("/symptoms", response_model=APIResponse[list[FormSubmissionRead]], responses=STANDARD_ERROR_RESPONSES)
async def list_symptoms(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    subs, total = await cycle_service.list_symptoms(db, current_user.id, from_date, to_date, page, pageSize)
    meta = {"page": page, "pageSize": pageSize, "total": total, "totalPages": -(-total // pageSize)}
    return create_success_response(data=subs, meta=meta)


@router.get("/predictions", response_model=APIResponse[PredictionRead], responses=STANDARD_ERROR_RESPONSES)
async def get_predictions(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    predictions = await cycle_service.get_predictions(db, current_user.id)
    return create_success_response(data=predictions)


@router.get("/trends", response_model=APIResponse[TrendRead], responses=STANDARD_ERROR_RESPONSES)
async def get_cycle_trends(
    months: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    trend_data = await cycle_service.get_trends(db, current_user.id, months)
    return create_success_response(data=trend_data)


@router.get("/hmb-status", response_model=APIResponse[HmbStatusRead], responses=STANDARD_ERROR_RESPONSES)
async def get_hmb_status(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    status_data = await cycle_service.get_hmb_status(db, current_user.id)
    return create_success_response(data=status_data)


@router.post("/hmb-acknowledge", response_model=APIResponse[HmbStatusRead], responses=STANDARD_ERROR_RESPONSES)
async def acknowledge_hmb_alert(
    ack_in: HmbAcknowledgeRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    result = await cycle_service.acknowledge_hmb(db, current_user.id, ack_in.action)
    return create_success_response(data=result)
