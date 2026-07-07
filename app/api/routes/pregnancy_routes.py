import uuid
from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.models.pregnancy import NutritionCategory
from app.schemas.pregnancy import (
    PregnancyStartRequest, PregnancyUpdateRequest, PregnancyEndRequest,
    PregnancyRecordRead, WeekInfoRead, VitalsCreateRequest, VitalsUpdateRequest,
    VitalsEntryRead, FeedbackCreateRequest, FeedbackRead, VisitRead,
    ManualVisitCreateRequest, VisitUpdateRequest, NutritionGuidanceRead,
    RiskScoreRead, RiskScoreHistoryItem, FormTemplateRead, RiskScoreOverrideRequest,
)
from app.services import pregnancy_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
    409: {"model": APIResponse[None], "description": "Conflict"},
    422: {"model": APIResponse[None], "description": "Validation Error"},
}


@router.post("/start", response_model=APIResponse[PregnancyRecordRead], status_code=status.HTTP_201_CREATED, responses=STANDARD_ERROR_RESPONSES)
async def start_pregnancy(
    data: PregnancyStartRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    pregnancy = await pregnancy_service.start_pregnancy(db, current_user.id, data)
    return create_success_response(data=pregnancy)


@router.get("/current", response_model=APIResponse[PregnancyRecordRead], responses=STANDARD_ERROR_RESPONSES)
async def get_current_pregnancy(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    pregnancy = await pregnancy_service.get_current_pregnancy(db, current_user.id)
    return create_success_response(data=pregnancy)


@router.put("/current", response_model=APIResponse[PregnancyRecordRead], responses=STANDARD_ERROR_RESPONSES)
async def update_current_pregnancy(
    data: PregnancyUpdateRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    pregnancy = await pregnancy_service.update_pregnancy(db, current_user.id, data)
    return create_success_response(data=pregnancy)


@router.post("/end", response_model=APIResponse[PregnancyRecordRead], responses=STANDARD_ERROR_RESPONSES)
async def end_pregnancy(
    data: PregnancyEndRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    pregnancy = await pregnancy_service.end_pregnancy(db, current_user.id, data)
    return create_success_response(data=pregnancy)


@router.get("/week-info", response_model=APIResponse[WeekInfoRead], responses=STANDARD_ERROR_RESPONSES)
async def get_week_info(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    info = await pregnancy_service.get_week_info(db, current_user.id)
    return create_success_response(data=info)


@router.get("/vitals/form-template", response_model=APIResponse[FormTemplateRead], responses=STANDARD_ERROR_RESPONSES)
async def get_vitals_form_template(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    template = await pregnancy_service.get_vitals_form_template(db)
    return create_success_response(data=template)


@router.post("/vitals", response_model=APIResponse[VitalsEntryRead], status_code=status.HTTP_201_CREATED, responses=STANDARD_ERROR_RESPONSES)
async def create_vitals(
    data: VitalsCreateRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    entry = await pregnancy_service.create_vitals(db, current_user.id, data)
    return create_success_response(data=entry)


@router.get("/vitals", response_model=APIResponse[list[VitalsEntryRead]], responses=STANDARD_ERROR_RESPONSES)
async def list_vitals(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    flaggedOnly: bool = Query(False),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    entries, total = await pregnancy_service.list_vitals(db, current_user.id, flaggedOnly, page, pageSize)
    meta = {"page": page, "pageSize": pageSize, "total": total, "totalPages": -(-total // pageSize)}
    return create_success_response(data=entries, meta=meta)


@router.get("/vitals/{entry_id}", response_model=APIResponse[VitalsEntryRead], responses=STANDARD_ERROR_RESPONSES)
async def get_vitals_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    entry = await pregnancy_service.get_vitals_entry(db, entry_id, current_user.id)
    return create_success_response(data=entry)


@router.put("/vitals/{entry_id}", response_model=APIResponse[VitalsEntryRead], responses=STANDARD_ERROR_RESPONSES)
async def update_vitals_entry(
    entry_id: uuid.UUID,
    data: VitalsUpdateRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    entry = await pregnancy_service.update_vitals(db, entry_id, current_user.id, data)
    return create_success_response(data=entry)


@router.get("/patients/{patient_id}/vitals", response_model=APIResponse[list[VitalsEntryRead]], responses=STANDARD_ERROR_RESPONSES)
async def get_patient_vitals(
    patient_id: uuid.UUID,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    entries, total = await pregnancy_service.get_patient_vitals(db, patient_id, page, pageSize)
    meta = {"page": page, "pageSize": pageSize, "total": total, "totalPages": -(-total // pageSize)}
    return create_success_response(data=entries, meta=meta)


@router.post("/vitals/{entry_id}/feedback", response_model=APIResponse[FeedbackRead], status_code=status.HTTP_201_CREATED, responses=STANDARD_ERROR_RESPONSES)
async def create_vitals_feedback(
    entry_id: uuid.UUID,
    data: FeedbackCreateRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
):
    feedback = await pregnancy_service.create_vitals_feedback(db, entry_id, current_user.id, data)
    return create_success_response(data=feedback)


@router.get("/vitals/{entry_id}/feedback", response_model=APIResponse[list[FeedbackRead]], responses=STANDARD_ERROR_RESPONSES)
async def list_vitals_feedback(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    feedback = await pregnancy_service.list_vitals_feedback(db, entry_id)
    return create_success_response(data=feedback)


@router.get("/anc-visits", response_model=APIResponse[list[VisitRead]], responses=STANDARD_ERROR_RESPONSES)
async def list_anc_visits(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    visits = await pregnancy_service.list_anc_visits(db, current_user.id)
    return create_success_response(data=visits)


@router.post(
    "/anc-visits/manual/{patient_id}",
    response_model=APIResponse[VisitRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
)
async def create_manual_visit(
    patient_id: uuid.UUID,
    data: ManualVisitCreateRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    visit = await pregnancy_service.create_manual_anc_visit(
        db, patient_id, data, facility_id
    )
    return create_success_response(data=visit)


@router.put(
    "/anc-visits/{visit_id}/patient/{user_id}",
    response_model=APIResponse[VisitRead],
    responses=STANDARD_ERROR_RESPONSES,
)
async def update_anc_visit(
    visit_id: uuid.UUID,
    user_id: uuid.UUID,
    data: VisitUpdateRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    visit = await pregnancy_service.update_anc_visit(
        db, visit_id, patient_id=user_id, data=data
    )
    return create_success_response(data=visit)


@router.get("/nutrition-guidance", response_model=APIResponse[list[NutritionGuidanceRead]], responses=STANDARD_ERROR_RESPONSES)
async def get_nutrition_guidance(
    category: Optional[NutritionCategory] = Query(None),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    guidance = await pregnancy_service.list_nutrition_guidance(db, category)
    return create_success_response(data=guidance)


@router.get("/risk-score", response_model=APIResponse[RiskScoreRead], responses=STANDARD_ERROR_RESPONSES)
async def get_risk_score(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    score = await pregnancy_service.get_risk_score(db, current_user.id)
    return create_success_response(data=score)


@router.get("/risk-score/history", response_model=APIResponse[list[RiskScoreHistoryItem]], responses=STANDARD_ERROR_RESPONSES)
async def get_risk_score_history(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    history = await pregnancy_service.get_risk_score_history(db, current_user.id)
    return create_success_response(data=history)


@router.put(
    "/patients/{patient_id}/risk-score/override",
    response_model=APIResponse[RiskScoreRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Clinician: override risk level for a patient",
)
async def override_risk_score(
    patient_id: uuid.UUID,
    data: RiskScoreOverrideRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    score = await pregnancy_service.override_risk_score(db, patient_id, current_user.id, data)
    return create_success_response(data=score)
