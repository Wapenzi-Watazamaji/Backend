from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

# Re-exporting FormTemplate schemas from their original location
from app.schemas.cycle import FormTemplateRead, FormTemplateCreate, FormTemplateUpdate

class CarePathwayTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    milestones: list[Any] = []
    is_active: bool = True

class CarePathwayTemplateCreate(CarePathwayTemplateBase):
    id: str

class CarePathwayTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    milestones: Optional[list[Any]] = None
    is_active: Optional[bool] = None

class CarePathwayTemplateRead(CarePathwayTemplateBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
