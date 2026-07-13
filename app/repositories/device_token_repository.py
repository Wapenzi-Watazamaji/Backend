import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.device_token import DeviceToken

async def get_by_id(db: AsyncSession, token_id: uuid.UUID) -> Optional[DeviceToken]:
    stmt = select(DeviceToken).where(DeviceToken.id == token_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_by_token(db: AsyncSession, device_token: str) -> Optional[DeviceToken]:
    stmt = select(DeviceToken).where(DeviceToken.device_token == device_token)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> List[DeviceToken]:
    stmt = select(DeviceToken).where(DeviceToken.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def create(db: AsyncSession, token_data: dict) -> DeviceToken:
    db_token = DeviceToken(**token_data)
    db.add(db_token)
    await db.flush()
    await db.refresh(db_token)
    return db_token

async def delete(db: AsyncSession, db_token: DeviceToken) -> None:
    await db.delete(db_token)
    await db.flush()
