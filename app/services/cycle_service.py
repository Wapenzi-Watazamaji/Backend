import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Any, Optional
from collections import Counter, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle import FormTemplate, FormContext, HmbAcknowledgeAction
from app.repositories import cycle_repository, profile_repository, pregnancy_repository
from app.schemas.cycle import PredictionRead, TrendRead, CycleLengthMonth, TrendInsight, TopSymptom
from app.utils.exceptions import NotFoundError, TemplateValidationError


PBAC_FLOW_SCORES = {
    "LIGHT": 1,
    "MODERATE": 5,
    "HEAVY": 10,
    "VERY_HEAVY": 20,
}

PBAC_CLOT_SCORES = {
    "NONE": 0,
    "SMALL": 1,
    "LARGE": 5,
}

PBAC_FLAG_SCORES = {
    "LEAKED_THROUGH_CLOTHING": 5,
    "CHANGED_AT_NIGHT": 5,
    "SOAKED_WITHIN_2_HOURS": 10,
}

HMB_THRESHOLD = 100


def validate_answers_against_template(template: FormTemplate, answers: dict[str, Any]) -> None:
    fields: list[dict] = template.fields.get("fields", [])
    for field in fields:
        key = field["key"]
        required = field.get("required", False)
        field_type = field["type"]

        if required and key not in answers:
            raise TemplateValidationError(
                message=f"Missing required field: {key}",
                fields={key: "This field is required"}
            )

        if key not in answers:
            continue

        value = answers[key]
        allowed = field.get("options", [])

        if field_type == "SINGLE_SELECT":
            if allowed and value not in allowed:
                raise TemplateValidationError(
                    message=f"Invalid value for field '{key}'",
                    fields={key: f"Must be one of: {', '.join(allowed)}"}
                )

        elif field_type == "MULTI_SELECT":
            if not isinstance(value, list):
                raise TemplateValidationError(
                    message=f"Field '{key}' must be a list",
                    fields={key: "Expected a list of values"}
                )
            if allowed:
                invalid = [v for v in value if v not in allowed]
                if invalid:
                    raise TemplateValidationError(
                        message=f"Invalid values for field '{key}': {invalid}",
                        fields={key: f"Must be one of: {', '.join(allowed)}"}
                    )


def compute_pbac_score(answers: dict[str, Any]) -> int:
    score = 0

    flow = answers.get("flowLevel")
    if flow:
        score += PBAC_FLOW_SCORES.get(flow, 0)

    clot = answers.get("clotLevel")
    if clot:
        score += PBAC_CLOT_SCORES.get(clot, 0)

    flags = answers.get("flags", [])
    for flag in flags:
        score += PBAC_FLAG_SCORES.get(flag, 0)

    return score


async def create_cycle_entry(db: AsyncSession, user_id: uuid.UUID, data):
    template = await cycle_repository.get_form_template_by_slug(db, data.templateSlug)
    if not template or template.context != FormContext.CYCLE_ENTRY:
        raise NotFoundError(message=f"Form template '{data.templateSlug}' not found")

    validate_answers_against_template(template, data.answers)

    pbac_score = compute_pbac_score(data.answers)

    submission_data = {
        "template_id": template.id,
        "user_id": user_id,
        "context": FormContext.CYCLE_ENTRY,
        "answers": data.answers,
        "client_generated_id": data.clientGeneratedId,
        "client_created_at": data.clientCreatedAt,
    }
    submission = await cycle_repository.create_submission(db, submission_data)

    entry_data = {
        "user_id": user_id,
        "submission_id": submission.id,
        "start_date": data.startDate,
        "end_date": data.endDate,
        "pbac_score": pbac_score,
    }
    entry = await cycle_repository.create_cycle_entry(db, entry_data)

    if pbac_score >= HMB_THRESHOLD:
        await _trigger_hmb(db, user_id, ["PBAC score exceeded clinical threshold of 100"])

    return entry


async def list_cycle_entries(db: AsyncSession, user_id: uuid.UUID, from_date, to_date, page, page_size):
    return await cycle_repository.list_cycle_entries(db, user_id, from_date, to_date, page, page_size)


async def get_cycle_entry(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID):
    entry = await cycle_repository.get_cycle_entry_by_id(db, entry_id, user_id)
    if not entry:
        raise NotFoundError(message="Cycle entry not found")
    return entry


async def update_cycle_entry(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID, data):
    entry = await cycle_repository.get_cycle_entry_by_id(db, entry_id, user_id)
    if not entry:
        raise NotFoundError(message="Cycle entry not found")

    entry_updates = {}
    if data.startDate is not None:
        entry_updates["start_date"] = data.startDate
    if data.endDate is not None:
        entry_updates["end_date"] = data.endDate

    if data.answers is not None:
        new_answers = {**entry.submission.answers, **data.answers}
        await cycle_repository.update_submission(db, entry.submission, {"answers": new_answers})
        pbac_score = compute_pbac_score(new_answers)
        entry_updates["pbac_score"] = pbac_score

        if pbac_score >= HMB_THRESHOLD:
            await _trigger_hmb(db, user_id, ["PBAC score exceeded clinical threshold of 100"])

    if entry_updates:
        entry = await cycle_repository.update_cycle_entry(db, entry, entry_updates)

    return entry


async def delete_cycle_entry(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID):
    entry = await cycle_repository.get_cycle_entry_by_id(db, entry_id, user_id)
    if not entry:
        raise NotFoundError(message="Cycle entry not found")
    await cycle_repository.delete_cycle_entry(db, entry)


async def add_pbac_item(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID, data):
    entry = await cycle_repository.get_cycle_entry_by_id(db, entry_id, user_id)
    if not entry:
        raise NotFoundError(message="Cycle entry not found")

    item_data = {
        "cycle_entry_id": entry_id,
        "date": data.date,
        "item_type": data.itemType,
        "soak_level": data.soakLevel,
        "point_value": data.pointValue,
    }
    return await cycle_repository.create_pbac_item(db, item_data)


async def list_pbac_items(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID):
    entry = await cycle_repository.get_cycle_entry_by_id(db, entry_id, user_id)
    if not entry:
        raise NotFoundError(message="Cycle entry not found")
    return await cycle_repository.list_pbac_items(db, entry_id)


async def get_pbac_score(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID):
    entry = await cycle_repository.get_cycle_entry_by_id(db, entry_id, user_id)
    if not entry:
        raise NotFoundError(message="Cycle entry not found")

    items = await cycle_repository.list_pbac_items(db, entry_id)
    total = sum(item.point_value for item in items)
    if entry.pbac_score:
        total += entry.pbac_score

    is_hmb = total >= HMB_THRESHOLD
    return {"entryId": entry_id, "totalScore": total, "isHmbRisk": is_hmb}


async def create_symptom(db: AsyncSession, user_id: uuid.UUID, data):
    template = await cycle_repository.get_form_template_by_slug(db, data.templateSlug)
    if not template or template.context != FormContext.CYCLE_SYMPTOM:
        raise NotFoundError(message=f"Form template '{data.templateSlug}' not found")

    validate_answers_against_template(template, data.answers)

    # Convert the symptom date to a timezone-aware datetime for storage
    symptom_datetime = datetime(data.date.year, data.date.month, data.date.day, tzinfo=timezone.utc)

    submission_data = {
        "template_id": template.id,
        "user_id": user_id,
        "context": FormContext.CYCLE_SYMPTOM,
        "answers": data.answers,
        "client_generated_id": data.clientGeneratedId,
        "client_created_at": symptom_datetime,  # Persist the user-provided symptom date
    }
    return await cycle_repository.create_submission(db, submission_data)


async def list_symptoms(db: AsyncSession, user_id: uuid.UUID, from_date, to_date, page, page_size):
    return await cycle_repository.get_symptom_submissions(db, user_id, from_date, to_date, page, page_size)


async def get_predictions(db: AsyncSession, user_id: uuid.UUID) -> PredictionRead:
    # Periods stop during pregnancy, so "days since last logged period" and
    # "next period predicted date" are not meaningful while a pregnancy is
    # active — without this check they grow unbounded from the last entry
    # logged before conception (e.g. 200+ days into a pregnancy).
    active_pregnancy = await pregnancy_repository.get_active_pregnancy(db, user_id)
    if active_pregnancy:
        return PredictionRead(
            nextPeriodPredictedDate=None,
            ovulationWindowStart=None,
            ovulationWindowEnd=None,
            averageCycleLengthDays=None,
            currentCycleDay=None,
        )

    entries = await cycle_repository.get_cycle_entries_for_predictions(db, user_id, limit=12)

    if len(entries) == 0:
        return PredictionRead(
            nextPeriodPredictedDate=None,
            ovulationWindowStart=None,
            ovulationWindowEnd=None,
            averageCycleLengthDays=None,
            currentCycleDay=None,
        )

    sorted_entries = sorted(entries, key=lambda e: e.start_date)
    cycle_lengths = []
    for i in range(1, len(sorted_entries)):
        delta = (sorted_entries[i].start_date - sorted_entries[i - 1].start_date).days
        if 15 <= delta <= 60:
            cycle_lengths.append(delta)

    if not cycle_lengths:
        # Fallback for 1 entry or no valid lengths
        profile = await profile_repository.get_by_user_id(db, user_id)
        avg_cycle = profile.typical_cycle_length_days if profile and profile.typical_cycle_length_days else 28
    else:
        avg_cycle = round(sum(cycle_lengths) / len(cycle_lengths))

    last_start = sorted_entries[-1].start_date
    next_period = last_start + timedelta(days=avg_cycle)
    ovulation_end = next_period - timedelta(days=14)
    ovulation_start = ovulation_end - timedelta(days=4)
    today = date.today()
    current_day = (today - last_start).days + 1

    return PredictionRead(
        nextPeriodPredictedDate=next_period,
        ovulationWindowStart=ovulation_start,
        ovulationWindowEnd=ovulation_end,
        averageCycleLengthDays=avg_cycle,
        currentCycleDay=max(current_day, 1),
    )


async def get_trends(db: AsyncSession, user_id: uuid.UUID, months: int = 6) -> TrendRead:
    entries = await cycle_repository.get_cycle_entries_for_predictions(db, user_id, limit=months * 2)
    symptom_subs = await cycle_repository.get_all_symptom_submissions(db, user_id)

    sorted_entries = sorted(entries, key=lambda e: e.start_date)

    monthly_lengths: dict[str, list[int]] = defaultdict(list)
    for i in range(1, len(sorted_entries)):
        delta = (sorted_entries[i].start_date - sorted_entries[i - 1].start_date).days
        if 15 <= delta <= 60:
            month_key = sorted_entries[i - 1].start_date.strftime("%Y-%m")
            monthly_lengths[month_key].append(delta)

    history = [
        CycleLengthMonth(month=month, averageLengthDays=round(sum(lengths) / len(lengths)))
        for month, lengths in sorted(monthly_lengths.items())
    ]

    all_symptoms = []
    for sub in symptom_subs:
        symptoms = sub.answers.get("symptoms", [])
        all_symptoms.extend(symptoms)

    top_counter = Counter(all_symptoms).most_common(5)
    top_symptoms = [TopSymptom(symptom=s, count=c) for s, c in top_counter]

    insights = []
    if len(history) >= 2:
        lengths_only = [h.averageLengthDays for h in history]
        spread = max(lengths_only) - min(lengths_only)
        if spread <= 3:
            insights.append(TrendInsight(type="REGULARITY", message="Your cycles have been fairly regular over the last 6 months"))
        else:
            insights.append(TrendInsight(type="IRREGULARITY", message="Your cycle lengths have varied more than usual recently"))

    long_periods = [e for e in sorted_entries if e.end_date and (e.end_date - e.start_date).days > 7]
    if len(long_periods) >= 2:
        insights.append(TrendInsight(type="DURATION_INCREASE", message="Your periods have lasted longer than usual twice this year"))

    return TrendRead(cycleLengthHistory=history, insights=insights, topSymptoms=top_symptoms)


async def get_hmb_status(db: AsyncSession, user_id: uuid.UUID):
    status = await cycle_repository.get_hmb_status(db, user_id)
    if not status:
        return {"isActive": False, "triggeredAt": None, "reasons": []}
    return {"isActive": status.is_active, "triggeredAt": status.triggered_at, "reasons": status.reasons}


async def acknowledge_hmb(db: AsyncSession, user_id: uuid.UUID, action: HmbAcknowledgeAction):
    status = await cycle_repository.get_hmb_status(db, user_id)
    if not status:
        raise NotFoundError(message="No active HMB status found")

    data = {
        "is_active": False,
        "acknowledged_at": datetime.now(timezone.utc),
        "acknowledged_action": action,
    }
    await cycle_repository.upsert_hmb_status(db, user_id, data)
    return {"isActive": False}


async def _trigger_hmb(db: AsyncSession, user_id: uuid.UUID, reasons: list[str]):
    data = {
        "is_active": True,
        "triggered_at": datetime.now(timezone.utc),
        "reasons": reasons,
    }
    await cycle_repository.upsert_hmb_status(db, user_id, data)
