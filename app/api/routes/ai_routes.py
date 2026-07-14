import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.profile import CompanionPreference
from app.schemas.ai import ContextSummaryResponse
from app.services.ai.context_tools import (
    get_profile_summary, get_current_pregnancy, get_pregnancy_risk_score,
    get_anc_visit_schedule, get_medical_history_summary
)
from app.repositories import profile_repository
from app.utils.exceptions import ForbiddenError
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter()

@router.get("/context-summary", response_model=APIResponse[ContextSummaryResponse])
async def get_context_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != UserRole.USER:
        raise ForbiddenError(message="Only mothers can access the AI companion.")
        
    profile = await profile_repository.get_by_user_id(db, current_user.id)
    if not profile or profile.companion_preference not in (CompanionPreference.AI_DOC, CompanionPreference.BOTH):
        raise ForbiddenError(message="AI Companion is not enabled for this profile.")
        
    user_id = current_user.id
    
    # Gather data from the tools
    summary_parts = []
    
    prof_data = await get_profile_summary(db, user_id=user_id)
    if not prof_data.get("error"):
        summary_parts.append(f"Stage: {prof_data.get('current_stage', 'Unknown')}.")
        
    preg_data = await get_current_pregnancy(db, user_id=user_id)
    if not preg_data.get("error"):
        summary_parts.append(f"Pregnancy: week {preg_data.get('week_number', 'unknown')}, {preg_data.get('trimester', 'unknown')} trimester.")
        
    risk_data = await get_pregnancy_risk_score(db, user_id=user_id)
    if not risk_data.get("error"):
        summary_parts.append(f"Risk level: {risk_data.get('level', 'Unknown')} (Score: {risk_data.get('score', 0)}).")
        
    anc_data = await get_anc_visit_schedule(db, user_id=user_id)
    if not anc_data.get("error"):
        next_visit = anc_data.get('next_visit')
        if next_visit:
            summary_parts.append(f"Next ANC visit: {next_visit.get('scheduled_at')}.")
            
    med_data = await get_medical_history_summary(db, user_id=user_id)
    if not med_data.get("error"):
        summary_parts.append(f"History: Prev pregnancies: {med_data.get('previous_pregnancies', 0)}.")

    summary_string = " ".join(summary_parts) if summary_parts else "No significant context available."
    
    return create_success_response(data=ContextSummaryResponse(summary=summary_string))
