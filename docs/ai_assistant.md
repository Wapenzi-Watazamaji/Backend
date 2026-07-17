# AI Assistant — Architecture (Chat Companion & Real-Time Video Avatar)

**Stack:** Flutter (mobile client) · FastAPI (this backend) · WebSockets (text streaming) · Tavus CVI (avatar + video pipeline) · Azure OpenAI (reasoning) · PostgreSQL (`asyncpg`) · Redis

**Contents:** 1. Design principles · 2. Shared tool layer · 3. Data models · 4. Chat companion · 5. Video avatar (5.0 MVP scope, 5.1–5.8 production design) · 6. Configuration · 7. Dependencies · 8. Security & compliance · 9. Rollout order

Two related, independently shippable features:

| Feature | What the mother experiences | Transport |
|---|---|---|
| **AI Chat Companion** | Types a question, gets a streamed text answer grounded in her own pregnancy/postpartum/medical data | WebSocket (`wss://`) |
| **Real-Time Video Avatar Assistant** | Taps "Talk to your companion", gets a live face-to-face video conversation with an AI avatar | WebRTC (Tavus/Daily) |

The video avatar ships in two stages: a client-direct build for the hackathon (§5.0, current target) and a server-orchestrated production design (§5.1–§5.8). Both are documented below.

Both features are gated behind the existing `Profile.companion_preference` field (`app/models/profile.py`: `AI_DOC`, `PERSONAL_DOCTOR`, `BOTH`, `NONE`). A mother whose preference is `NONE` or `PERSONAL_DOCTOR` never sees either feature client-side, and the backend rejects session/connection attempts for `NONE` server-side too (§8, point 4). No new "AI enabled" flag needed; this field already covers it.

Both features share one foundation: a read-only "Mother Context" tool layer (§2). Chat calls it directly; the video avatar's production-design adapter (§5.2) calls it too, once that adapter is built. The hackathon build (§5.0) only touches it via one read-only summary endpoint. Building the data-access layer once and consuming it from every orchestration path, present and future, is the core architectural decision in this doc.

---

## 1. Design principles

1. **FastAPI never becomes a medical decision-maker.** The LLM, in either feature, can *read* a mother's records through narrow, purpose-built tools. It cannot write to the database, create `EmergencyRequest` rows, or message clinicians. Anything with real-world consequence stays human-in-the-loop: a UI affordance ("Call your facility", "Alert emergency contact"), not an autonomous agent action.
2. **Least data, not most data.** Tools return compact, purpose-shaped summaries ("32 weeks, risk level MODERATE, next ANC visit in 4 days"), never raw table dumps or the entirety of `MedicalHistoryRecord.custom_fields`. What leaves the FastAPI process toward Azure OpenAI or Tavus is minimized deliberately: that data is leaving BintiCare's direct control.
3. **The `user_id` is never LLM-supplied.** Every tool call is bound server-side to the JWT-authenticated caller. In the production video design, that binding is to the `VideoSession.user_id` FastAPI resolves (§5.3); the current hackathon video build has no server-side tool-calling at all (§5.0), so this invariant applies there only via the one summary read at call start. The model chooses *which* tool to call; it never chooses *whose* data the tool reads. This is the most important security invariant in the design.
4. **One reasoning backend, two front doors.** Chat and video both terminate in Azure OpenAI chat-completions calls carrying the same system prompt philosophy and the same tool registry. Divergence between the two experiences should come from UX, not from two prompt/tool implementations drifting apart independently.
5. **No new infrastructure unless required.** This repo has no task queue (no Celery, RQ, or APScheduler) today. Rather than introduce one just for a session-timeout backstop, §5.5 uses an in-process asyncio loop backed by Redis, already a declared dependency and currently unused in `app/`.

---

## 2. Shared foundation: the Mother Context tool layer

New module: `app/services/ai/context_tools.py`.

This layer adds no new business logic. It's a thin, read-only façade over repositories that already exist (`pregnancy_repository`, `postpartum_repository`, `medical_history_repository`, `cycle_repository`, `profile_repository`). Each function takes a bound `user_id` (never trusted from model output) and an `AsyncSession`, and returns a small JSON-serializable dict shaped for LLM consumption, not a raw ORM object.

### 2.1 Tool registry (v1, read-only)

| Tool name | Backed by | Returns (shape) |
|---|---|---|
| `get_profile_summary` | `profile_repository.get_by_user_id` | `{ current_stage, preferred_language, county, companion_preference }` |
| `get_current_pregnancy` | `pregnancy_repository` (active record) | `{ week_number, trimester, due_date, is_first_pregnancy, status }` |
| `get_pregnancy_risk_score` | `pregnancy_repository` (risk score) | `{ score, level, calculated_at, top_factors: [...] }` |
| `get_anc_visit_schedule` | `pregnancy_repository` (scheduled visits) | `{ next_visit: {...}, missed_count, completed_count }` |
| `get_medical_history_summary` | `medical_history_repository` | `{ blood_type, allergies, chronic_conditions, previous_pregnancies }` (never returns `custom_fields` verbatim — see §8, point 1) |
| `get_postpartum_status` | `postpartum_repository` | `{ baby: {...}, days_postpartum, latest_epds: {score, risk_level} }` |
| `get_cycle_summary` | `cycle_repository` | `{ current_phase, typical_cycle_length_days, last_entry_date }` |
| `get_nutrition_guidance` | `pregnancy_repository` | `{ category, title, summary }[]` (already public/non-PII content) |

Not in v1: `create_emergency_request`, `send_message_to_clinician`, `update_*`, or anything else that mutates state. If a future iteration wants the assistant to *initiate* an escalation, that's a distinct, heavily-audited tool reviewed on its own merits, not folded into this rollout.

### 2.2 Tool definition format

Azure OpenAI (chat) and Tavus's custom LLM layer (video) both speak the OpenAI `tools`/function-calling JSON schema, so one Python-side registry serves both:

```python
# app/services/ai/context_tools.py
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_pregnancy",
            "description": "Get the mother's active pregnancy status: week number, trimester, due date.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    # ... one entry per tool in the table above
]

TOOL_DISPATCH = {
    "get_profile_summary": get_profile_summary,
    "get_current_pregnancy": get_current_pregnancy,
    # ...
}

async def execute_tool(name: str, db: AsyncSession, *, user_id: uuid.UUID) -> dict:
    # user_id is always injected by the orchestrator, never taken from
    # model-supplied arguments — the schemas above define zero
    # user-identifying parameters on purpose.
    handler = TOOL_DISPATCH.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    return await handler(db, user_id=user_id)
```

The tool JSON schemas expose zero identity parameters (no `user_id`, no `patient_id`). That's what makes principle 3 in §1 structurally true, not just a policy we hope holds.

---

## 3. New data models

Two additions to `app/models/`, following existing conventions: UUID PKs, `func.now()` timestamps, string-backed enums with `create_type=False` since Alembic manages the Postgres enum types.

### 3.1 `app/models/ai_chat.py`

```python
class ChatRole(str, PyEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    TOOL = "TOOL"

class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole, name="chat_role_enum", create_type=False), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)  # audit trail of what was fetched
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

`tool_calls` is an audit trail: which tools fired for a turn, not their full result payload. Useful for debugging "why did it say that" without storing PHI a second time inside the chat log.

### 3.2 `app/models/video_session.py`

```python
class VideoSessionStatus(str, PyEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    TIMED_OUT = "TIMED_OUT"
    FAILED = "FAILED"

class VideoSession(Base):
    __tablename__ = "video_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tavus_conversation_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    status: Mapped[VideoSessionStatus] = mapped_column(Enum(VideoSessionStatus, name="video_session_status_enum", create_type=False), nullable=False, default=VideoSessionStatus.PENDING)
    conversation_url: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

Note: `VideoSession` backs the production design in §5.1–§5.8 only. It isn't needed for the hackathon build in §5.0.

Both models get an Alembic revision the usual way (`alembic revision --autogenerate -m "add ai chat and video session models"`), following the naming pattern already used across `alembic/versions/`.

---

## 4. Feature A — Real-Time Chat Companion (WebSocket)

### 4.1 Endpoint & authentication

```
WSS /api/v1/chat/ws?token=<access_token>
```

WebSocket clients (including Flutter's `web_socket_channel`) can't reliably attach an `Authorization` header the way `HTTPBearer` expects for REST calls, so the JWT travels as a query parameter over `wss://` (TLS-encrypted, same trust model the REST API already uses). The route reuses the existing `_extract_user_id` logic from `app/api/deps.py` rather than reimplementing JWT verification.

```python
# app/api/routes/chat_routes.py
@router.websocket("/ws")
async def chat_ws(websocket: WebSocket, token: str, db: AsyncSession = Depends(get_db)):
    try:
        user_id = _extract_user_id_from_raw_token(token)  # thin wrapper around the same jwt.decode logic
        user = await user_repository.get_by_id(db, user_id)
    except UnauthorizedError:
        await websocket.close(code=4401)
        return
    if user.role != UserRole.USER or not user.profile or user.profile.companion_preference == CompanionPreference.NONE:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    await ChatSessionHandler(websocket, user, db).run()
```

Restricting to `UserRole.USER` mirrors the pattern already established by `require_clinician`/`require_facility_admin` in `deps.py`: this is a mother-facing feature, not a clinician tool.

### 4.2 Wire protocol

**Client → Server**
```json
// To send a message
{ "type": "user_message", "content": "Is it normal to have swollen feet at 32 weeks?", "client_message_id": "c-1a2b" }

// To respond to a consent request
{ "type": "provide_consent", "consent": true }
```

**Server → Client**, a sequence of typed events per turn:

| `type` | Payload | Meaning |
|---|---|---|
| `connected` | `{ conversation_id }` | Handshake ack, conversation created/resumed |
| `consent_required` | `{}` | Emitted if the mother's sharing preference requires consent validation before context access |
| `token` | `{ delta }` | One streamed text chunk of the answer |
| `tool_call_started` | `{ tool_name }` | Model is fetching the mother's data (drives a UI "checking your records…" indicator) |
| `tool_call_finished` | `{ tool_name }` | Fetch complete (result itself is never sent to the client — only used server-side to ground the answer) |
| `message_complete` | `{ message_id }` | Full answer streamed, turn done |
| `error` | `{ code, message }` | Non-fatal turn-level error (see §4.5) |
| `pong` | `{}` | Keepalive reply to client `ping` |

Streaming matters here for the same reason it matters in the video flow: perceived latency. A mother asking a question should see the first words appear well under a second, even if the full answer takes longer to complete.

### 4.2a Data Sharing Consent Flow

Access to backend patient records (context tools) is explicitly gated based on persistent AI Companion consent, recorded in the database.
- **Granting Consent**: The client must call `POST /api/v1/ai/consent` to grant the AI Companion access to the user's data. This creates an explicit `Consent` record with `grantee_id="AI_COMPANION"`.
- **Session Handling**: 
  - The server checks for this active consent (`has_ai_consent`) during `GET /api/v1/ai/context-summary` and when initiating websocket sessions.
  - If active consent exists, context tools are enabled for the session.
  - If consent does not exist or has been revoked (via `DELETE /api/v1/ai/consent`), context tools are disabled, and the AI routes to a general-knowledge conversation layout with no backend context.
- **Revoking Consent**: The user can revoke access anytime via `DELETE /api/v1/ai/consent`, immediately disabling context access for future interactions.

### 4.3 Turn sequence

```
Flutter              FastAPI (chat_routes)         Azure OpenAI            Context Tool Layer / DB
  |  user_message         |                              |                         |
  |----------------------->|                              |                         |
  |                       | (If consented):              |                         |
  |                       | append to ChatMessage(USER)  |                         |
  |                       | stream chat.completions ----->|                         |
  |                       |    (messages + tools[])      |                         |
  |                       |<---- delta: tool_call --------|                         |
  |                       | execute_tool(name, user_id) ------------------------>   |
  |                       |<----------------------------------------------------    |
  |                       | append tool result message   |                         |
  |                       | stream chat.completions ----->|  (continuation)         |
  |                       |                              |                         |
  |                       | (If NOT consented):          |                         |
  |                       | bypass orchestrator/tools    |                         |
  |                       | stream chat.completions ----->| (general responder only)|
  |                       |                              |                         |
  |  token, token, token   |<---- delta: content ----------|                         |
  |<-----------------------|                              |                         |
  |                       | append to ChatMessage(ASSISTANT)                       |
  |  message_complete      |                              |                         |
  |<-----------------------|                              |                         |
```

Standard OpenAI-style tool-calling loop (if consented): stream until `finish_reason == "tool_calls"`, execute the requested tool(s) server-side against Postgres, append the tool result as a `role: tool` message, and re-invoke the model. Repeat until `finish_reason == "stop"`, streaming text deltas to the client throughout except for the tool-execution gap (typically under 200ms). If consent was refused, the tool-calling loop is bypassed entirely, avoiding execution of any context tools and prompting general advice.

### 4.4 Connection & rate-limit state in Redis

Redis is declared in `pyproject.toml` and configured in `app/core/config.py` (`REDIS_URL`) but unused anywhere in `app/` today. This feature is a natural first consumer:

- `chat:conn:{user_id}` → connection instance id, with a short TTL refreshed on each message. Lets a second FastAPI worker/instance detect and gracefully close a stale duplicate connection for the same mother (e.g. she reopens the app on two devices).
- `chat:ratelimit:{user_id}` → sliding-window counter (e.g. max 20 turns/minute) to bound Azure OpenAI spend per user and blunt abuse. Exceeding it returns an `error` event with `code: "RATE_LIMITED"` rather than silently dropping the message.

### 4.5 Error handling

| `code` | Trigger | Client behavior |
|---|---|---|
| `RATE_LIMITED` | Redis counter exceeded | Show "slow down" toast, keep socket open |
| `UPSTREAM_UNAVAILABLE` | Azure OpenAI call failed/timed out | Show retry affordance, keep socket open |
| `TOOL_EXECUTION_FAILED` | A context tool raised (e.g. DB timeout) | Model is told the tool failed and asked to answer without that data, or to say it couldn't check |
| close `4401` | Invalid/expired token at handshake | Client re-authenticates, reconnects |
| close `4403` | `companion_preference` is `NONE`, or role isn't `USER` | Client hides the chat entry point entirely (shouldn't normally happen if UI gating is correct) |

### 4.6 Safety guardrails (system prompt contract)

The system prompt (versioned in code, not user-editable) instructs the model to:
1. Answer using the mother's real context when a tool result is available; say plainly when it isn't.
2. Never state a diagnosis. Frame answers as general guidance and explicitly recommend contacting her facility or clinician for anything symptomatic.
3. For a fixed list of red-flag terms (heavy bleeding, severe headache with vision changes, reduced fetal movement, severe abdominal pain, suicidal ideation in a postpartum context), respond with urgent-care guidance. The server independently detects the same keyword list turn-side and emits a `type: "escalation_suggested"` event regardless of what the model does; Flutter renders this as a prominent "Call your facility" / emergency button. This is a deterministic backstop that doesn't depend on the LLM behaving correctly on any given turn.

---

## 5. Feature B — Real-Time Video Avatar Assistant

Adapted from the reference Tavus/Azure OpenAI architecture, retargeted from lecture tutoring to maternal-health companionship. One fact carries over unchanged: video and audio never pass through FastAPI. Tavus's CVI runs on WebRTC; once a session starts, the phone streams directly to Tavus/Daily infrastructure.

The table and the rest of this section describe the full production design, where FastAPI also orchestrates sessions and acts as the "brain" behind the avatar's spoken answers. §5.0 below covers what to actually build first, where FastAPI's role shrinks to a single one-shot read.

| System | Job |
|---|---|
| Flutter app | Captures the mother's speech, joins the video room, renders the avatar |
| FastAPI | Creates/ends Tavus sessions, injects the mother's context, adapts Azure OpenAI to Tavus's expected LLM API shape |
| Tavus CVI | Speech-to-text, avatar face/voice, hosts the WebRTC room |
| Azure OpenAI | Generates answer text, grounded in the mother's context via the same tool layer as chat (§2) |

### 5.0 MVP scope: client-direct integration (current build target)

The rest of §5 (5.1–5.8) specifies the full production architecture: a server-side Tavus/Azure OpenAI adapter, live tool-calling mid-conversation, and session-identity resolution (§5.3). That's the intended end state, but it's also the most time-consuming and fragile part of this document, and it isn't necessary to demonstrate the feature. This is what to build instead, for now:

```
Flutter                          FastAPI                       Tavus CVI
  |  GET /ai/context-summary 🔒     |                              |
  |-------------------------------->|                              |
  |                                | tool layer (§2), no LLM call  |
  |  { summary: "32 weeks, ..." }   |                              |
  |<--------------------------------|                              |
  |  POST /v2/conversations (TAVUS_API_KEY embedded client-side)   |
  |------------------------------------------------------------->  |
  |  conversation_url                                              |
  |<-------------------------------------------------------------  |
  |  join room (WebRTC, direct to Tavus/Daily)                     |
  |<===============================================================>
```

New endpoint: `GET /api/v1/ai/context-summary` (Bearer JWT, role `USER`, gated on `companion_preference` exactly as in §4.1/§5.4). It calls the same read-only tool layer as chat (§2), no LLM, no Tavus, and returns one compact string:

```json
{ "summary": "32 weeks pregnant, first pregnancy, risk level MODERATE, next ANC visit in 4 days." }
```

Flutter fetches this once, then passes `summary` straight through as `conversational_context` when it calls Tavus's `POST /v2/conversations` directly from the client.

This build needs its own Persona: same `system_prompt` as §5.1, but **without** the `layers.llm` override — no `base_url`, no `TAVUS_LLM_SHARED_SECRET`. Leaving that layer unset is what lets Tavus answer using its own default managed LLM instead of trying to reach an adapter that doesn't exist yet. §5.1's persona, wired to the custom adapter, belongs to the production design only — don't point Flutter at it.

Flutter joins the returned `conversation_url` the same way as in the full design.

What this drops, and why that's acceptable for now:
- No `VideoSession` model, webhook receiver, or timeout reaper (§5.5): nothing tracks the call server-side. A stray session gets killed manually from the Tavus dashboard.
- No Azure OpenAI involvement in video answers: the avatar is grounded only by the static summary captured at call start, not by live tool calls mid-conversation. It won't answer follow-up specifics (exact due date, full visit history) as precisely as the full design would.
- No session-identity resolution problem (§5.3): there's no shared backend adapter serving every mother's conversation, so there's nothing to disambiguate.

Trade-off to track: this requires `TAVUS_API_KEY` to live in the Flutter client so it can call Tavus directly, which contradicts §5.7/§8's rule that no secret ships to the client. Treat this as a time-boxed compromise: a client-side API key is extractable from the compiled app by anyone who decompiles it. Before any real launch, move this back behind FastAPI by building out §5.1–§5.7.

---

§5.1–§5.8 describe that full production architecture. Not required for the hackathon build; revisit once the MVP is validated.

### 5.1 One-time setup: the Persona

One shared Persona is enough. The course/lecture-specific detail from the original reference design has no analogue here: what varies per session is the mother's own context, injected at session start (§5.3), not a different persona per condition or stage.

```json
POST https://tavusapi.com/v2/personas
{
  "persona_name": "BintiCare Companion",
  "system_prompt": "You are a warm, patient maternal-health companion. You speak clearly and calmly, avoid clinical jargon, never diagnose, and always encourage the mother to contact her facility or clinician for anything concerning. You have access to tools that read the mother's own BintiCare records — use them before answering questions about her specific pregnancy, risk score, or upcoming visits.",
  "layers": {
    "llm": {
      "model": "gpt-4.1",
      "base_url": "https://<this-api-host>/api/v1/ai/video/completions",
      "api_key": "<TAVUS_LLM_SHARED_SECRET>"
    }
  }
}
```

`TAVUS_LLM_SHARED_SECRET` is a server-to-server credential Tavus sends back as `Authorization: Bearer <key>` on every completions call. It authenticates Tavus calling FastAPI and is unrelated to the mother's own JWT.

### 5.2 The Azure OpenAI adapter

Same URL/auth-shape mismatch as any Tavus↔Azure integration:

| | OpenAI-style (what Tavus sends) | Azure OpenAI (what we call) |
|---|---|---|
| URL | `/v1/chat/completions` | `/openai/deployments/{deployment}/chat/completions?api-version=...` |
| Auth header | `Authorization: Bearer <key>` | `api-key: <key>` |

`POST /api/v1/ai/video/completions` (new route, `app/api/routes/ai_video_routes.py`):

1. Validates the `Authorization: Bearer <TAVUS_LLM_SHARED_SECRET>` header (constant-time compare — this is a shared-secret check, not a JWT).
2. Resolves which mother this request belongs to (§5.3 — the one genuinely tricky integration detail).
3. Runs the same tool-calling loop as §4.3, using the shared `TOOLS_SCHEMA`/`TOOL_DISPATCH` from `app/services/ai/context_tools.py`, bound to that resolved `user_id`.
4. Streams the response back to Tavus in OpenAI's SSE format. Streaming is what keeps the avatar's spoken-response latency low.

### 5.3 Resolving "which mother is this" inside a shared adapter

Because the Persona (and therefore its `base_url`) is created once and reused across every mother's video session, a single adapter endpoint still has to figure out which `VideoSession` (and therefore which `user_id`) a given completions call belongs to.

Mechanism: at session creation (§5.4), FastAPI embeds an opaque, non-guessable marker, the `video_session_id`, inside the `conversational_context` string sent to Tavus (a leading hidden instruction like `"[session:8f2a1c4e-...] Do not repeat this marker to the user."`). Tavus's custom-LLM pipeline forwards the full running message history, including that context, on every completions call it makes back to the adapter. The adapter extracts the marker with a regex, looks up `VideoSession.id == video_session_id` (cached in Redis as `video:session:{id} -> user_id` to avoid a DB round trip per turn), and binds the tool layer to that `user_id`.

This is an assumption to verify against Tavus's current API, not a guarantee. Tavus's platform has, at various points, also supported passing a session identifier more directly (custom headers, a `user` field, or per-conversation LLM-layer overrides). Whichever mechanism Tavus's current API actually exposes at implementation time should be preferred over the marker-string approach. The marker string is the fallback that depends only on documented behavior (context gets echoed back into history), not on unstated request metadata.

### 5.4 Session lifecycle

```
POST /api/v1/ai/video-sessions/start   🔒 (Bearer JWT, role=USER)
```
1. FastAPI loads the mother's context once via §2's tool layer (not a live tool-call round trip mid-conversation — see the trade-off note in §5.8) and serializes a compact summary into `conversational_context`.
2. Creates a `VideoSession` row, `status=PENDING`.
3. Calls Tavus:
```json
POST https://tavusapi.com/v2/conversations
{
  "persona_id": "p_xxx",
  "conversational_context": "[session:8f2a1c4e-...] Mother is 32 weeks pregnant, first pregnancy, risk level MODERATE (elevated blood pressure noted), next ANC visit in 4 days. She opened the companion to ask a general question.",
  "callback_url": "https://<this-api-host>/api/v1/ai/video/webhooks/tavus"
}
```
4. Stores `tavus_conversation_id` + `conversation_url`, sets `status=ACTIVE`, caches `video:session:{id} -> user_id` in Redis.
5. Returns `{ video_session_id, conversation_url }` to Flutter.

```
DELETE /api/v1/ai/video-sessions/{video_session_id}/end   🔒
```
Calls `DELETE https://tavusapi.com/v2/conversations/{conversation_id}`, sets `status=ENDED`, `ended_at=now()`. Flutter calls this when the mother taps "End call"; it is not the only way a session ends (see §5.5).

```
POST /api/v1/ai/video/webhooks/tavus   (Tavus → FastAPI, shared-secret auth)
```
Receives `utterance`, `conversation.started`, `conversation.ended`, and perception events. Used to bump `VideoSession.last_activity_at` (drives the idle-timeout check below) and, optionally, to log Q&A pairs for support/QA — deliberately not into `ChatMessage`, since that table is scoped to the text-chat feature. A session transcript, if kept, belongs on `VideoSession` or a dedicated log, not commingled with chat history.

### 5.5 Timeout/cost backstop without a task queue

Tavus bills per conversation-minute, so prompt cleanup matters. Relying solely on the Flutter client calling `/end` isn't sufficient: the app can crash, lose connectivity, or the mother can just walk away. Since this repo has no Celery, RQ, or APScheduler, the backstop is an in-process asyncio loop started from a FastAPI `lifespan` handler in `app/main.py`:

```python
async def _video_session_reaper():
    while True:
        await asyncio.sleep(30)
        stale = await video_session_repository.find_active_past(
            db, max_duration=settings.VIDEO_SESSION_MAX_DURATION_SECONDS,
            idle_after=settings.VIDEO_SESSION_IDLE_TIMEOUT_SECONDS,
        )
        for session in stale:
            await end_video_session(session, reason="TIMED_OUT")
```

Single-instance-only mechanism: if FastAPI is ever horizontally scaled, this loop runs once per instance and needs a Redis-based lock (`SET reaper:lock NX PX 30000`) so only one instance sweeps at a time. That's a one-line addition when the time comes, not a redesign, noted here so it isn't forgotten.

### 5.6 Sequence summary

```
Flutter          FastAPI               Tavus CVI            Azure OpenAI
  |  POST /start     |                     |                     |
  |------------------>|                     |                     |
  |                  | build context from  |                     |
  |                  | tool layer (§2)     |                     |
  |                  | create conversation |                     |
  |                  |--------------------->|                     |
  |                  |<---------------------|                     |
  |  conversation_url |  conversation_url   |                     |
  |<------------------|                     |                     |
  |  join room (WebRTC, direct to Tavus/Daily)                    |
  |<========================================>|                    |
  |                  |                     | POST /video/completions
  |                  |<---------------------|                     |
  |                  | resolve session→user_id (§5.3)             |
  |                  | tool-calling loop (§2/§4.3) --------------->|
  |                  |<---------------------------------------------
  |                  |---------------------->|  (streamed SSE)     |
  |                  |                     | TTS + lip-sync, streams to phone
```

### 5.7 Auth boundary

- Flutter → FastAPI: mother's JWT, same as every other endpoint in this codebase.
- FastAPI → Tavus: `TAVUS_API_KEY`, server-side only.
- Tavus → FastAPI adapter: `TAVUS_LLM_SHARED_SECRET`, distinct from `TAVUS_API_KEY` and from any mother's JWT. A compromised adapter secret shouldn't grant Tavus (or an attacker who obtained it) the ability to call any other BintiCare endpoint.
- FastAPI → Azure OpenAI: `AZURE_OPENAI_API_KEY`, server-side only.
- None of the three secrets above are ever sent to the Flutter client.

### 5.8 Decisions to make before building

| Decision | Recommendation | Why |
|---|---|---|
| Context injection: static (once, at session start) vs. live tool-calls mid-conversation | **Static summary at start, same as §5.4**, with the same tool layer still reachable live if the model asks a specific question the static summary didn't cover | A mother's records don't change mid-call; a static snapshot avoids adding tool-call latency to every spoken turn, while the adapter still supports live tool calls as a fallback for specificity |
| Persona granularity | **One shared "Companion" persona** (as in §5.1), context varies per session | Matches the original reference design's own recommendation; per-stage personas (pregnancy vs. postpartum) would be pure duplication of the system prompt for no behavioral gain, since context injection already carries the stage-specific detail |
| Feature gating | Gate on `Profile.companion_preference in (AI_DOC, BOTH)` | The field already exists for this exact purpose — don't invent a parallel flag |
| Timeout/cost controls | Hard max duration (e.g. 10 min) + idle timeout (e.g. 90s of no utterance) via §5.5 | Tavus bills per minute; a silent abandoned call is pure cost with no benefit |
| Backend involvement during hackathon/MVP | **None** — Flutter talks to Tavus directly, backend only serves one static context-summary read (§5.0) | The adapter and session-resolution machinery isn't justified before the concept is validated; revisit before any real launch |

---

## 6. New configuration

Additions to `app/core/config.py`'s `Settings`:

```python
class Settings(BaseSettings):
    ...
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT: str
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"

    TAVUS_API_KEY: str
    TAVUS_PERSONA_ID: str
    TAVUS_LLM_SHARED_SECRET: str

    VIDEO_SESSION_MAX_DURATION_SECONDS: int = 600
    VIDEO_SESSION_IDLE_TIMEOUT_SECONDS: int = 90

    CHAT_RATE_LIMIT_PER_MINUTE: int = 20
```

All secret-shaped values load from `.env` the same way `SECRET_KEY`/`DB_PASSWORD` already do: none are hardcoded, none ship to the client.

Note: the `TAVUS_*` and `VIDEO_SESSION_*` entries above back the production video design (§5.1–§5.8) only. The current hackathon build (§5.0) never calls Tavus from the backend, so none of them are needed yet — `AZURE_OPENAI_*` is the only block this build actually requires, and only for the chat companion.

---

## 7. New dependencies

`pyproject.toml` additions:

```toml
dependencies = [
    ...
    "openai>=1.0.0",       # Azure OpenAI async client, streaming chat.completions
    "httpx>=0.27.0",       # promote from dev-only to runtime — used for server-side Tavus REST calls
]
```

WebSocket support for the chat route is already covered transitively by `uvicorn[standard]` (which bundles `websockets`); no separate addition needed there.

`httpx` is only exercised server-side once the production video adapter (§5.2) exists. The hackathon build calls Tavus from Flutter, not from FastAPI, so this promotion can wait until that track starts.

---

## 8. Security & compliance notes

1. **Minimize what leaves the process.** Tool outputs sent to Azure OpenAI/Tavus are summaries (§2, §1 point 2), never raw `custom_fields` JSONB or full `surgical_history` records. If a future tool needs finer detail, shape that tool's return value narrowly rather than widening an existing one.
2. **Consent is still an open question.** The existing `Consent`/`ConsentType` model (`ASK_EVERYTIME` / `AUTO_SHARE` / `FACILITY_AUTO_SHARE`) governs sharing a mother's data with other facilities/clinicians during referrals; it doesn't currently model "mother has acknowledged her data will be processed by Azure OpenAI/Tavus as AI infrastructure providers." That's a distinct consent surface (likely a one-time in-app acknowledgment before first use of either feature) and should be decided with product/legal before launch, not assumed away.
3. **No autonomous writes.** Restated from §1: nothing the LLM does in either feature can create, modify, or delete a database row. This is enforced structurally (the tool registry contains no write tools), not just by prompt instruction.
4. **Role + preference gating enforced server-side**, not just hidden in the Flutter UI (§4.1, §5.4). A mother with `companion_preference == NONE` should get a `403`/`4403` close code if the client is somehow bypassed, not a working session.
5. **Shared secrets are distinct per trust boundary** (§5.7). The Tavus adapter secret, the Tavus API key, and the Azure OpenAI key are three separate credentials, so rotating or revoking one (e.g. if the adapter endpoint URL leaks) doesn't require rotating the others.

---

## 9. Suggested rollout order

1. **Chat companion, tools only for read-only low-risk data** (`get_current_pregnancy`, `get_anc_visit_schedule`, `get_nutrition_guidance`): smallest surface area, validates the streaming + tool-calling loop end to end (§4).
2. **Expand chat tool registry** to the full set in §2.1, add the Redis rate-limiter and connection registry (§4.4).
3. **Video avatar, client-direct build (§5.0)**: the one new backend endpoint (`/ai/context-summary`) is a thin read on the same tool layer, so it can ship alongside step 1 rather than waiting on step 2. The bulk of this track's work is Tavus persona/contract setup and WebRTC integration in Flutter.
4. **Video avatar, production design (§5.1–§5.8)**: a distinct, larger effort, not a continuation of step 3. Revisit once the MVP is validated, building the server-side adapter and converging at §5.2's route.
5. **Consent surface** (§8, point 2) should land before either feature is enabled for real users, not after.
