import uuid
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class NotificationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    title: str
    body: str
    is_read: bool
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class DeviceRegisterRequest(BaseModel):
    device_token: str = Field(alias="deviceToken")
    platform: str

    model_config = ConfigDict(
        populate_by_name=True
    )

class DeviceRegisterResponse(BaseModel):
    token_id: uuid.UUID = Field(alias="tokenId")

    model_config = ConfigDict(
        populate_by_name=True
    )

class SmsSendRequest(BaseModel):
    to_phone_number: str = Field(alias="toPhoneNumber")
    template_id: str = Field(alias="templateId")
    variables: Dict[str, Any] = {}

    model_config = ConfigDict(
        populate_by_name=True
    )

class SmsSendResponse(BaseModel):
    sms_id: str = Field(alias="smsId")
    status: str

    model_config = ConfigDict(
        populate_by_name=True
    )

class SmsInboundWebhook(BaseModel):
    from_number: str = Field(alias="from")
    text: str
    linked_reminder_id: Optional[str] = Field(default=None, alias="linkedReminderId")

    model_config = ConfigDict(
        populate_by_name=True
    )

class SmsPreferenceResponse(BaseModel):
    contact_preference: str = Field(alias="contactPreference")

    model_config = ConfigDict(
        populate_by_name=True
    )

class SmsPreferenceUpdate(BaseModel):
    contact_preference: str = Field(alias="contactPreference")

    model_config = ConfigDict(
        populate_by_name=True
    )
