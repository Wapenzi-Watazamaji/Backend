# Notifications — System & Internal APIs (Web Dashboard / Backend)

**Base path:** `/api/v1/notifications`
**Authentication:** Varies — see each endpoint.

> A mother's own reminders, device registration, notification inbox, and SMS preference are documented in [`docs/mobile/reminders-notifications.md`](../mobile/reminders-notifications.md). This doc covers backend-internal endpoints and the web dashboard's live alert channel.

---

## POST `/sms/send` — Internal

Sends a templated SMS. Triggered server-side (e.g. on emergency referral creation), not called directly by either client — documented here for backend/ops reference.

**Request Body**
```json
{
  "toPhoneNumber": "+254712345678",
  "templateId": "appointment_reminder",
  "variables": {
    "motherName": "Jane Doe",
    "facilityName": "Karen Health Center",
    "appointmentDate": "2026-07-14 09:00"
  }
}
```

**Response `200 OK`**
```json
{ "success": true, "data": { "smsId": "sms_9911", "status": "SENT" } }
```

---

## POST `/sms/inbound-webhook` — Public (gateway callback)

Receives inbound SMS replies from the SMS gateway (Africa's Talking). Used by `SMS_ONLY` patients (no app session) to interact with the platform purely by text — see the "Offline SMS" section in `docs/mobile/reminders-notifications.md` for the full command list (check-in replies, `vitals ...`, `get facilities ...`, `register facility ...`, `request doctor`).

**Request Body** (gateway-defined shape, example)
```json
{
  "from": "+254712345678",
  "text": "1",
  "linkedReminderId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
}
```

**Response `200 OK`** — `{ "success": true, "data": null }`

---

## Clinician & Facility Admin SMS Alerts

Since clinicians and facility admins use the web dashboard rather than a mobile app, critical real-time alerts are additionally sent to their registered phone numbers via SMS (and mirrored into the dashboard's inbox / WebSocket feed below):

1. **Patient doctor assignment** — SMS when a patient registers or is assigned to them.
2. **Danger signs detected** — SMS immediately when an assigned patient's daily vitals contain flagged danger signs.
3. **Emergency broadcasts** — Critical SMS broadcast to all registered clinicians/admins at a facility when a mother triggers an emergency SOS there.

These are fire-and-forget side effects of other endpoints (vitals submission, emergency creation) — there's no dedicated endpoint to call for them.

---

## Real-Time WebSocket Channel

Lets web clients listen to a persistent WebSocket for immediate, non-blocking notification alerts (for custom warning cards / audio chimes on the dashboard).

**URL:** `ws://<host>/api/v1/notifications/ws/{user_id}`

**Path Parameters:** `user_id` (UUID, required) — the authenticated clinician/admin/user's ID.

**Message Payload (JSON)**
```json
{
  "id": "e4f8b9d3-6e42-4f3b-8d1a-4c2b9a1d8e5f",
  "userId": "d2a6b3f7-9c8e-4a1d-8f2b-9e4a3b1d7f6c",
  "category": "EMERGENCY_ALERT",
  "title": "Emergency Assistance Requested",
  "body": "CRITICAL EMERGENCY: Patient Jane Doe has requested emergency assistance. Notes: Severe labor pain. Phone: +254712345678.",
  "isRead": false,
  "relatedEntityType": "EMERGENCY_REQUEST",
  "relatedEntityId": "f7a6b2c8-9d4e-4a3b-8f1a-2c9b6a1d8e5f",
  "createdAt": "2026-07-13T08:35:00Z"
}
```

Each message mirrors a row that also appears in `GET /notifications` (see `docs/mobile/reminders-notifications.md`) — the WebSocket is a push channel for the same underlying `Notification` records, not a separate data source.
