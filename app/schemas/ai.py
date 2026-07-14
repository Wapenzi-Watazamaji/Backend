from typing import List, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.ai_chat import ChatRole

class ContextSummaryResponse(BaseModel):
    summary: str

class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: ChatRole
    content: str
    tool_calls: Optional[List[dict]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    started_at: datetime
    last_message_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
