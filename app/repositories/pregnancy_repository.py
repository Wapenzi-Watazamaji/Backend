import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.pregnancy import (
    PregnancyRecord, PregnancyStatus, CarePathwayTemplate, PregnancyVitalsEntry,
    VitalsFeedback, ScheduledVisit, PregnancyRiskScore, WeekInfo, NutritionGuidance,
    NutritionCategory,
)
from app.models.cycle import FormSubmission


async def get_active_pregnancy(db: AsyncSession, user_id: uuid.UUID) -> PregnancyRecord | None:
    stmt = select(PregnancyRecord).where(
        and_(PregnancyRecord.user_id == user_id, PregnancyRecord.status == PregnancyStatus.ACTIVE)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_pregnancy_by_id(db: AsyncSession, pregnancy_id: uuid.UUID) -> PregnancyRecord | None:
    stmt = select(PregnancyRecord).where(PregnancyRecord.id == pregnancy_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_pregnancy(db: AsyncSession, data: dict) -> PregnancyRecord:
    obj = PregnancyRecord(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_pregnancy(db: AsyncSession, record: PregnancyRecord, data: dict) -> PregnancyRecord:
    for key, value in data.items():
        setattr(record, key, value)
    await db.flush()
    await db.refresh(record)
    return record


async def get_care_pathway_template(db: AsyncSession, template_id: str) -> CarePathwayTemplate | None:
    stmt = select(CarePathwayTemplate).where(CarePathwayTemplate.id == template_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_scheduled_visit(db: AsyncSession, data: dict) -> ScheduledVisit:
    obj = ScheduledVisit(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_scheduled_visits(db: AsyncSession, pregnancy_id: uuid.UUID) -> list[ScheduledVisit]:
    stmt = (
        select(ScheduledVisit)
        .where(ScheduledVisit.pregnancy_id == pregnancy_id)
        .order_by(ScheduledVisit.scheduled_at)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_scheduled_visit_by_id(db: AsyncSession, visit_id: uuid.UUID, pregnancy_id: uuid.UUID) -> ScheduledVisit | None:
    stmt = select(ScheduledVisit).where(
        and_(ScheduledVisit.id == visit_id, ScheduledVisit.pregnancy_id == pregnancy_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_scheduled_visit(db: AsyncSession, visit: ScheduledVisit, data: dict) -> ScheduledVisit:
    for key, value in data.items():
        setattr(visit, key, value)
    await db.flush()
    await db.refresh(visit)
    return visit


async def create_vitals_entry(db: AsyncSession, data: dict) -> PregnancyVitalsEntry:
    obj = PregnancyVitalsEntry(**data)
    db.add(obj)
    await db.flush()
    stmt = (
        select(PregnancyVitalsEntry)
        .where(PregnancyVitalsEntry.id == obj.id)
        .options(selectinload(PregnancyVitalsEntry.submission))
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_vitals_entry_by_id(db: AsyncSession, entry_id: uuid.UUID) -> PregnancyVitalsEntry | None:
    stmt = (
        select(PregnancyVitalsEntry)
        .where(PregnancyVitalsEntry.id == entry_id)
        .options(
            selectinload(PregnancyVitalsEntry.submission).selectinload(FormSubmission.template),
            selectinload(PregnancyVitalsEntry.feedback),
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_vitals_entries(
    db: AsyncSession,
    pregnancy_id: uuid.UUID,
    flagged_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[PregnancyVitalsEntry], int]:
    filters = [PregnancyVitalsEntry.pregnancy_id == pregnancy_id]
    if flagged_only:
        filters.append(PregnancyVitalsEntry.is_flagged == True)

    count_stmt = select(PregnancyVitalsEntry).where(and_(*filters))
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    stmt = (
        select(PregnancyVitalsEntry)
        .where(and_(*filters))
        .options(selectinload(PregnancyVitalsEntry.submission))
        .order_by(PregnancyVitalsEntry.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def update_vitals_entry(db: AsyncSession, entry: PregnancyVitalsEntry, data: dict) -> PregnancyVitalsEntry:
    for key, value in data.items():
        setattr(entry, key, value)
    await db.flush()
    stmt = (
        select(PregnancyVitalsEntry)
        .where(PregnancyVitalsEntry.id == entry.id)
        .options(selectinload(PregnancyVitalsEntry.submission))
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_vitals_feedback(db: AsyncSession, data: dict) -> VitalsFeedback:
    obj = VitalsFeedback(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_vitals_feedback(db: AsyncSession, vitals_entry_id: uuid.UUID) -> list[VitalsFeedback]:
    stmt = (
        select(VitalsFeedback)
        .where(VitalsFeedback.vitals_entry_id == vitals_entry_id)
        .order_by(VitalsFeedback.created_at)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def save_risk_score(db: AsyncSession, data: dict) -> PregnancyRiskScore:
    obj = PregnancyRiskScore(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_latest_risk_score(db: AsyncSession, pregnancy_id: uuid.UUID) -> PregnancyRiskScore | None:
    stmt = (
        select(PregnancyRiskScore)
        .where(PregnancyRiskScore.pregnancy_id == pregnancy_id)
        .order_by(PregnancyRiskScore.calculated_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_risk_score_history(db: AsyncSession, pregnancy_id: uuid.UUID) -> list[PregnancyRiskScore]:
    stmt = (
        select(PregnancyRiskScore)
        .where(PregnancyRiskScore.pregnancy_id == pregnancy_id)
        .order_by(PregnancyRiskScore.calculated_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_week_info(db: AsyncSession, week_number: int) -> WeekInfo | None:
    stmt = select(WeekInfo).where(WeekInfo.week_number == week_number)
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_nutrition_guidance(
    db: AsyncSession, category: Optional[NutritionCategory] = None
) -> list[NutritionGuidance]:
    stmt = select(NutritionGuidance)
    if category:
        stmt = stmt.where(NutritionGuidance.category == category)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_all_flagged_vitals(db: AsyncSession, pregnancy_id: uuid.UUID) -> list[PregnancyVitalsEntry]:
    stmt = select(PregnancyVitalsEntry).where(
        and_(PregnancyVitalsEntry.pregnancy_id == pregnancy_id, PregnancyVitalsEntry.is_flagged == True)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_risk_score_override(
    db: AsyncSession, score: PregnancyRiskScore, override_data: dict
) -> PregnancyRiskScore:
    """Write a clinician_override payload to the latest risk score."""
    score.clinician_override = override_data
    await db.flush()
    await db.refresh(score)
    return score
