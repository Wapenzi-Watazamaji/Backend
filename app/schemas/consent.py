import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.consent import ConsentType

class ConsentRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    consent_type: ConsentType
    grantee_id: Optional[str] = None
    grantee_name: Optional[str] = None
    active: bool
    granted_at: datetime
    revoked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
