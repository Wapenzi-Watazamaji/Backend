import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from app.models.reminder import ReminderType

class ReminderBase(BaseModel):
    title: str
    type: ReminderType

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class ReminderCreate(ReminderBase):
    due_at: datetime

class ReminderUpdate(BaseModel):
    due_at: Optional[datetime] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class ReminderRead(ReminderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    due_at: datetime
    is_done: bool
    created_at: datetime
    updated_at: datetime
