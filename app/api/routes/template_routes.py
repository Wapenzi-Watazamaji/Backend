from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.template import FormTemplateRead, CarePathwayTemplateRead, FormTemplateCreate, FormTemplateUpdate
from app.services import template_service
from app.utils.exceptions import APIResponse, create_success_response, NotFoundError, ForbiddenError
import uuid
from fastapi import status

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
}

@router.get("/forms", response_model=APIResponse[list[FormTemplateRead]], responses=STANDARD_ERROR_RESPONSES, summary="List all Form Templates")
async def get_all_form_templates(
    context: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    templates = await template_service.get_all_form_templates(db, context)
    return create_success_response(data=templates)

@router.get("/care-pathways", response_model=APIResponse[list[CarePathwayTemplateRead]], responses=STANDARD_ERROR_RESPONSES, summary="List all Care Pathway Templates")
async def get_all_care_pathway_templates(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    templates = await template_service.get_all_care_pathways(db)
    return create_success_response(data=templates)

@router.post("/forms", response_model=APIResponse[FormTemplateRead], status_code=status.HTTP_201_CREATED, responses=STANDARD_ERROR_RESPONSES)
async def create_form_template(
    template_in: FormTemplateCreate,
    requester_facility_id: uuid.UUID = Depends(deps.get_facility_context),
    current_user: User = Depends(deps.require_facility_admin),
    db: AsyncSession = Depends(deps.get_db),
):
    template_data = template_in.model_dump()
    template_data["facility_id"] = requester_facility_id
    
    template = await template_service.create_form_template(db, template_data)
    return create_success_response(data=template, message="Form template created successfully")

@router.put("/forms/{template_id}", response_model=APIResponse[FormTemplateRead], responses=STANDARD_ERROR_RESPONSES)
async def update_form_template(
    template_id: uuid.UUID,
    template_in: FormTemplateUpdate,
    requester_facility_id: uuid.UUID = Depends(deps.get_facility_context),
    current_user: User = Depends(deps.require_facility_admin),
    db: AsyncSession = Depends(deps.get_db),
):
    template = await template_service.get_form_template_by_id(db, template_id)
    if not template:
        raise NotFoundError(message="Form template not found")
        
    if template.facility_id != requester_facility_id:
        raise ForbiddenError(message="You can only update form templates for your own facility")
        
    update_data = template_in.model_dump(exclude_unset=True)
    updated_template = await template_service.update_form_template(db, template, update_data)
    return create_success_response(data=updated_template, message="Form template updated successfully")

