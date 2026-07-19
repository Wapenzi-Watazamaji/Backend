import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.cycle import (
    FormTemplate, FormSubmission, CycleEntry, PbacItem, HmbStatus, FormContext
)


async def get_active_form_template(db: AsyncSession, context: FormContext, slug: Optional[str] = None, facility_id: Optional[uuid.UUID] = None) -> FormTemplate | None:
    stmt = select(FormTemplate).where(
        and_(FormTemplate.context == context, FormTemplate.is_active == True)
    )
    if slug:
        stmt = stmt.where(FormTemplate.slug == slug)
        
    if facility_id:
        # Try to find a facility-specific template first
        facility_stmt = stmt.where(FormTemplate.facility_id == facility_id).order_by(FormTemplate.created_at.desc())
        result = await db.execute(facility_stmt)
        template = result.scalars().first()
        if template:
            return template
            
    # Fallback to global template (facility_id is NULL)
    stmt = stmt.where(FormTemplate.facility_id.is_(None)).order_by(FormTemplate.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_form_template_by_slug(db: AsyncSession, slug: str) -> FormTemplate | None:
    stmt = select(FormTemplate).where(FormTemplate.slug == slug)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_form_template_by_id(db: AsyncSession, template_id: uuid.UUID) -> FormTemplate | None:
    stmt = select(FormTemplate).where(FormTemplate.id == template_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_form_template(db: AsyncSession, data: dict) -> FormTemplate:
    obj = FormTemplate(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_form_template(db: AsyncSession, template: FormTemplate, data: dict) -> FormTemplate:
    for key, value in data.items():
        setattr(template, key, value)
    await db.flush()
    await db.refresh(template)
    return template


async def create_submission(db: AsyncSession, data: dict) -> FormSubmission:
    obj = FormSubmission(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_submission_by_id(db: AsyncSession, submission_id: uuid.UUID, user_id: uuid.UUID) -> FormSubmission | None:
    stmt = select(FormSubmission).where(
        and_(FormSubmission.id == submission_id, FormSubmission.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_cycle_entry(db: AsyncSession, data: dict) -> CycleEntry:
    obj = CycleEntry(**data)
    db.add(obj)
    await db.flush()
    stmt = select(CycleEntry).where(CycleEntry.id == obj.id).options(selectinload(CycleEntry.submission))
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_cycle_entry_by_id(db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID) -> CycleEntry | None:
    stmt = (
        select(CycleEntry)
        .where(and_(CycleEntry.id == entry_id, CycleEntry.user_id == user_id))
        .options(selectinload(CycleEntry.submission))
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_cycle_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CycleEntry], int]:
    filters = [CycleEntry.user_id == user_id]
    if from_date:
        filters.append(CycleEntry.start_date >= from_date)
    if to_date:
        filters.append(CycleEntry.start_date <= to_date)

    count_stmt = select(func.count()).select_from(CycleEntry).where(and_(*filters))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(CycleEntry)
        .where(and_(*filters))
        .options(selectinload(CycleEntry.submission))
        .order_by(CycleEntry.start_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def update_cycle_entry(db: AsyncSession, entry: CycleEntry, data: dict) -> CycleEntry:
    for key, value in data.items():
        setattr(entry, key, value)
    await db.flush()
    await db.refresh(entry)
    stmt = select(CycleEntry).where(CycleEntry.id == entry.id).options(selectinload(CycleEntry.submission))
    result = await db.execute(stmt)
    return result.scalars().first()


async def delete_cycle_entry(db: AsyncSession, entry: CycleEntry) -> None:
    await db.delete(entry)
    await db.flush()


async def update_submission(db: AsyncSession, submission: FormSubmission, data: dict) -> FormSubmission:
    for key, value in data.items():
        setattr(submission, key, value)
    await db.flush()
    await db.refresh(submission)
    return submission


async def create_pbac_item(db: AsyncSession, data: dict) -> PbacItem:
    obj = PbacItem(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def list_pbac_items(db: AsyncSession, cycle_entry_id: uuid.UUID) -> list[PbacItem]:
    stmt = select(PbacItem).where(PbacItem.cycle_entry_id == cycle_entry_id).order_by(PbacItem.date)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_cycle_entries_for_predictions(db: AsyncSession, user_id: uuid.UUID, limit: int = 12) -> list[CycleEntry]:
    stmt = (
        select(CycleEntry)
        .where(CycleEntry.user_id == user_id)
        .order_by(CycleEntry.start_date.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_hmb_status(db: AsyncSession, user_id: uuid.UUID) -> HmbStatus | None:
    stmt = select(HmbStatus).where(HmbStatus.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def upsert_hmb_status(db: AsyncSession, user_id: uuid.UUID, data: dict) -> HmbStatus:
    existing = await get_hmb_status(db, user_id)
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        await db.flush()
        await db.refresh(existing)
        return existing
    obj = HmbStatus(user_id=user_id, **data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_symptom_submissions(
    db: AsyncSession,
    user_id: uuid.UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[FormSubmission], int]:
    filters = [
        FormSubmission.user_id == user_id,
        FormSubmission.context == FormContext.CYCLE_SYMPTOM,
    ]

    # Apply date filters against client_created_at (the user's symptom date)
    if from_date:
        from_dt = datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc)
        filters.append(FormSubmission.client_created_at >= from_dt)
    if to_date:
        to_dt = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=timezone.utc)
        filters.append(FormSubmission.client_created_at <= to_dt)

    count_stmt = select(func.count()).select_from(FormSubmission).where(and_(*filters))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(FormSubmission)
        .where(and_(*filters))
        .order_by(FormSubmission.client_created_at.desc().nulls_last(), FormSubmission.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_all_symptom_submissions(db: AsyncSession, user_id: uuid.UUID) -> list[FormSubmission]:
    stmt = select(FormSubmission).where(
        and_(
            FormSubmission.user_id == user_id,
            FormSubmission.context == FormContext.CYCLE_SYMPTOM,
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()
