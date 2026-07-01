# Profile Module — API Reference

**Base path:** `/api/v1/profile`
**Authentication:** All endpoints require 🔒 `Authorization: Bearer <access_token>`

---

## POST `/me`

Creates a profile for the authenticated user. Returns `409` if a profile already exists — use `PUT /me` to update instead.

**Request Body** — All fields optional.
```json
{
  "current_stage": "PREGNANT",
  "emergency_sharing_preference": "ASK_FIRST",
  "notification_preference": "NOTIFICATION",
  "emergency_contact": {
    "name": "James Kamau",
    "relationship": "Husband",
    "phone": "+254721556002"
  },
  "companion_preference": "BOTH",
  "preferred_unit_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
}
```

**Response `201 Created`** — `ProfileRead` object (see GET `/me` for the shape).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Profile already exists for this user |
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `422` | `VALIDATION_ERROR` | Invalid enum value |

---

## GET `/me`

Returns the authenticated user's profile. If no profile record exists yet, one is auto-created with empty defaults.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
    "current_stage": "PREGNANT",
    "preferred_unit_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6", "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed"],
    "emergency_sharing_preference": "ASK_FIRST",
    "notification_preference": "NOTIFICATION",
    "emergency_contact": {
      "name": "James Kamau",
      "relationship": "Husband",
      "phone": "+254721556002"
    },
    "companion_preference": "BOTH",
    "personal_doctor_id": null,
    "personal_doctor_request_status": null,
    "qr_passport_token": null,
    "created_at": "2026-07-01T09:00:00Z",
    "updated_at": "2026-07-01T09:00:00Z"
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |

---

## PUT `/me`

Partially updates the authenticated user's profile. All fields are optional — only send what you want to change.

**Request Body**
```json
{
  "current_stage": "PREGNANT",
  "emergency_sharing_preference": "ASK_FIRST",
  "notification_preference": "NOTIFICATION",
  "emergency_contact": {
    "name": "James Kamau",
    "relationship": "Husband",
    "phone": "+254721556002"
  },
  "companion_preference": "BOTH",
  "preferred_unit_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6", "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed"]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `current_stage` | enum | ❌ | `PREGNANT` \| `POSTPARTUM` \| `NOT_PREGNANT` |
| `emergency_sharing_preference` | enum | ❌ | `ASK_FIRST` \| `ALWAYS_SHARE` \| `NEVER_SHARE` |
| `notification_preference` | enum | ❌ | `SMS` \| `NOTIFICATION` |
| `emergency_contact` | object | ❌ | Pass `null` to clear |
| `emergency_contact.name` | string | ❌ | |
| `emergency_contact.relationship` | string | ❌ | |
| `emergency_contact.phone` | string | ❌ | |
| `companion_preference` | enum | ❌ | `AI_DOC` \| `PERSONAL_DOCTOR` \| `BOTH` \| `NONE` |
| `preferred_unit_ids` | UUID[] | ❌ | Array of facility UUIDs |

**Response `200 OK`** — Updated `ProfileRead` object (same shape as `GET /me`).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `422` | `VALIDATION_ERROR` | Invalid enum value |

---

## GET `/me/qr`

Returns the user's QR passport token. Generates one if it doesn't exist yet.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "qr_passport_token": "abc123xyz..."
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |

---

## POST `/me/qr/refresh`

Regenerates the user's QR passport token, invalidating the old one. Use this when the user suspects their QR code has been misused.

**Request Body** — None.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "qr_passport_token": "newtoken456..."
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |

---

## POST `/me/personal-doctor-request`

Submits a request to a facility for a personal doctor assignment. Sets `personal_doctor_request_status` to `PENDING` until a `FACILITY_ADMIN` assigns one.

**Request Body**
```json
{
  "facility_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `facility_id` | UUID | ✅ | The facility to request a doctor from |

**Response `200 OK`** — Updated `ProfileRead` object with `personal_doctor_request_status: "PENDING"`.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `422` | `VALIDATION_ERROR` | `facility_id` is not a valid UUID |

---

## Enum Reference

| Enum | Values |
|---|---|
| `current_stage` | `PREGNANT`, `POSTPARTUM`, `NOT_PREGNANT` |
| `emergency_sharing_preference` | `ASK_FIRST`, `ALWAYS_SHARE`, `NEVER_SHARE` |
| `notification_preference` | `SMS`, `NOTIFICATION` |
| `companion_preference` | `AI_DOC`, `PERSONAL_DOCTOR`, `BOTH`, `NONE` |
| `personal_doctor_request_status` | `ASSIGNED`, `PENDING`, `REJECTED` *(read-only — set by server/admin)* |
