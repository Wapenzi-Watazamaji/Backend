"""
Postpartum Service — business logic for:
  - Baby Profile (create / get / update)
  - Baby Milestones
  - Baby Vaccinations + schedule
  - Baby Vitals (via FormSubmission)
  - Maternal Check-ins (via FormSubmission)
  - EPDS Depression Screening with Q10 override
  - Postnatal Clinic-visit schedule
"""
import uuid
from datetime import datetime, timezone, timedelta, date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.postpartum import (
    BabyProfile, BabyMilestone, BabyVaccinationRecord,
    EpdsScreening, EpdsRiskLevel, MilestoneCategory,
    DeliveryType,
)
from app.models.cycle import FormContext, FormSubmission
from app.models.pregnancy import ScheduledVisit, VisitStatus, CarePathwayTemplate
from app.repositories import postpartum_repository, cycle_repository
from app.repositories import pregnancy_repository
from app.utils.exceptions import NotFoundError

MOH_VACCINATION_PATHWAY_ID = "path_vaccination_moh_v1"
MOH_POSTNATAL_PATHWAY_ID = "path_postnatal_moh_v1"

# Status map for vaccination schedule display
_VISIT_STATUS_MAP = {
    VisitStatus.COMPLETED: "GIVEN",
    VisitStatus.SCHEDULED: "UPCOMING",
    VisitStatus.MISSED: "OVERDUE",
    VisitStatus.RESCHEDULED: "UPCOMING",
}


# ------------------------------------------------------------------ #
# Internal helpers                                                    #
# ------------------------------------------------------------------ #

def _score_epds(responses: list) -> tuple[int, int, bool, EpdsRiskLevel]:
    """
    responses: list of {questionId: "q1"…"q10", answerValue: 0-3}
    Returns: (total_score, q10_score, is_self_harm, risk_level)
    """
    answer_map = {item.questionId: item.answerValue for item in responses}
    total = sum(answer_map.get(f"q{i}", 0) for i in range(1, 11))
    q10 = answer_map.get("q10", 0)
    is_self_harm = q10 > 0

    if is_self_harm:
        level = EpdsRiskLevel.SELF_HARM_RISK
    elif total >= 12:
        level = EpdsRiskLevel.HIGH
    elif total >= 9:
        level = EpdsRiskLevel.MEDIUM
    else:
        level = EpdsRiskLevel.LOW

    return total, q10, is_self_harm, level


async def _generate_vaccination_schedule(
    db: AsyncSession,
    baby_id: uuid.UUID,
    date_of_birth: date,
) -> None:
    """
    Instantiate ScheduledVisit rows from path_vaccination_moh_v1
    using the baby's DOB as the time base.
    We repurpose 'pregnancy_id' on ScheduledVisit to store baby_id so
    we can query them without a schema change. A dedicated column can
    be added in a future migration if needed.
    """
    stmt = select(CarePathwayTemplate).where(
        CarePathwayTemplate.id == MOH_VACCINATION_PATHWAY_ID
    )
    result = await db.execute(stmt)
    pathway = result.scalars().first()
    if not pathway:
        return  # Seed data not present — skip silently

    for milestone in pathway.milestones:
        trigger_weeks = milestone.get("triggerWeek", 0)
        scheduled_date = date_of_birth + timedelta(weeks=trigger_weeks)
        scheduled_at = datetime.combine(scheduled_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        visit = ScheduledVisit(
            baby_id=baby_id,
            pathway_template_id=MOH_VACCINATION_PATHWAY_ID,
            milestone_order=milestone.get("order"),
            label=milestone.get("label", "Vaccination"),
            scheduled_at=scheduled_at,
            status=VisitStatus.SCHEDULED,
            purpose=milestone.get("vaccineId"),  # store vaccineId in purpose
        )
        db.add(visit)
    await db.flush()


async def _generate_postnatal_visits(
    db: AsyncSession,
    pregnancy_id: uuid.UUID,
    delivery_date: date,
) -> None:
    """
    Instantiate postnatal ScheduledVisit rows from path_postnatal_moh_v1.
    These track combined mother + baby clinic visits.
    """
    stmt = select(CarePathwayTemplate).where(
        CarePathwayTemplate.id == MOH_POSTNATAL_PATHWAY_ID
    )
    result = await db.execute(stmt)
    pathway = result.scalars().first()
    if not pathway:
        return  # Seed data not present — skip silently

    for milestone in pathway.milestones:
        trigger_days = milestone.get("triggerDays", 0)
        scheduled_date = delivery_date + timedelta(days=trigger_days)
        scheduled_at = datetime.combine(scheduled_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        visit = ScheduledVisit(
            pregnancy_id=pregnancy_id,
            pathway_template_id=MOH_POSTNATAL_PATHWAY_ID,
            milestone_order=milestone.get("order"),
            label=milestone.get("label", "Postnatal visit"),
            scheduled_at=scheduled_at,
            status=VisitStatus.SCHEDULED,
            purpose=",".join(milestone.get("covers", ["MOTHER", "BABY"])),
        )
        db.add(visit)
    await db.flush()


# ------------------------------------------------------------------ #
# Baby Profile                                                        #
# ------------------------------------------------------------------ #

async def create_baby_profile(db: AsyncSession, user_id: uuid.UUID, data) -> BabyProfile:
    # Parse optional time_of_birth string "HH:MM"
    time_of_birth = None
    if data.timeOfBirth:
        from datetime import time as dt_time
        parts = data.timeOfBirth.split(":")
        time_of_birth = dt_time(int(parts[0]), int(parts[1]))

    # Validate pregnancy ownership if pregnancyId is provided
    if data.pregnancyId:
        pregnancy = await pregnancy_repository.get_pregnancy_by_id(db, data.pregnancyId)
        if not pregnancy or pregnancy.user_id != user_id:
            raise NotFoundError(message="Pregnancy record not found or does not belong to this user")

    profile = await postpartum_repository.create_baby_profile(db, {
        "user_id": user_id,
        "name": data.name,
        "date_of_birth": data.dateOfBirth,
        "time_of_birth": time_of_birth,
        "gender": data.sex,
        "delivery_type": data.deliveryType,
        "birth_weight_kg": data.birthWeightKg,
        "birth_length_cm": data.birthLengthCm,
        "place_of_birth": data.placeOfBirth,
        "notes": data.notes,
        "pregnancy_id": data.pregnancyId,
    })

    # Auto-generate vaccination schedule
    await _generate_vaccination_schedule(db, profile.id, data.dateOfBirth)
    
    # Auto-generate PNC visits if linked to a pregnancy
    if data.pregnancyId:
        await _generate_postnatal_visits(db, data.pregnancyId, data.dateOfBirth)

    await db.commit()
    await db.refresh(profile)
    return profile



async def list_baby_profiles(db: AsyncSession, user_id: uuid.UUID) -> list[BabyProfile]:
    return await postpartum_repository.list_baby_profiles(db, user_id)


async def get_baby_profile(db: AsyncSession, baby_id: uuid.UUID, user_id: uuid.UUID) -> BabyProfile:
    profile = await postpartum_repository.get_baby_profile_by_id(db, baby_id, user_id)
    if not profile:
        raise NotFoundError(message="No baby profile found")
    return profile


async def update_baby_profile(db: AsyncSession, baby_id: uuid.UUID, user_id: uuid.UUID, data) -> BabyProfile:
    profile = await get_baby_profile(db, baby_id, user_id)
    if not profile:
        raise NotFoundError(message="No baby profile found")

    update_data: dict = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.sex is not None:
        update_data["gender"] = data.sex
    if data.birthWeightKg is not None:
        update_data["birth_weight_kg"] = data.birthWeightKg
    if data.birthLengthCm is not None:
        update_data["birth_length_cm"] = data.birthLengthCm
    if data.deliveryType is not None:
        update_data["delivery_type"] = data.deliveryType
    if data.placeOfBirth is not None:
        update_data["place_of_birth"] = data.placeOfBirth
    if data.notes is not None:
        update_data["notes"] = data.notes

    updated = await postpartum_repository.update_baby_profile(db, profile, update_data)
    await db.commit()
    await db.refresh(updated)
    return updated


# ------------------------------------------------------------------ #
# Baby Milestones                                                     #
# ------------------------------------------------------------------ #

async def create_milestone(db: AsyncSession, baby_id: uuid.UUID, user_id: uuid.UUID, data) -> BabyMilestone:
    profile = await get_baby_profile(db, baby_id, user_id)
    if not profile:
        raise NotFoundError(message="No baby profile found. Create a baby profile first.")

    milestone = await postpartum_repository.create_milestone(db, {
        "baby_id": profile.id,
        "user_id": user_id,
        "category": data.category,
        "title": data.title,
        "achieved_at": data.achievedAt,
        "note": data.note,
        "photo_url": data.photoUrl,
    })
    await db.commit()
    await db.refresh(milestone)
    return milestone


async def list_milestones(
    db: AsyncSession,
    baby_id: uuid.UUID,
    user_id: uuid.UUID,
    category: Optional[MilestoneCategory] = None,
) -> list[BabyMilestone]:
    profile = await get_baby_profile(db, baby_id, user_id)
    if not profile:
        raise NotFoundError(message="No baby profile found")
    return await postpartum_repository.list_milestones(db, profile.id, category)


# ------------------------------------------------------------------ #
# Baby Vaccinations                                                   #
# ------------------------------------------------------------------ #

async def record_vaccination(
    db: AsyncSession, baby_id: uuid.UUID, user_id: uuid.UUID, data
) -> BabyVaccinationRecord:
    profile = await get_baby_profile(db, baby_id, user_id)
    if not profile:
        raise NotFoundError(message="No baby profile found")

    # Try to match to a ScheduledVisit row for this vaccine
    visits = await postpartum_repository.get_vaccination_scheduled_visits(db, profile.id)
    matched_visit = next(
        (v for v in visits if v.purpose == data.vaccineId), None
    )

    record = await postpartum_repository.create_vaccination_record(db, {
        "baby_id": profile.id,
        "scheduled_visit_id": matched_visit.id if matched_visit else None,
        "vaccine_id": data.vaccineId,
        "given_at": data.givenAt,
        "facility_id": data.facilityId,
        "batch_number": data.batchNumber,
    })

    # Mark the scheduled visit as COMPLETED
    if matched_visit:
        await postpartum_repository.update_scheduled_visit(db, matched_visit, {
            "status": VisitStatus.COMPLETED,
        })

    await db.commit()
    await db.refresh(record)
    return record


async def get_vaccination_schedule(
    db: AsyncSession, baby_id: uuid.UUID, user_id: uuid.UUID
) -> list[dict]:
    profile = await get_baby_profile(db, baby_id, user_id)
    if not profile:
        raise NotFoundError(message="No baby profile found")

    visits = await postpartum_repository.get_vaccination_scheduled_visits(db, profile.id)
    today = datetime.now(timezone.utc)
    schedule = []
    for visit in visits:
        # Determine status: overdue if SCHEDULED and past scheduled date
        status = _VISIT_STATUS_MAP.get(visit.status, "UPCOMING")
        if visit.status == VisitStatus.SCHEDULED and visit.scheduled_at < today:
            status = "OVERDUE"

        # Fetch administered record if GIVEN
        given_at = None
        if visit.status == VisitStatus.COMPLETED:
            rec = await postpartum_repository.get_vaccination_record_by_visit(db, visit.id)
            given_at = rec.given_at if rec else None

        schedule.append({
            "id": visit.id,
            "vaccineId": visit.purpose,  # stored in purpose field
            "name": visit.label,
            "ageMilestone": visit.summary or "",
            "status": status,
            "scheduledAt": visit.scheduled_at,
            "givenAt": given_at,
        })
    return schedule


async def mark_vaccination_given(
    db: AsyncSession,
    baby_id: uuid.UUID,
    user_id: uuid.UUID,
    visit_id: uuid.UUID,
    data,
) -> ScheduledVisit:
    profile = await get_baby_profile(db, baby_id, user_id)
    if not profile:
        raise NotFoundError(message="No baby profile found")

    visit = await postpartum_repository.get_scheduled_visit_by_id(db, visit_id)
    if not visit or visit.baby_id != profile.id:
        raise NotFoundError(message="Vaccination visit not found")

    # Create vaccination record
    await postpartum_repository.create_vaccination_record(db, {
        "baby_id": profile.id,
        "scheduled_visit_id": visit.id,
        "vaccine_id": visit.purpose or "",
        "given_at": data.givenAt,
        "facility_id": data.facilityId,
        "batch_number": data.batchNumber,
    })

    updated = await postpartum_repository.update_scheduled_visit(db, visit, {
        "status": VisitStatus.COMPLETED,
    })
    await db.commit()
    await db.refresh(updated)
    return updated


# ------------------------------------------------------------------ #
# Baby Vitals (via FormSubmission)                                    #
# ------------------------------------------------------------------ #

async def get_baby_vitals_template(db: AsyncSession) -> object:
    template = await cycle_repository.get_active_form_template(db, FormContext.BABY_VITALS)
    if not template:
        raise NotFoundError(message="No active baby vitals template found")
    return template


async def create_baby_vitals(
    db: AsyncSession, baby_id: uuid.UUID, user_id: uuid.UUID, data
) -> FormSubmission:
    profile = await get_baby_profile(db, baby_id, user_id)
    if not profile:
        raise NotFoundError(message="No baby profile found")

    template = await cycle_repository.get_form_template_by_slug(db, data.templateId)
    if not template or template.context != FormContext.BABY_VITALS:
        raise NotFoundError(message=f"Baby vitals template '{data.templateId}' not found")

    answers = dict(data.answers)
    answers["baby_id"] = str(profile.id)

    submission = await cycle_repository.create_submission(db, {
        "template_id": template.id,
        "user_id": user_id,
        "context": FormContext.BABY_VITALS,
        "answers": answers,
        "client_generated_id": data.clientGeneratedId,
        "client_created_at": data.clientCreatedAt,
    })
    await db.commit()
    await db.refresh(submission)
    return submission


async def list_baby_vitals(
    db: AsyncSession, baby_id: uuid.UUID, user_id: uuid.UUID
) -> list[FormSubmission]:
    from sqlalchemy import select, and_, func
    stmt = (
        select(FormSubmission)
        .where(
            and_(
                FormSubmission.user_id == user_id,
                FormSubmission.context == FormContext.BABY_VITALS,
                FormSubmission.answers['baby_id'].as_string() == str(baby_id)
            )
        )
        .order_by(FormSubmission.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_baby_vitals_alerts(
    db: AsyncSession, baby_id: uuid.UUID, user_id: uuid.UUID
) -> list[dict]:
    """
    Scan recent baby vitals submissions for flagged symptoms and return alerts.
    This is a simple rule-based engine: any BABY_VITALS submission containing
    flagged symptoms generates an alert.
    """
    FLAGGED_SYMPTOMS = {
        "DIFFICULTY_BREATHING", "UNUSUALLY_SLEEPY", "POOR_FEEDING",
        "JAUNDICE", "FEVER", "COLD_TO_TOUCH",
    }
    submissions = await list_baby_vitals(db, baby_id, user_id)
    alerts = []
    for submission in submissions[:10]:  # scan last 10
        symptoms = submission.answers.get("symptoms", [])
        flagged = [s for s in symptoms if s in FLAGGED_SYMPTOMS]
        for symptom in flagged:
            alerts.append({
                "id": f"balrt_{submission.id}_{symptom}",
                "type": symptom,
                "message": f"Symptom '{symptom}' was reported for your baby",
                "createdAt": submission.created_at,
            })
    return alerts


# ------------------------------------------------------------------ #
# Maternal Check-ins                                                  #
# ------------------------------------------------------------------ #

async def get_maternal_checkin_template(db: AsyncSession) -> object:
    template = await cycle_repository.get_active_form_template(db, FormContext.MATERNAL_CHECKIN)
    if not template:
        raise NotFoundError(message="No active maternal check-in template found")
    return template


async def create_maternal_checkin(
    db: AsyncSession, user_id: uuid.UUID, data
) -> FormSubmission:
    template = await cycle_repository.get_form_template_by_slug(db, data.templateId)
    if not template or template.context != FormContext.MATERNAL_CHECKIN:
        raise NotFoundError(message=f"Maternal check-in template '{data.templateId}' not found")

    submission = await cycle_repository.create_submission(db, {
        "template_id": template.id,
        "user_id": user_id,
        "context": FormContext.MATERNAL_CHECKIN,
        "answers": data.answers,
        "client_generated_id": data.clientGeneratedId,
        "client_created_at": data.clientCreatedAt,
    })
    await db.commit()
    await db.refresh(submission)
    return submission


async def list_maternal_checkins(
    db: AsyncSession, user_id: uuid.UUID
) -> list[FormSubmission]:
    from sqlalchemy import select, and_
    stmt = (
        select(FormSubmission)
        .where(
            and_(
                FormSubmission.user_id == user_id,
                FormSubmission.context == FormContext.MATERNAL_CHECKIN,
            )
        )
        .order_by(FormSubmission.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_maternal_checkin(
    db: AsyncSession, submission_id: uuid.UUID, user_id: uuid.UUID
) -> FormSubmission:
    submission = await cycle_repository.get_submission_by_id(db, submission_id, user_id)
    if not submission or submission.context != FormContext.MATERNAL_CHECKIN:
        raise NotFoundError(message="Maternal check-in not found")
    return submission


# ------------------------------------------------------------------ #
# EPDS Screening                                                      #
# ------------------------------------------------------------------ #

async def submit_epds(db: AsyncSession, user_id: uuid.UUID, data) -> dict:
    total, q10_score, is_self_harm, level = _score_epds(data.responses)
    answers = {item.questionId: item.answerValue for item in data.responses}

    screening = await postpartum_repository.create_epds_screening(db, {
        "user_id": user_id,
        "answers": answers,
        "total_score": total,
        "q10_score": q10_score,
        "is_self_harm_flagged": is_self_harm,
        "risk_level": level,
    })
    await db.commit()
    await db.refresh(screening)

    return {
        "id": screening.id,
        "totalScore": screening.total_score,
        "suggestsSupportBeneficial": screening.total_score >= 13,
        "immediateConcernFlag": screening.is_self_harm_flagged,
        "completedAt": screening.created_at,
    }


async def list_epds_history(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    screenings = await postpartum_repository.list_epds_screenings(db, user_id)
    return [
        {
            "id": s.id,
            "totalScore": s.total_score,
            "immediateConcernFlag": s.is_self_harm_flagged,
            "completedAt": s.created_at,
        }
        for s in screenings
    ]


async def get_epds_flag(db: AsyncSession, user_id: uuid.UUID) -> dict:
    is_active = await postpartum_repository.has_active_self_harm_flag(db, user_id)
    return {"isActive": is_active}


# ------------------------------------------------------------------ #
# Postnatal Clinic-Visit Schedule                                     #
# ------------------------------------------------------------------ #

async def get_postnatal_clinic_schedule(
    db: AsyncSession, user_id: uuid.UUID
) -> list[dict]:
    """
    Returns combined mother+baby postnatal visit schedule.
    Visits are linked to the (now-ended) pregnancy record.
    """
    from sqlalchemy import select, and_
    from app.models.pregnancy import PregnancyRecord, PregnancyStatus

    # Get the most recently ended pregnancy for this user
    stmt = (
        select(PregnancyRecord)
        .where(
            and_(
                PregnancyRecord.user_id == user_id,
                PregnancyRecord.status == PregnancyStatus.ENDED,
            )
        )
        .order_by(PregnancyRecord.ended_at.desc())
    )
    result = await db.execute(stmt)
    pregnancy = result.scalars().first()

    if not pregnancy:
        raise NotFoundError(message="No ended pregnancy found — postnatal schedule not available")

    stmt = (
        select(ScheduledVisit)
        .where(
            and_(
                ScheduledVisit.pregnancy_id == pregnancy.id,
                ScheduledVisit.pathway_template_id == MOH_POSTNATAL_PATHWAY_ID,
            )
        )
        .order_by(ScheduledVisit.scheduled_at.asc())
    )
    result = await db.execute(stmt)
    visits = result.scalars().all()

    schedule = []
    for v in visits:
        covers = v.purpose.split(",") if v.purpose else ["MOTHER", "BABY"]
        schedule.append({
            "id": v.id,
            "label": v.label,
            "scheduledAt": v.scheduled_at,
            "covers": covers,
            "status": v.status.value,
        })
    return schedule
