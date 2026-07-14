import uuid
from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.deps import _extract_user_id, get_current_user
from app.repositories import user_repository, profile_repository
from app.utils.exceptions import UnauthorizedError, NotFoundError, create_success_response, APIResponse
from app.models.user import User, UserRole
from app.models.profile import CompanionPreference
from app.models.ai_chat import ChatConversation, ChatMessage
from app.services.ai.chat_service import ChatSessionHandler
from app.schemas.ai import ChatConversationResponse, ChatMessageResponse

router = APIRouter()

@router.get("/conversations", response_model=APIResponse[list[ChatConversationResponse]])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatConversation).where(ChatConversation.user_id == current_user.id).order_by(ChatConversation.last_message_at.desc())
    result = await db.execute(stmt)
    return create_success_response(data=result.scalars().all())

@router.get("/conversations/{conversation_id}/messages", response_model=APIResponse[list[ChatMessageResponse]])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    stmt = select(ChatConversation).where(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    )
    conv = (await db.execute(stmt)).scalars().first()
    if not conv:
        raise NotFoundError("Conversation not found")
        
    msg_stmt = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.created_at.asc())
    msgs = (await db.execute(msg_stmt)).scalars().all()
    return create_success_response(data=msgs)

@router.websocket("/ws")
async def chat_ws(websocket: WebSocket, token: str, conversation_id: str | None = None, db: AsyncSession = Depends(get_db)):
    try:
        class MockCredentials:
            def __init__(self, t):
                self.credentials = t
        
        user_id = _extract_user_id(MockCredentials(token))
        user = await user_repository.get_by_id(db, user_id)
        if not user:
            raise UnauthorizedError()
    except Exception:
        await websocket.close(code=4401)
        return
        
    profile = await profile_repository.get_by_user_id(db, user.id)
    if user.role != UserRole.USER or not profile or profile.companion_preference == CompanionPreference.NONE:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    handler = ChatSessionHandler(websocket, user, db, conversation_id)
    await handler.run()
