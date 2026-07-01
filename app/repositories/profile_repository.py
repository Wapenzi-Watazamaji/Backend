import uuid
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.profile import Profile


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalars().first()


async def get_by_qr_token(db: AsyncSession, qr_token: str) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.qr_passport_token == qr_token))
    return result.scalars().first()


async def create(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    profile = Profile(user_id=user_id, preferred_unit_ids=[])
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def update(db: AsyncSession, profile: Profile, data: dict) -> Profile:
    for key, value in data.items():
        setattr(profile, key, value)
    await db.flush()
    await db.refresh(profile)
    return profile


async def generate_qr_token(db: AsyncSession, profile: Profile) -> Profile:
    token = secrets.token_urlsafe(24)
    profile.qr_passport_token = token
    await db.flush()
    await db.refresh(profile)
    return profile
