import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timezone
from app.models.reminder import Reminder, ReminderType

async def get_by_id(db: AsyncSession, reminder_id: uuid.UUID) -> Optional[Reminder]:
    stmt = select(Reminder).where(Reminder.id == reminder_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_by_user_id(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    upcoming_only: bool = False, 
    reminder_type: Optional[ReminderType] = None
) -> List[Reminder]:
    conditions = [Reminder.user_id == user_id]
    
    if upcoming_only:
        conditions.append(Reminder.due_at >= datetime.now(timezone.utc))
        
    if reminder_type:
        conditions.append(Reminder.type == reminder_type)
        
    stmt = select(Reminder).where(and_(*conditions)).order_by(Reminder.due_at.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def create(db: AsyncSession, reminder_data: dict) -> Reminder:
    db_reminder = Reminder(**reminder_data)
    db.add(db_reminder)
    await db.flush()
    await db.refresh(db_reminder)
    return db_reminder

async def update(db: AsyncSession, db_reminder: Reminder, reminder_data: dict) -> Reminder:
    for key, value in reminder_data.items():
        setattr(db_reminder, key, value)
    db.add(db_reminder)
    await db.flush()
    await db.refresh(db_reminder)
    return db_reminder

async def delete(db: AsyncSession, db_reminder: Reminder) -> None:
    await db.delete(db_reminder)
    await db.flush()
