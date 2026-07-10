from typing import Optional
from pydantic import BaseModel

from app.schemas.user import UserRead
from app.schemas.profile import ProfileRead
from app.schemas.medical_history import MedicalHistoryRecordRead
from app.schemas.pregnancy import PregnancyRecordRead

class QRPublicProfileRead(BaseModel):
    user: UserRead
    profile: ProfileRead
    medical_history: Optional[MedicalHistoryRecordRead] = None
    active_pregnancy: Optional[PregnancyRecordRead] = None
