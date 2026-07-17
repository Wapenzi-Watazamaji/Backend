# AI Chat & Assistant API Documentation

This document outlines the endpoints available for the AI Chat Companion and Tavus Video Avatar integrations. All routes require standard Bearer token authentication via JWT.

## 1. Data Access Consent

Before the AI Companion can access backend context (for both the Tavus Video Avatar and Text Chat), the client must explicitly grant consent. If no consent is granted, the AI returns general responses and `context-summary` returns an empty string or generic message.

### Grant Consent
Grants the AI Companion persistent access to the mother's context.

**HTTP Request:**
`POST /api/v1/ai/consent`

**Headers:**
`Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "AI Companion consent granted.",
  "data": {
    "id": "e45a2c13-bed2-422a-f7e2-fc7f3a4b5c6d",
    "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "consent_type": "AUTO_SHARE",
    "grantee_id": "AI_COMPANION",
    "grantee_name": "AI Companion",
    "active": true,
    "granted_at": "2026-07-17T09:30:00Z",
    "revoked_at": null
  }
}
```

### Revoke Consent
Revokes previously granted consent.

**HTTP Request:**
`DELETE /api/v1/ai/consent`

**Headers:**
`Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "AI Companion consent revoked.",
  "data": { ... }
}
```

---

## 2. Tavus Video Avatar Integration

### Get Context Summary
Retrieves a highly condensed text summary of the mother's current pregnancy, risk score, upcoming visits, and profile preferences. This is meant to be fetched by the client and passed directly into the Tavus API as the `conversational_context`. Requires active consent granted via `/api/v1/ai/consent`.

**HTTP Request:**
`GET /api/v1/ai/context-summary`

**Headers:**
`Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "summary": "Stage: PREGNANT. Pregnancy: week 32, 3 trimester. Risk level: LOW (Score: 2). Next ANC visit: 2026-07-28T10:00:00Z. History: Prev pregnancies: 1."
}
```

---

## 3. Text Chat Companion (WebSocket)

### Connect to Chat
Opens a persistent WebSocket connection to stream chat messages directly from Azure OpenAI.

**WebSocket URL:**
`ws://<server-domain>/api/v1/chat/ws?token=<jwt_token>&conversation_id=<optional_uuid>`

**Query Parameters:**
- `token` (required): The user's JWT access token.
- `conversation_id` (optional): The UUID of a past conversation to resume. If omitted, it will automatically connect to the user's most recent conversation, or create a new one if none exists.

**Message Protocol:**
The connection uses JSON over WebSockets.

**Client -> Server (Send Message):**
```json
{
  "type": "user_message",
  "content": "Is it normal to have swollen ankles at 32 weeks?"
}
```

**Server -> Client (Receive Responses):**
The server streams the response back in chunks, along with metadata about tool executions.

1. **Connection Success:**
   ```json
   {"type": "connected", "conversation_id": "d4769b50-fa5a-4c13-bed2-422af7e2fc7f"}
   ```
2. **Text Tokens (The actual AI response streaming):**
   ```json
   {"type": "token", "delta": "It "}
   {"type": "token", "delta": "is "}
   {"type": "token", "delta": "normal..."}
   ```
3. **Tool Call Events (When the AI fetches data from the backend):**
   ```json
   {"type": "tool_call_started", "tool_name": "get_current_pregnancy"}
   {"type": "tool_call_finished", "tool_name": "get_current_pregnancy"}
   ```
4. **Message Complete:**
   ```json
   {"type": "message_complete"}
   ```

---

## 4. Chat History & Management

### List Past Conversations
Retrieve a list of the user's past AI chat sessions, ordered by the most recently active.

**HTTP Request:**
`GET /api/v1/chat/conversations`

**Headers:**
`Authorization: Bearer <token>`

**Response (200 OK):**
```json
[
  {
    "id": "d4769b50-fa5a-4c13-bed2-422af7e2fc7f",
    "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "started_at": "2026-07-14T08:30:00Z",
    "last_message_at": "2026-07-14T08:35:00Z"
  }
]
```

### Get Messages for a Conversation
Retrieve the full message history for a specific conversation to render the chat UI before opening the WebSocket.

**HTTP Request:**
`GET /api/v1/chat/conversations/{conversation_id}/messages`

**Headers:**
`Authorization: Bearer <token>`

**Response (200 OK):**
```json
[
  {
    "id": "e45a2c13-bed2-422a-f7e2-fc7f3a4b5c6d",
    "conversation_id": "d4769b50-fa5a-4c13-bed2-422af7e2fc7f",
    "role": "USER",
    "content": "When is my next visit?",
    "tool_calls": null,
    "created_at": "2026-07-14T08:31:00Z"
  },
  {
    "id": "f56b3d24-cf33-533b-08f3-ed8g4b5c6d7e",
    "conversation_id": "d4769b50-fa5a-4c13-bed2-422af7e2fc7f",
    "role": "ASSISTANT",
    "content": "Your next Antenatal Care visit is scheduled for July 28th.",
    "tool_calls": null,
    "created_at": "2026-07-14T08:31:05Z"
  }
]
```
*(Note: System messages and raw tool outputs are filtered to `role: "TOOL"` and generally do not need to be rendered in the user-facing UI).*
