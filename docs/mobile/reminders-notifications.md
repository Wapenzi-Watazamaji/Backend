# Reminders & Notifications — API Reference (Mobile / Mother-facing)

**Base paths:** `/api/v1/reminders`, `/api/v1/devices`, `/api/v1/notifications`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` (role `USER`) unless noted

> Internal/system endpoints (templated SMS send, the inbound SMS webhook, and the live WebSocket alert channel used by the web dashboard) live in [`docs/web/notifications-system.md`](../web/notifications-system.md).

---

## Reminders (`/api/v1/reminders`)

### POST `/`

Creates a custom user reminder (e.g. pills, blood pressure check).

**Request Body**
```json
{
  "title": "Take folic acid",
  "type": "MEDICATION",
  "dueAt": "2026-07-15T08:00:00Z"
}
```

`type`: `MEDICATION` \| `APPOINTMENT` \| `CYCLE` \| `VACCINATION` \| `OTHER`

**Response `201 Created`**
```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "userId": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "title": "Take folic acid",
    "type": "MEDICATION",
    "dueAt": "2026-07-15T08:00:00Z",
    "isDone": false,
    "createdAt": "2026-07-13T10:00:00Z",
    "updatedAt": "2026-07-13T10:00:00Z"
  }
}
```

---

### GET `/`

Lists reminders for the authenticated user.

**Query Parameters:** `upcomingOnly` (boolean), `type` (filter, same enum as above)

**Response `200 OK`** — array of `ReminderRead` objects.

---

### PUT `/{reminder_id}`

Updates a custom reminder's title/due date.

**Request Body**
```json
{ "dueAt": "2026-07-15T07:30:00Z" }
```

---

### PUT `/{reminder_id}/mark-done`

Marks a reminder as completed.

**Response `200 OK`** — updated `ReminderRead`, `isDone: true`.

---

### DELETE `/{reminder_id}`

**Response `204 No Content`**

---

## Push Notification Devices (`/api/v1/devices`)

### POST `/register`

Registers a mobile device token to receive push notifications.

**Request Body**
```json
{ "deviceToken": "fcm_token_12345abcdef", "platform": "ANDROID" }
```

`platform`: `ANDROID` \| `IOS` \| `WEB`

**Response `201 Created`**
```json
{ "success": true, "data": { "tokenId": "5e8e8e8e-5717-4562-b3fc-2c963f66afa6" } }
```

---

### DELETE `/{tokenId}`

Unregisters a push token.

**Response `204 No Content`**

---

## In-App Notifications (`/api/v1/notifications`)

### GET `/`

Retrieves the in-app notification inbox.

**Query Parameters:** `unreadOnly` (boolean, default `false`), `page` (default 1), `pageSize` (default 20)

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "f5f5f5f5-f5f5-f5f5-f5f5-f5f5f5f5f5f5",
      "userId": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "category": "APPOINTMENT_REMINDER",
      "title": "Upcoming Visit Reminder",
      "body": "Hi Jane, you have a scheduled visit at Karen Health Center tomorrow.",
      "isRead": false,
      "relatedEntityType": "SCHEDULED_VISIT",
      "relatedEntityId": "a2a2a2a2-a2a2-a2a2-a2a2-a2a2a2a2a2a2",
      "createdAt": "2026-07-13T08:00:00Z"
    }
  ],
  "meta": { "page": 1, "pageSize": 20, "totalItems": 1, "totalPages": 1 }
}
```

---

### PUT `/{id}/read`

Marks a notification as read.

---

## SMS Preferences (`/api/v1/notifications/sms/preferences`)

### GET `/`

Retrieves the user's preferred contact channel. If no profile exists yet, one is auto-bootstrapped.

**Response `200 OK`**
```json
{ "success": true, "data": { "contactPreference": "BOTH" } }
```

`contactPreference`: `SMS` \| `APP_NOTIFICATIONS` \| `BOTH`

---

### PUT `/`

Updates the contact channel preference.

**Request Body**
```json
{ "contactPreference": "SMS" }
```

---

## Offline SMS (SMS-only patients)

Patients registered as `accountType: SMS_ONLY` (no app session — enrolled via `docs/web/facility-admin.md`) never call these REST endpoints directly. Instead their replies to reminder/check-in SMS prompts are converted server-side into records via the inbound webhook documented in `docs/web/notifications-system.md`. This includes offline vitals logging (`"vitals bp 130/85 weight 74.5"`), facility discovery (`"get facilities nairobi"`), facility registration (`"register facility <name>"`), and personal doctor requests (`"request doctor"`) — all reachable purely over SMS.

---

## Standard Error Response Shape

```json
{
  "success": false,
  "message": "Detailed error message",
  "data": null,
  "meta": null,
  "error": { "code": "VALIDATION_ERROR", "message": "Detailed error message" }
}
```
