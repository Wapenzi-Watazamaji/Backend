import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.pregnancy import (
    PregnancyRecord, PregnancyStatus, PregnancyVitalsEntry, VitalsFeedback,
    ScheduledVisit, PregnancyRiskScore, WeekInfo, NutritionGuidance,
    VisitStatus, RiskLevel, NutritionCategory,
)
from app.schemas.pregnancy import (
    ManualVisitCreateRequest,
    VisitUpdateRequest
)
from app.models.profile import CurrentStage, Profile
from app.models.cycle import FormContext
from app.repositories import pregnancy_repository, cycle_repository
from app.services.cycle_service import validate_answers_against_template
from app.utils.exceptions import (
    NotFoundError, NoActivePregnancyError, ActivePregnancyExistsError, ForbiddenError,
)



MOH_ANC_PATHWAY_ID = "path_anc_moh_v1"

RISK_FACTORS_CONFIG = [
    {
        "key": "BLEEDING",
        "label": "Vaginal bleeding reported",
        "weight": 40,
        "severity": "CRITICAL",
        "description": "Patient reported vaginal bleeding",
    },
    {
        "key": "HIGH_BLOOD_PRESSURE",
        "label": "High blood pressure",
        "weight": 30,
        "severity": "CRITICAL",
        "description": "Blood pressure reading exceeds safe threshold",
    },
    {
        "key": "REDUCED_FETAL_MOVEMENT",
        "label": "Reduced fetal movement reported",
        "weight": 25,
        "severity": "WARNING",
        "description": "Patient reported feeling the baby move significantly less than usual",
    },
    {
        "key": "SEVERE_HEADACHE",
        "label": "Severe headache",
        "weight": 20,
        "severity": "WARNING",
        "description": "Patient reported a persistent severe headache",
    },
    {
        "key": "SEVERE_SWELLING",
        "label": "Severe swelling",
        "weight": 20,
        "severity": "WARNING",
        "description": "Patient reported severe ankle or facial swelling",
    },
    {
        "key": "FEVER",
        "label": "Fever",
        "weight": 15,
        "severity": "WARNING",
        "description": "Patient temperature is above normal range",
    },
]


def _calculate_due_date(lmp: date) -> date:
    return lmp + timedelta(days=280)


def _calculate_lmp_from_due_date(due_date: date) -> date:
    return due_date - timedelta(days=280)


def _get_current_week(lmp: date) -> int:
    days = (date.today() - lmp).days
    return max(1, min(42, days // 7 + 1))


def _determine_flagging(answers: dict, template_fields: list) -> tuple[bool, list[str]]:
    flagged_reasons = []
    for field in template_fields:
        key = field.get("key")
        value = answers.get(key)
        if value is None:
            continue
        flagging_options = field.get("flaggingOptions", {})
        if not flagging_options:
            continue

        if isinstance(value, (int, float)):
            if "min" in flagging_options and value < flagging_options["min"]:
                flagged_reasons.append(f"{key} below minimum threshold ({flagging_options['min']})")
            if "max" in flagging_options and value > flagging_options["max"]:
                flagged_reasons.append(f"{key} above maximum threshold ({flagging_options['max']})")

        flag_values = flagging_options.get("flagValues", [])
        if flag_values:
            if isinstance(value, list):
                matched = [v for v in value if v in flag_values]
                for v in matched:
                    flagged_reasons.append(f"{key}: {v} flagged")
            elif value in flag_values:
                flagged_reasons.append(f"{key}: {value} flagged")

    return len(flagged_reasons) > 0, flagged_reasons


async def _update_profile_stage(db: AsyncSession, user_id: uuid.UUID, stage: CurrentStage) -> None:
    stmt = select(Profile).where(Profile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()
    if profile:
        profile.current_stage = stage
        await db.flush()


async def _generate_anc_visits(db: AsyncSession, pregnancy_id: uuid.UUID, lmp: date) -> None:
    pathway = await pregnancy_repository.get_care_pathway_template(db, MOH_ANC_PATHWAY_ID)
    if not pathway:
        return
    for milestone in pathway.milestones:
        scheduled_date = lmp + timedelta(weeks=milestone["triggerWeek"])
        scheduled_at = datetime.combine(scheduled_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        await pregnancy_repository.create_scheduled_visit(db, {
            "pregnancy_id": pregnancy_id,
            "pathway_template_id": MOH_ANC_PATHWAY_ID,
            "milestone_order": milestone["order"],
            "label": milestone["label"],
            "scheduled_at": scheduled_at,
            "status": VisitStatus.SCHEDULED,
        })


async def _recalculate_risk_score(
    db: AsyncSession, user_id: uuid.UUID, pregnancy_id: uuid.UUID
) -> PregnancyRiskScore:
    flagged_entries = await pregnancy_repository.get_all_flagged_vitals(db, pregnancy_id)

    all_flagged_strings: list[str] = []
    for entry in flagged_entries:
        all_flagged_strings.extend(entry.flagged_reasons)

    active_factors = []
    total_score = 0
    matched_keys = set()

    for cfg in RISK_FACTORS_CONFIG:
        key = cfg["key"]
        hit = any(key in reason for reason in all_flagged_strings)
        if hit:
            active_factors.append({
                "label": cfg["label"],
                "weight": cfg["weight"],
                "severity": cfg["severity"],
                "description": cfg["description"],
            })
            total_score += cfg["weight"]
            matched_keys.add(key)

    if "HIGH_BLOOD_PRESSURE" not in matched_keys and flagged_entries:
        active_factors.append({
            "label": "Blood pressure within normal range",
            "weight": 0,
            "severity": "SUCCESS",
            "description": "Consistent readings across recent entries",
        })

    total_score = min(total_score, 100)
    if total_score <= 30:
        level = RiskLevel.LOW
    elif total_score <= 60:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.HIGH

    return await pregnancy_repository.save_risk_score(db, {
        "pregnancy_id": pregnancy_id,
        "user_id": user_id,
        "score": total_score,
        "level": level,
        "factors": active_factors,
        "calculated_at": datetime.now(timezone.utc),
    })


async def start_pregnancy(db: AsyncSession, user_id: uuid.UUID, data) -> PregnancyRecord:
    existing = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if existing:
        raise ActivePregnancyExistsError(message="You already have an active pregnancy record")

    if data.dateInputType == "LMP":
        lmp = data.lastMenstrualPeriod
        due_date = _calculate_due_date(lmp)
    else:
        due_date = data.dueDate
        lmp = _calculate_lmp_from_due_date(due_date)

    pregnancy = await pregnancy_repository.create_pregnancy(db, {
        "user_id": user_id,
        "last_menstrual_period": lmp,
        "due_date": due_date,
        "is_first_pregnancy": data.isFirstPregnancy,
        "status": PregnancyStatus.ACTIVE,
    })

    await _update_profile_stage(db, user_id, CurrentStage.PREGNANT)
    await _generate_anc_visits(db, pregnancy.id, lmp)
    await db.commit()
    await db.refresh(pregnancy)
    return pregnancy


async def get_current_pregnancy(db: AsyncSession, user_id: uuid.UUID) -> PregnancyRecord:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")
    return pregnancy


async def update_pregnancy(db: AsyncSession, user_id: uuid.UUID, data) -> PregnancyRecord:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")
    updated = await pregnancy_repository.update_pregnancy(db, pregnancy, {"due_date": data.dueDate})
    await db.commit()
    await db.refresh(updated)
    return updated


async def end_pregnancy(db: AsyncSession, user_id: uuid.UUID, data) -> PregnancyRecord:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")
    updated = await pregnancy_repository.update_pregnancy(db, pregnancy, {
        "status": PregnancyStatus.ENDED,
        "outcome": data.outcome,
        "ended_at": data.endedAt,
    })
    await _update_profile_stage(db, user_id, CurrentStage.POSTPARTUM)
    await db.commit()
    await db.refresh(updated)
    return updated


async def get_week_info(db: AsyncSession, user_id: uuid.UUID) -> dict:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")
    week = _get_current_week(pregnancy.last_menstrual_period)
    info = await pregnancy_repository.get_week_info(db, week)
    if not info:
        trimester = 1 if week <= 12 else (2 if week <= 26 else 3)
        return {
            "weekNumber": week,
            "trimester": trimester,
            "babySizeComparison": "Information not available",
            "developmentNote": "Your baby is growing and developing.",
            "imageUrl": None,
        }
    return {
        "weekNumber": info.week_number,
        "trimester": info.trimester,
        "babySizeComparison": info.baby_size_comparison,
        "developmentNote": info.development_note,
        "imageUrl": info.image_url,
    }


async def get_vitals_form_template(db: AsyncSession):
    template = await cycle_repository.get_active_form_template(db, FormContext.PREGNANCY_VITALS)
    if not template:
        raise NotFoundError(message="No active pregnancy vitals template found")
    return template


async def create_vitals(db: AsyncSession, user_id: uuid.UUID, data) -> PregnancyVitalsEntry:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")

    template = await cycle_repository.get_form_template_by_slug(db, data.templateSlug)
    if not template or template.context != FormContext.PREGNANCY_VITALS:
        raise NotFoundError(message=f"Form template '{data.templateSlug}' not found")

    validate_answers_against_template(template, data.answers)
    template_fields = template.fields.get("fields", [])
    is_flagged, flagged_reasons = _determine_flagging(data.answers, template_fields)

    submission = await cycle_repository.create_submission(db, {
        "template_id": template.id,
        "user_id": user_id,
        "context": FormContext.PREGNANCY_VITALS,
        "answers": data.answers,
        "client_generated_id": data.clientGeneratedId,
        "client_created_at": data.clientCreatedAt,
    })

    entry = await pregnancy_repository.create_vitals_entry(db, {
        "pregnancy_id": pregnancy.id,
        "submission_id": submission.id,
        "is_flagged": is_flagged,
        "flagged_reasons": flagged_reasons,
    })

    await _recalculate_risk_score(db, user_id, pregnancy.id)
    await db.commit()
    await db.refresh(entry)
    entry.submission = submission
    return entry


async def list_vitals(
    db: AsyncSession, user_id: uuid.UUID, flagged_only: bool, page: int, page_size: int
) -> tuple[list[PregnancyVitalsEntry], int]:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")
    return await pregnancy_repository.list_vitals_entries(db, pregnancy.id, flagged_only, page, page_size)


async def get_vitals_entry(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID) -> PregnancyVitalsEntry:
    entry = await pregnancy_repository.get_vitals_entry_by_id(db, entry_id)
    if not entry:
        raise NotFoundError(message="Vitals entry not found")
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy or entry.pregnancy_id != pregnancy.id:
        raise NotFoundError(message="Vitals entry not found")
    return entry


async def update_vitals(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID, data) -> PregnancyVitalsEntry:
    entry = await get_vitals_entry(db, entry_id, user_id)
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)

    new_answers = {**entry.submission.answers, **data.answers}
    await cycle_repository.update_submission(db, entry.submission, {"answers": new_answers})

    template_fields = entry.submission.template.fields.get("fields", []) if entry.submission.template else []
    is_flagged, flagged_reasons = _determine_flagging(new_answers, template_fields)

    updated_entry = await pregnancy_repository.update_vitals_entry(db, entry, {
        "is_flagged": is_flagged,
        "flagged_reasons": flagged_reasons,
    })
    await _recalculate_risk_score(db, user_id, pregnancy.id)
    await db.commit()
    return updated_entry


async def get_patient_vitals(
    db: AsyncSession, patient_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[PregnancyVitalsEntry], int]:
    patient_pregnancy = await pregnancy_repository.get_active_pregnancy(db, patient_id)
    if not patient_pregnancy:
        raise NotFoundError(message="No active pregnancy found for this patient")
    return await pregnancy_repository.list_vitals_entries(db, patient_pregnancy.id, False, page, page_size)


async def create_vitals_feedback(
    db: AsyncSession, entry_id: uuid.UUID, clinician_id: uuid.UUID, data
) -> VitalsFeedback:
    entry = await pregnancy_repository.get_vitals_entry_by_id(db, entry_id)
    if not entry:
        raise NotFoundError(message="Vitals entry not found")
    feedback = await pregnancy_repository.create_vitals_feedback(db, {
        "vitals_entry_id": entry_id,
        "clinician_id": clinician_id,
        "message": data.message,
    })
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def list_vitals_feedback(db: AsyncSession, entry_id: uuid.UUID) -> list[VitalsFeedback]:
    entry = await pregnancy_repository.get_vitals_entry_by_id(db, entry_id)
    if not entry:
        raise NotFoundError(message="Vitals entry not found")
    return await pregnancy_repository.list_vitals_feedback(db, entry_id)


async def list_anc_visits(db: AsyncSession, user_id: uuid.UUID) -> list[ScheduledVisit]:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")
    return await pregnancy_repository.list_scheduled_visits(db, pregnancy.id)


async def create_manual_anc_visit(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: ManualVisitCreateRequest,
    facility_id: Optional[uuid.UUID] = None,
) -> ScheduledVisit:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")

    # Header/context facility takes priority; fall back to the body value if not present
    resolved_facility_id = facility_id or data.facilityId

    visit = await pregnancy_repository.create_scheduled_visit(
        db,
        {
            "pregnancy_id": pregnancy.id,
            "pathway_template_id": None,
            "label": data.purpose[:120],
            "scheduled_at": data.scheduledAt,
            "status": VisitStatus.SCHEDULED,
            "facility_id": resolved_facility_id,
            "purpose": data.purpose,
        },
    )
    await db.commit()
    await db.refresh(visit)
    return visit


async def update_anc_visit(
    db: AsyncSession,
    visit_id: uuid.UUID,
    patient_id: uuid.UUID,
    data: VisitUpdateRequest,
) -> ScheduledVisit:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, patient_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")

    visit = await pregnancy_repository.get_scheduled_visit_by_id(db, visit_id, pregnancy.id)
    if not visit:
        raise NotFoundError(message="Scheduled visit not found")

    update_data = {}
    if data.status is not None:
        update_data["status"] = data.status
    if data.summary is not None:
        update_data["summary"] = data.summary
    if data.scheduledAt is not None:
        update_data["scheduled_at"] = data.scheduledAt
        update_data["status"] = VisitStatus.RESCHEDULED

    updated = await pregnancy_repository.update_scheduled_visit(db, visit, update_data)
    await db.commit()
    await db.refresh(updated)
    return updated


async def list_nutrition_guidance(
    db: AsyncSession, category: Optional[NutritionCategory]
) -> list[NutritionGuidance]:
    return await pregnancy_repository.list_nutrition_guidance(db, category)


async def get_risk_score(db: AsyncSession, user_id: uuid.UUID) -> PregnancyRiskScore:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")
    score = await pregnancy_repository.get_latest_risk_score(db, pregnancy.id)
    if not score:
        score = await _recalculate_risk_score(db, user_id, pregnancy.id)
        await db.commit()
    return score


async def get_risk_score_history(db: AsyncSession, user_id: uuid.UUID) -> list[PregnancyRiskScore]:
    pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if not pregnancy:
        raise NoActivePregnancyError(message="No active pregnancy found")
    return await pregnancy_repository.list_risk_score_history(db, pregnancy.id)
