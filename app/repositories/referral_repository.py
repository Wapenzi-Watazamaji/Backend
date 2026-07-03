import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.referral import Referral, ReferralStatus, ReferralReason


async def create_referral(db: AsyncSession, data: dict) -> Referral:
    obj = Referral(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_referral_by_id(db: AsyncSession, referral_id: uuid.UUID) -> Referral | None:
    stmt = select(Referral).where(Referral.id == referral_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_referrals(
    db: AsyncSession,
    facility_id: Optional[uuid.UUID] = None,
    status: Optional[ReferralStatus] = None,
    direction: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> list[Referral]:
    stmt = select(Referral)

    conditions = []
    if status:
        conditions.append(Referral.status == status)
    if facility_id and direction == "INCOMING":
        conditions.append(Referral.to_facility_id == facility_id)
    elif facility_id and direction == "OUTGOING":
        conditions.append(Referral.from_facility_id == facility_id)
    elif facility_id:
        conditions.append(
            (Referral.to_facility_id == facility_id) | (Referral.from_facility_id == facility_id)
        )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Referral.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_referral(db: AsyncSession, referral: Referral, data: dict) -> Referral:
    for key, value in data.items():
        setattr(referral, key, value)
    await db.flush()
    await db.refresh(referral)
    return referral
