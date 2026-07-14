import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import (
    profile_repository,
    pregnancy_repository,
    postpartum_repository,
    cycle_repository,
)
from sqlalchemy import select
from app.models.pregnancy import PregnancyVitalsEntry, ClinicalNote
from app.models.postpartum import EpdsScreening
from app.models.facility import Facility
from app.services import medical_history_service


async def get_profile_summary(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    profile = await profile_repository.get_by_user_id(db, user_id)
    if not profile:
        return {"error": "Profile not found"}
    return {
        "current_stage": profile.current_stage.value if profile.current_stage else None,
        "preferred_language": profile.user.preferred_language if profile.user else None,
        "county": profile.user.county if profile.user else None,
        "companion_preference": profile.companion_preference.value if profile.companion_preference else None,
    }


async def get_current_pregnancy(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        return {"error": "No active pregnancy found"}
    
    # Calculate simple derived values (normally done in service layer, but we can do a quick calc or just return DB fields)
    week_number = None # Needs calculation in a real app based on LMP/Due Date
    if pregnancy.due_date:
        import datetime
        now = datetime.date.today()
        days_remaining = (pregnancy.due_date - now).days
        weeks_gestation = 40 - (days_remaining // 7)
        if 0 <= weeks_gestation <= 42:
            week_number = weeks_gestation
            
    trimester = 1
    if week_number:
        if week_number > 26:
            trimester = 3
        elif week_number > 12:
            trimester = 2

    return {
        "week_number": week_number,
        "trimester": trimester,
        "due_date": pregnancy.due_date.isoformat() if pregnancy.due_date else None,
        "is_first_pregnancy": pregnancy.is_first_pregnancy,
        "status": pregnancy.status.value if pregnancy.status else None,
    }


async def get_pregnancy_risk_score(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        return {"error": "No active pregnancy found"}
    
    score_record = await pregnancy_repository.get_latest_risk_score(db, pregnancy.id)
    if not score_record:
        return {"error": "No risk score available"}
    
    return {
        "score": score_record.score,
        "level": score_record.level.value if score_record.level else None,
        "calculated_at": score_record.calculated_at.isoformat() if score_record.calculated_at else None,
        "top_factors": score_record.factors,
    }


async def get_anc_visit_schedule(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        return {"error": "No active pregnancy found"}
    
    visits = await pregnancy_repository.list_scheduled_visits(db, pregnancy.id)
    if not visits:
        return {"error": "No visits scheduled"}
        
    completed_count = sum(1 for v in visits if v.status and v.status.value == "COMPLETED")
    missed_count = sum(1 for v in visits if v.status and v.status.value == "MISSED")
    
    next_visit = next((v for v in visits if v.status and v.status.value == "SCHEDULED"), None)
    
    return {
        "completed_count": completed_count,
        "missed_count": missed_count,
        "next_visit": {
            "label": next_visit.label,
            "scheduled_at": next_visit.scheduled_at.isoformat(),
            "purpose": next_visit.purpose
        } if next_visit else None,
    }


async def get_medical_history_summary(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    history = await medical_history_service.get_medical_history(db, user_id)
    if not history:
        return {"error": "No medical history on file"}
    
    return {
        "blood_type": f"{history.blood_type or ''}{history.rh_factor or ''}".strip(),
        "allergies": history.allergies,
        "chronic_conditions": history.chronic_conditions,
        "previous_pregnancies": history.previous_pregnancies,
    }


async def get_postpartum_status(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    baby = await postpartum_repository.get_latest_baby_profile(db, user_id)
    if not baby:
        return {"error": "No postpartum records found"}
        
    days_postpartum = None
    if baby.date_of_birth:
        import datetime
        now = datetime.date.today()
        days_postpartum = (now - baby.date_of_birth).days

    epds = await postpartum_repository.get_latest_epds_screening(db, user_id)
    
    return {
        "baby": {
            "name": baby.name,
            "date_of_birth": baby.date_of_birth.isoformat() if baby.date_of_birth else None,
            "gender": baby.gender.value if baby.gender else None,
        },
        "days_postpartum": days_postpartum,
        "latest_epds": {
            "score": epds.total_score,
            "risk_level": epds.risk_level.value if epds.risk_level else None
        } if epds else None
    }


async def get_cycle_summary(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    entries, _ = await cycle_repository.list_cycle_entries(db, user_id, page=1, page_size=1)
    if not entries:
        return {"error": "No cycle data found"}
        
    last_entry = entries[0]
    profile = await profile_repository.get_by_user_id(db, user_id)
    
    return {
        "typical_cycle_length_days": profile.typical_cycle_length_days if profile else None,
        "last_entry_start_date": last_entry.start_date.isoformat() if last_entry.start_date else None,
        "last_entry_end_date": last_entry.end_date.isoformat() if last_entry.end_date else None,
    }


async def get_nutrition_guidance(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    # Normally this would be personalized, but for now we just return a summary of available guidance
    guidance = await pregnancy_repository.list_nutrition_guidance(db)
    return {
        "guidance": [{"category": g.category.value, "title": g.title, "summary": g.summary} for g in guidance]
    }

async def get_recent_vitals(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy: return {"error": "No active pregnancy"}
    stmt = select(PregnancyVitalsEntry).where(PregnancyVitalsEntry.pregnancy_id == pregnancy.id).order_by(PregnancyVitalsEntry.created_at.desc()).limit(1)
    entry = (await db.execute(stmt)).scalars().first()
    if not entry: return {"error": "No vitals logged yet"}
    
    # We must explicitly await the lazy load of the submission to get answers
    await db.refresh(entry, ['submission'])
    return {
        "logged_at": entry.created_at.isoformat(),
        "is_flagged": entry.is_flagged,
        "vitals_data": entry.submission.answers if entry.submission else {}
    }

async def get_recent_clinical_notes(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    stmt = select(ClinicalNote).where(ClinicalNote.patient_user_id == user_id).order_by(ClinicalNote.created_at.desc()).limit(3)
    notes = (await db.execute(stmt)).scalars().all()
    if not notes: return {"error": "No clinical notes found"}
    return {
        "notes": [{"date": n.created_at.isoformat(), "message": n.message} for n in notes]
    }

async def get_mental_health_score(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    stmt = select(EpdsScreening).where(EpdsScreening.user_id == user_id).order_by(EpdsScreening.created_at.desc()).limit(1)
    epds = (await db.execute(stmt)).scalars().first()
    if not epds: return {"error": "No EPDS screening found"}
    return {
        "date": epds.created_at.isoformat(),
        "total_score": epds.total_score,
        "risk_level": epds.risk_level.value,
        "is_self_harm_flagged": epds.is_self_harm_flagged
    }

async def get_preferred_facility_details(db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    profile = await profile_repository.get_by_user_id(db, user_id)
    if not profile or not profile.preferred_facility_id:
        return {"error": "No preferred facility selected"}
        
    stmt = select(Facility).where(Facility.id == profile.preferred_facility_id)
    facility = (await db.execute(stmt)).scalars().first()
    if not facility: return {"error": "Facility details not found"}
    
    return {
        "name": facility.name,
        "type": facility.type.value,
        "phone_number": facility.phone_number,
        "address": facility.address,
        "services": facility.services_offered
    }

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_profile_summary",
            "description": "Get a summary of the mother's profile, including her current stage (PREGNANT, POSTPARTUM) and preferences.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_pregnancy",
            "description": "Get the mother's active pregnancy status, including week number, trimester, and due date.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pregnancy_risk_score",
            "description": "Get the mother's latest pregnancy risk score and level.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_anc_visit_schedule",
            "description": "Get a summary of the mother's antenatal care (ANC) visits, including the next scheduled visit.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_medical_history_summary",
            "description": "Get a summary of the mother's medical history, such as blood type, allergies, and chronic conditions.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_postpartum_status",
            "description": "Get the mother's postpartum status, including information about her baby and latest EPDS screening.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cycle_summary",
            "description": "Get a summary of the mother's menstrual cycle, including the start date of her last entry.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_nutrition_guidance",
            "description": "Get general nutrition guidance for pregnant mothers.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_vitals",
            "description": "Get the mother's most recently logged vitals (e.g. blood pressure, weight, heart rate).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_clinical_notes",
            "description": "Get the most recent notes left by the mother's clinician or doctor.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_mental_health_score",
            "description": "Get the mother's latest EPDS mental health screening score.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_preferred_facility_details",
            "description": "Get the contact details and services of the mother's preferred hospital/clinic.",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]

TOOL_DISPATCH = {
    "get_profile_summary": get_profile_summary,
    "get_current_pregnancy": get_current_pregnancy,
    "get_pregnancy_risk_score": get_pregnancy_risk_score,
    "get_anc_visit_schedule": get_anc_visit_schedule,
    "get_medical_history_summary": get_medical_history_summary,
    "get_postpartum_status": get_postpartum_status,
    "get_cycle_summary": get_cycle_summary,
    "get_nutrition_guidance": get_nutrition_guidance,
    "get_recent_vitals": get_recent_vitals,
    "get_recent_clinical_notes": get_recent_clinical_notes,
    "get_mental_health_score": get_mental_health_score,
    "get_preferred_facility_details": get_preferred_facility_details,
}

async def execute_tool(name: str, db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    handler = TOOL_DISPATCH.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    return await handler(db, user_id=user_id)
