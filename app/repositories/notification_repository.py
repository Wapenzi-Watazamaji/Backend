import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.notification import Notification

async def get_by_id(db: AsyncSession, notification_id: uuid.UUID) -> Optional[Notification]:
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_by_user_id(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    unread_only: bool = False, 
    limit: int = 20, 
    offset: int = 0
) -> Tuple[List[Notification], int]:
    conditions = [Notification.user_id == user_id]
    if unread_only:
        conditions.append(Notification.is_read == False)
        
    base_stmt = select(Notification).where(and_(*conditions))
    
    # Get total count
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    count_res = await db.execute(count_stmt)
    total_count = count_res.scalar() or 0
    
    # Get paginated data
    stmt = base_stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    
    return items, total_count

async def create(db: AsyncSession, notification_data: dict) -> Notification:
    db_notification = Notification(**notification_data)
    db.add(db_notification)
    await db.flush()
    await db.refresh(db_notification)
    
    try:
        from app.core.websocket import manager
        payload = {
            "id": str(db_notification.id),
            "userId": str(db_notification.user_id),
            "category": db_notification.category.value if hasattr(db_notification.category, "value") else str(db_notification.category),
            "title": db_notification.title,
            "body": db_notification.body,
            "isRead": db_notification.is_read,
            "relatedEntityType": db_notification.related_entity_type,
            "relatedEntityId": str(db_notification.related_entity_id) if db_notification.related_entity_id else None,
            "createdAt": db_notification.created_at.isoformat() if db_notification.created_at else None
        }
        # Run non-blocking push
        import asyncio
        asyncio.create_task(manager.send_personal_message(payload, str(db_notification.user_id)))
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to broadcast websocket notification: {e}")
        
    return db_notification

async def update(db: AsyncSession, db_notification: Notification, notification_data: dict) -> Notification:
    for key, value in notification_data.items():
        setattr(db_notification, key, value)
    db.add(db_notification)
    await db.flush()
    await db.refresh(db_notification)
    return db_notification
