# AI Companion — API Reference (Mobile / Mother-facing)

**Base paths:** `/api/v1/ai`, `/api/v1/chat`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` (role `USER`) unless noted

The AI Companion is a real-time text chat assistant, grounded in the mother's own pregnancy/postpartum/medical data when she's granted consent. It's gated behind `Profile.companion_preference` (`AI_DOC` \| `PERSONAL_DOCTOR` \| `BOTH` \| `NONE` — see `docs/mobile/profile.md`); a mother whose preference is `NONE` or `PERSONAL_DOCTOR` never sees this feature, and the server rejects connection attempts for `NONE` too.

> **Only text chat is implemented today.** An earlier design doc for a real-time video avatar (Tavus/WebRTC) exists in the repo's history but has no corresponding routes in the codebase — treat any video-avatar mention elsewhere as future/unimplemented, not current API surface.

---

## 1. Consent

Before the AI Companion can access backend context (pregnancy stage, risk score, upcoming visits, medical history summary), the client must explicitly grant consent. Without it, the assistant gives general-knowledge responses only, with zero access to the mother's records.

### POST `/ai/consent`

Grants the AI Companion persistent access to the mother's context. Creates a `Consent` record with `grantee_id: "AI_COMPANION"` (visible later via `GET /profile/me/consents`, see `docs/mobile/profile.md`).

**Response `200 OK`**
```json
{
  "success": true,
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

**Errors:** `403 FORBIDDEN` if the caller's role isn't `USER`.

### DELETE `/ai/consent`

Revokes previously granted consent, immediately disabling context access for future interactions.

**Response `200 OK`** — same shape, `active: false`, `revoked_at` set.

---

## 2. Context Summary

### GET `/ai/context-summary`

Returns a condensed text summary of the mother's current pregnancy, risk score, upcoming visits, and profile preferences — meant to be fetched once and reused as grounding context, rather than the chat's own tool-calling loop. Returns a generic "no context available" string if consent hasn't been granted.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "summary": "Stage: PREGNANT. Pregnancy: week 32, 3 trimester. Risk level: LOW (Score: 2). Next ANC visit: 2026-07-28T10:00:00Z. History: Prev pregnancies: 1."
  }
}
```

**Errors:** `403 FORBIDDEN` if the caller's role isn't `USER`.

---

## 3. Chat (WebSocket)

### Connect

```
WSS /api/v1/chat/ws?token=<access_token>&conversation_id=<optional_uuid>
```

WebSocket clients can't reliably attach an `Authorization` header, so the JWT travels as a query parameter over `wss://` (TLS-encrypted — same trust model as the REST API).

**Query Parameters**

| Param | Required | Notes |
|---|---|---|
| `token` | ✅ | Access token |
| `conversation_id` | ❌ | Resume a past conversation; if omitted, resumes the most recent one or creates a new one |

The server closes the connection with code `4401` (unauthorized) or `4403` (role/preference not eligible — see the gating rule above) if the connection isn't allowed.

### Wire Protocol

**Client → Server**
```json
{ "type": "user_message", "content": "Is it normal to have swollen ankles at 32 weeks?" }
```

**Server → Client**, a sequence of typed events per turn:

| `type` | Payload | Meaning |
|---|---|---|
| `connected` | `{ conversation_id }` | Handshake ack, conversation created/resumed |
| `token` | `{ delta }` | One streamed text chunk of the answer |
| `tool_call_started` | `{ tool_name }` | Model is fetching the mother's data (drives a "checking your records…" indicator) |
| `tool_call_finished` | `{ tool_name }` | Fetch complete — the result itself is never sent to the client, only used server-side to ground the answer |
| `message_complete` | `{ message_id }` | Full answer streamed, turn done |
| `error` | `{ code, message }` | Non-fatal turn-level error |

Example turn:
```json
{"type": "connected", "conversation_id": "d4769b50-fa5a-4c13-bed2-422af7e2fc7f"}
{"type": "tool_call_started", "tool_name": "get_current_pregnancy"}
{"type": "tool_call_finished", "tool_name": "get_current_pregnancy"}
{"type": "token", "delta": "It "}
{"type": "token", "delta": "is "}
{"type": "token", "delta": "normal..."}
{"type": "message_complete", "message_id": "..."}
```

If consent has not been granted, the tool-calling loop is bypassed entirely — the model streams a general-knowledge response with `tool_call_*` events never firing.

---

## 4. Chat History

### GET `/chat/conversations`

Lists the mother's past AI chat sessions, most recently active first.

**Response `200 OK`**
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

### GET `/chat/conversations/{conversation_id}/messages`

Retrieves the full message history for a conversation, to render the chat UI before opening the WebSocket.

**Response `200 OK`**
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

Note: messages with `role: "TOOL"` are internal audit records of what data was fetched for a turn — they generally don't need to be rendered in the chat UI.

**Errors:** `404 NOT_FOUND` if the conversation doesn't exist or doesn't belong to the caller.

---

## Data Access Boundaries

- The AI never writes to the database — it can only *read* narrow, purpose-shaped summaries (current stage, risk level, next visit, etc.), never raw records or `MedicalHistoryRecord.custom_fields` verbatim.
- The `user_id` bound to every tool call always comes from the authenticated JWT, never from the model — the model chooses *which* tool to call, never *whose* data it reads.
- Personal Doctor Chat (a human clinician thread, as distinct from this AI companion) is not implemented — there is no equivalent REST/WebSocket surface for messaging an assigned clinician directly today.
