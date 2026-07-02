import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.staff import StaffMember, StaffStatus


async def is_active_staff_at_facility(
    db: AsyncSession,
    user_id: uuid.UUID,
    facility_id: uuid.UUID,
) -> bool:
    """Return True if the given user is an ACTIVE staff member at the given facility."""
    stmt = select(StaffMember).where(
        StaffMember.user_id == user_id,
        StaffMember.facility_id == facility_id,
        StaffMember.status == StaffStatus.ACTIVE,
    )
    result = await db.execute(stmt)
    return result.scalars().first() is not None


async def get_by_user_and_facility(
    db: AsyncSession,
    user_id: uuid.UUID,
    facility_id: uuid.UUID,
) -> StaffMember | None:
    """Return the StaffMember record for a user at a given facility, regardless of status."""
    stmt = select(StaffMember).where(
        StaffMember.user_id == user_id,
        StaffMember.facility_id == facility_id,
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_by_facility(
    db: AsyncSession,
    facility_id: uuid.UUID,
) -> list[StaffMember]:
    """Return all staff members at a given facility."""
    stmt = select(StaffMember).where(StaffMember.facility_id == facility_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, data: dict) -> StaffMember:
    staff = StaffMember(**data)
    db.add(staff)
    await db.flush()
    await db.refresh(staff)
    return staff


async def get_by_id(db: AsyncSession, staff_id: uuid.UUID) -> StaffMember | None:
    stmt = select(StaffMember).where(StaffMember.id == staff_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def update(db: AsyncSession, staff: StaffMember, update_data: dict) -> StaffMember:
    for field, value in update_data.items():
        setattr(staff, field, value)
    db.add(staff)
    await db.flush()
    await db.refresh(staff)
    return staff
