import uuid
import json
import logging
from typing import Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncAzureOpenAI

from app.core.config import settings
from app.models.user import User
from app.models.ai_chat import ChatConversation, ChatMessage, ChatRole
from app.services.ai.context_tools import TOOLS_SCHEMA, execute_tool

logger = logging.getLogger(__name__)

ORCHESTRATOR_PROMPT = """You are the internal routing Orchestrator for BintiCare, an AI assistant for pregnant mothers.
Your ONLY job is to determine if you need to fetch patient records from the backend to accurately answer the user's latest query.
If you need patient data, call the appropriate tools.
If you do NOT need any personal data (e.g., general medical questions, basic greetings, or chitchat), output exactly the string "NO_TOOLS" and nothing else."""

RESPONDER_PROMPT = """You are a warm, patient maternal-health companion for the BintiCare app.
You speak clearly and calmly, avoid clinical jargon, never diagnose, and always encourage the mother to contact her facility or clinician for anything concerning.
Below, you may be provided with raw backend data about the user's pregnancy, risks, or schedule. Use this data to accurately inform the user, but weave it naturally into a conversational, empathetic response."""

class ChatSessionHandler:
    def __init__(self, websocket: WebSocket, user: User, db: AsyncSession, conversation_id: Optional[str] = None):
        self.websocket = websocket
        self.user = user
        self.db = db
        self.requested_conversation_id = conversation_id
        self.conversation: Optional[ChatConversation] = None
        
        # Instantiate Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        ) if settings.AZURE_OPENAI_API_KEY else None

    async def run(self):
        try:
            self.conversation = await self._get_or_create_conversation()
            await self.websocket.send_json({"type": "connected", "conversation_id": str(self.conversation.id)})
            
            while True:
                data = await self.websocket.receive_json()
                if data.get("type") == "user_message":
                    content = data.get("content")
                    if content:
                        await self._handle_user_message(content)
                        
        except WebSocketDisconnect:
            logger.info(f"User {self.user.id} disconnected from chat.")
        except Exception as e:
            logger.error(f"Chat error: {e}")
            try:
                await self.websocket.send_json({"type": "error", "code": "UPSTREAM_UNAVAILABLE", "message": str(e)})
            except:
                pass

    async def _get_or_create_conversation(self) -> ChatConversation:
        if self.requested_conversation_id:
            try:
                c_id = uuid.UUID(self.requested_conversation_id)
                stmt = select(ChatConversation).where(
                    ChatConversation.id == c_id, 
                    ChatConversation.user_id == self.user.id
                )
                result = await self.db.execute(stmt)
                conv = result.scalars().first()
                if conv:
                    return conv
            except ValueError:
                pass
                
        stmt = select(ChatConversation).where(ChatConversation.user_id == self.user.id).order_by(ChatConversation.last_message_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        conv = result.scalars().first()
        if not conv:
            conv = ChatConversation(user_id=self.user.id)
            self.db.add(conv)
            await self.db.commit()
            await self.db.refresh(conv)
        return conv

    async def _handle_user_message(self, content: str):
        msg = ChatMessage(conversation_id=self.conversation.id, role=ChatRole.USER, content=content)
        self.db.add(msg)
        self.conversation.last_message_at = datetime.utcnow()
        await self.db.commit()

        if not self.client:
            await self.websocket.send_json({"type": "error", "code": "UPSTREAM_UNAVAILABLE", "message": "OpenAI not configured."})
            return

        stmt = select(ChatMessage).where(ChatMessage.conversation_id == self.conversation.id).order_by(ChatMessage.created_at.asc()).limit(15)
        history = (await self.db.execute(stmt)).scalars().all()
        
        # --- PHASE 1: ORCHESTRATOR ---
        orch_messages = [{"role": "system", "content": ORCHESTRATOR_PROMPT}]
        for m in history:
            role = m.role.value.lower()
            if role == "tool": continue # Hide raw DB output from Orchestrator reasoning
            orch_messages.append({"role": role, "content": m.content})
            
        orch_response = await self.client.chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=orch_messages,
            tools=TOOLS_SCHEMA,
            stream=False
        )
        orch_msg = orch_response.choices[0].message
        
        # --- PHASE 2: TOOL EXECUTION ---
        tool_results_context = []
        tool_calls_record = []
        
        if orch_msg.tool_calls:
            for tc in orch_msg.tool_calls:
                tool_name = tc.function.name
                await self.websocket.send_json({"type": "tool_call_started", "tool_name": tool_name})
                
                result = await execute_tool(tool_name, self.db, user_id=self.user.id)
                result_str = json.dumps(result)
                
                tool_results_context.append(f"{tool_name} returned: {result_str}")
                tool_calls_record.append({"name": tool_name})
                
                await self.websocket.send_json({"type": "tool_call_finished", "tool_name": tool_name})
                
            db_tool_msg = ChatMessage(
                conversation_id=self.conversation.id, 
                role=ChatRole.TOOL, 
                content=" | ".join(tool_results_context),
                tool_calls=tool_calls_record
            )
            self.db.add(db_tool_msg)
            await self.db.commit()

        # --- PHASE 3: RESPONDER ---
        resp_messages = [{"role": "system", "content": RESPONDER_PROMPT}]
        
        # We add the history up to the message before this one
        for m in history[:-1]:
            role = m.role.value.lower()
            if role == "tool": continue
            resp_messages.append({"role": role, "content": m.content})
            
        # Inject the context gathered by the Orchestrator
        if tool_results_context:
            context_str = "Backend data retrieved for the user based on their query:\n" + "\n".join(tool_results_context)
            resp_messages.append({"role": "system", "content": context_str})
            
        # Append the actual current user message
        resp_messages.append({"role": "user", "content": content})
            
        response_stream = await self.client.chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=resp_messages,
            stream=True
        )
        
        assistant_content = ""
        async for chunk in response_stream:
            if len(chunk.choices) == 0: continue
            delta = chunk.choices[0].delta
            if delta.content:
                assistant_content += delta.content
                await self.websocket.send_json({"type": "token", "delta": delta.content})
                
        await self.websocket.send_json({"type": "message_complete"})
        
        db_msg = ChatMessage(conversation_id=self.conversation.id, role=ChatRole.ASSISTANT, content=assistant_content)
        self.db.add(db_msg)
        await self.db.commit()
