# Profile Module — API Reference

**Base path:** `/api/v1/profile`
**Authentication:** All endpoints require 🔒 `Authorization: Bearer <access_token>`

---

## POST `/me`

Creates a profile for the authenticated user. Returns `400` if a profile already exists — use `PUT /me` to update instead.

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
  "typical_cycle_length_days": 28,
  "home_address_name": "Kileleshwa, Nairobi",
  "home_location_lat": "-1.2833",
  "home_location_lng": "36.8167",
  "live_location_sharing_enabled": false,
  "preferred_facility_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

**Response `201 Created`** — `ProfileRead` object (see GET `/me` for the shape).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Profile already exists for this user |
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | `preferred_facility_id` does not match an existing facility |
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
    "preferred_facility_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "emergency_sharing_preference": "ASK_FIRST",
    "notification_preference": "NOTIFICATION",
    "emergency_contact": {
      "name": "James Kamau",
      "relationship": "Husband",
      "phone": "+254721556002"
    },
    "companion_preference": "BOTH",
    "typical_cycle_length_days": 28,
    "home_address_name": "Kileleshwa, Nairobi",
    "home_location_lat": "-1.2833",
    "home_location_lng": "36.8167",
    "live_location_sharing_enabled": false,
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
  "typical_cycle_length_days": 28,
  "home_address_name": "Kileleshwa, Nairobi",
  "home_location_lat": "-1.2833",
  "home_location_lng": "36.8167",
  "live_location_sharing_enabled": true,
  "preferred_facility_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `current_stage` | enum | ❌ | `PREGNANT` \| `POSTPARTUM` \| `NOT_PREGNANT` |
| `emergency_sharing_preference` | enum | ❌ | `ASK_FIRST` \| `ALWAYS_SHARE` \| `NEVER_SHARE` |
| `notification_preference` | enum | ❌ | `SMS` \| `NOTIFICATION` \| `BOTH` |
| `emergency_contact` | object | ❌ | Pass `null` to clear |
| `emergency_contact.name` | string | ❌ | |
| `emergency_contact.relationship` | string | ❌ | |
| `emergency_contact.phone` | string | ❌ | |
| `companion_preference` | enum | ❌ | `AI_DOC` \| `PERSONAL_DOCTOR` \| `BOTH` \| `NONE` |
| `typical_cycle_length_days` | integer | ❌ | Baseline for predictions (default 28) |
| `home_address_name` | string | ❌ | Descriptive name of the home address |
| `home_location_lat` | string | ❌ | Latitude of the home address |
| `home_location_lng` | string | ❌ | Longitude of the home address |
| `live_location_sharing_enabled` | boolean | ❌ | True if the app has permission to continuously update live location |
| `preferred_facility_id` | UUID | ❌ | ID of preferred facility |

**Response `200 OK`** — Updated `ProfileRead` object (same shape as `GET /me`).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | Profile does not exist yet — create one via `POST /me` first |
| `404` | `NOT_FOUND` | `preferred_facility_id` does not match an existing facility |
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
| `404` | `NOT_FOUND` | `facility_id` does not match an existing facility |
| `422` | `VALIDATION_ERROR` | `facility_id` is not a valid UUID |

---

## GET `/qr/scan/{token}`

Public endpoint to scan a QR passport token and retrieve the holder's base profile, medical history, and active pregnancy (if any). Used by clinicians/facility staff during emergency lookups.

**Authentication:** None — this is the one endpoint in this module that does **not** require a Bearer token.

**Path Parameters**

| Param | Type | Notes |
|---|---|---|
| `token` | string | The `qr_passport_token` value obtained from `GET /me/qr` |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "QR Passport verified",
  "data": {
    "user": {
      "id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "phone_number": "+254712345678",
      "full_name": "Wanjiru Kamau",
      "role": "USER",
      "date_of_birth": "2000-03-14",
      "gender": "FEMALE",
      "preferred_language": "en",
      "county": "Kilifi",
      "profile_photo_url": null,
      "is_active": true,
      "created_at": "2026-07-01T09:00:00Z",
      "updated_at": "2026-07-01T09:00:00Z"
    },
    "profile": { "...": "same shape as GET /me" },
    "medical_history": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "patient_user_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "blood_type": "O",
      "rh_factor": "+",
      "allergies": ["Penicillin"],
      "chronic_conditions": [],
      "current_medications": [],
      "surgical_history": [],
      "previous_pregnancies": 1,
      "previous_outcomes": [],
      "family_history": [],
      "custom_fields": null,
      "created_by": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "last_updated_by": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "created_at": "2026-07-01T09:00:00Z",
      "updated_at": "2026-07-01T09:00:00Z"
    },
    "active_pregnancy": null
  },
  "meta": {}
}
```

| Field | Type | Notes |
|---|---|---|
| `user` | object | `UserRead` shape — see `auth.md` |
| `profile` | object | `ProfileRead` shape — see `GET /me` above |
| `medical_history` | object \| null | `null` if no medical history record exists |
| `active_pregnancy` | object \| null | `null` if the user has no active pregnancy — see `pregnancy.md` |

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Token does not match any profile (invalid, or was invalidated by a refresh) |

---

## GET `/me/consents` 🔒

Lists all consent grants (active and revoked) the authenticated user has issued — e.g. facilities granted auto-share access to their records.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Consents fetched successfully",
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "user_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "consent_type": "FACILITY_AUTO_SHARE",
      "grantee_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "grantee_name": "Kilifi County Hospital",
      "active": true,
      "granted_at": "2026-07-01T09:00:00Z",
      "revoked_at": null
    }
  ],
  "meta": {}
}
```

| Field | Type | Notes |
|---|---|---|
| `consent_type` | enum | `ASK_EVERYTIME` \| `AUTO_SHARE` \| `FACILITY_AUTO_SHARE` |
| `grantee_id` | string \| null | ID of the facility/entity the consent was granted to |
| `grantee_name` | string \| null | Display name of the grantee |
| `active` | boolean | `false` once revoked |
| `revoked_at` | datetime \| null | Set when the consent is revoked |

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |

---

## PUT `/me/consents/{grantee_id}/revoke` 🔒

Revokes an active consent grant for the given grantee. Sets `active` to `false` and stamps `revoked_at`.

**Path Parameters**

| Param | Type | Notes |
|---|---|---|
| `grantee_id` | string | The `grantee_id` of the consent to revoke (e.g. a facility ID) |

**Request Body** — None.

**Response `200 OK`** — Updated `ConsentRead` object (see `GET /me/consents` for the shape) with `active: false`.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | No active consent found for this `grantee_id` |

---

## Enum Reference

| Enum | Values |
|---|---|
| `current_stage` | `PREGNANT`, `POSTPARTUM`, `NOT_PREGNANT` |
| `emergency_sharing_preference` | `ASK_FIRST`, `ALWAYS_SHARE`, `NEVER_SHARE` |
| `notification_preference` | `SMS`, `NOTIFICATION`, `BOTH` |
| `companion_preference` | `AI_DOC`, `PERSONAL_DOCTOR`, `BOTH`, `NONE` |
| `personal_doctor_request_status` | `ASSIGNED`, `PENDING`, `REJECTED` *(read-only — set by server/admin)* |
| `consent_type` | `ASK_EVERYTIME`, `AUTO_SHARE`, `FACILITY_AUTO_SHARE` *(read-only — set by server)* |
