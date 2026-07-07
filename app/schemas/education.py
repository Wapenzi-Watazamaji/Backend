import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from app.models.education import ContentCategory
from app.models.profile import CurrentStage

class EducationContentBase(BaseModel):
    title: str
    category: ContentCategory
    body: str
    target_stages: List[CurrentStage]

class EducationContentCreate(EducationContentBase):
    pass

class EducationContentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[ContentCategory] = None
    body: Optional[str] = None
    target_stages: Optional[List[CurrentStage]] = None

class EducationContentRead(EducationContentBase):
    id: uuid.UUID
    facility_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EducationEventBase(BaseModel):
    title: str
    event_date: datetime
    description: str

class EducationEventCreate(EducationEventBase):
    pass

class EducationEventUpdate(BaseModel):
    title: Optional[str] = None
    event_date: Optional[datetime] = None
    description: Optional[str] = None

class EducationEventRead(EducationEventBase):
    id: uuid.UUID
    facility_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
