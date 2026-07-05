import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.postpartum import BabyProfile, BabyMilestone, BabyVaccinationRecord, EpdsScreening, MilestoneCategory
from app.models.pregnancy import ScheduledVisit



async def create_baby_profile(db: AsyncSession, data: dict) -> BabyProfile:
    obj = BabyProfile(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_latest_baby_profile(db: AsyncSession, user_id: uuid.UUID) -> BabyProfile | None:
    stmt = (
        select(BabyProfile)
        .where(BabyProfile.user_id == user_id)
        .order_by(BabyProfile.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_baby_profiles(db: AsyncSession, user_id: uuid.UUID) -> list[BabyProfile]:
    stmt = (
        select(BabyProfile)
        .where(BabyProfile.user_id == user_id)
        .order_by(BabyProfile.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_baby_profile_by_id(db: AsyncSession, profile_id: uuid.UUID, user_id: uuid.UUID) -> BabyProfile | None:
    stmt = select(BabyProfile).where(
        and_(BabyProfile.id == profile_id, BabyProfile.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_baby_profile(db: AsyncSession, profile: BabyProfile, data: dict) -> BabyProfile:
    for key, value in data.items():
        setattr(profile, key, value)
    await db.flush()
    await db.refresh(profile)
    return profile


async def create_milestone(db: AsyncSession, data: dict) -> BabyMilestone:
    obj = BabyMilestone(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_milestones(
    db: AsyncSession,
    baby_id: uuid.UUID,
    category: MilestoneCategory | None = None,
) -> list[BabyMilestone]:
    stmt = select(BabyMilestone).where(BabyMilestone.baby_id == baby_id)
    if category:
        stmt = stmt.where(BabyMilestone.category == category)
    stmt = stmt.order_by(BabyMilestone.achieved_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()



async def create_vaccination_record(db: AsyncSession, data: dict) -> BabyVaccinationRecord:
    obj = BabyVaccinationRecord(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_vaccination_scheduled_visits(
    db: AsyncSession,
    baby_id: uuid.UUID,
) -> list[ScheduledVisit]:
    stmt = (
        select(ScheduledVisit)
        .where(ScheduledVisit.baby_id == baby_id)
        .order_by(ScheduledVisit.scheduled_at.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_scheduled_visit_by_id(
    db: AsyncSession,
    visit_id: uuid.UUID,
) -> ScheduledVisit | None:
    stmt = select(ScheduledVisit).where(ScheduledVisit.id == visit_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_scheduled_visit(db: AsyncSession, visit: ScheduledVisit, data: dict) -> ScheduledVisit:
    for key, value in data.items():
        setattr(visit, key, value)
    await db.flush()
    await db.refresh(visit)
    return visit


async def get_vaccination_record_by_visit(
    db: AsyncSession, scheduled_visit_id: uuid.UUID
) -> BabyVaccinationRecord | None:
    stmt = select(BabyVaccinationRecord).where(
        BabyVaccinationRecord.scheduled_visit_id == scheduled_visit_id
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_epds_screening(db: AsyncSession, data: dict) -> EpdsScreening:
    obj = EpdsScreening(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_epds_screenings(db: AsyncSession, user_id: uuid.UUID) -> list[EpdsScreening]:
    stmt = (
        select(EpdsScreening)
        .where(EpdsScreening.user_id == user_id)
        .order_by(EpdsScreening.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_latest_epds_screening(db: AsyncSession, user_id: uuid.UUID) -> EpdsScreening | None:
    stmt = (
        select(EpdsScreening)
        .where(EpdsScreening.user_id == user_id)
        .order_by(EpdsScreening.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def has_active_self_harm_flag(db: AsyncSession, user_id: uuid.UUID) -> bool:
    latest = await get_latest_epds_screening(db, user_id)
    return bool(latest and latest.is_self_harm_flagged)
