import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.facility import Facility


async def get_by_id(db: AsyncSession, facility_id: uuid.UUID) -> Facility | None:
    result = await db.execute(select(Facility).where(Facility.id == facility_id))
    return result.scalars().first()


async def get_by_email(db: AsyncSession, email: str) -> Facility | None:
    result = await db.execute(select(Facility).where(Facility.email == email))
    return result.scalars().first()


async def create(db: AsyncSession, data: dict) -> Facility:
    facility = Facility(**data)
    db.add(facility)
    await db.flush()
    await db.refresh(facility)
    return facility


async def update(db: AsyncSession, facility: Facility, data: dict) -> Facility:
    for key, value in data.items():
        setattr(facility, key, value)
    await db.flush()
    await db.refresh(facility)
    return facility


async def get_facilities(db: AsyncSession, search: str | None = None) -> list[Facility]:
    stmt = select(Facility)
    if search:
        stmt = stmt.where(Facility.name.ilike(f"%{search}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())
