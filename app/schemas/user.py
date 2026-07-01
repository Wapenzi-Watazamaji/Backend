from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional
from app.models.user import UserRole, Gender, AccountType
import uuid

class UserBase(BaseModel):
    phone_number: str
    role: UserRole
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    preferred_language: Optional[str] = "en"
    county: Optional[str] = None
    profile_photo_url: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserCreateSmsOnly(UserBase):
    pass

class UserLogin(BaseModel):
    phone_number: str
    password: str


class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
