import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User

async def get_by_phone_number(db: AsyncSession, phone_number: str) -> User | None:
    stmt = select(User).where(User.phone_number == phone_number)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create(db: AsyncSession, user_data: dict) -> User:
    db_user = User(**user_data)
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user
