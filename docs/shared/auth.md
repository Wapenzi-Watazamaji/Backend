# Auth Module — API Reference

**Base path:** `/api/v1/auth`
**Used by:** both the mobile app (mother registration/login) and the web dashboard (clinician/facility-admin login) — this is the one module both frontends share, which is why it lives in `shared/` rather than `mobile/` or `web/`.
**Authentication:** All endpoints are public unless marked 🔒

---

## POST `/register`

Registers a new user with a password (full account). In practice this is used by the mobile app for mother self-registration. It technically accepts any `role`, but `CLINICIAN`/`FACILITY_ADMIN` accounts are normally provisioned instead via `POST /facilities/register` (self-service facility signup) or `POST /facility-admin/register-staff` (invited by an existing admin) — see `docs/web/facility-admin.md` and `docs/web/facilities.md`.

**Request Body**
```json
{
  "phone_number": "+254712345678",
  "full_name": "Wanjiru Kamau",
  "role": "USER",
  "password": "SecurePass123",
  "date_of_birth": "2000-03-14",
  "gender": "FEMALE",
  "preferred_language": "en",
  "county": "Kilifi",
  "profile_photo_url": null
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `phone_number` | string | ✅ | |
| `full_name` | string | ✅ | |
| `role` | enum | ✅ | `USER` \| `CLINICIAN` \| `FACILITY_ADMIN` |
| `password` | string | ✅ | |
| `date_of_birth` | date (YYYY-MM-DD) | ❌ | |
| `gender` | enum | ❌ | `MALE` \| `FEMALE` |
| `preferred_language` | string | ❌ | Default: `"en"` |
| `county` | string | ❌ | |
| `profile_photo_url` | string | ❌ | |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
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
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `409` | `PHONE_ALREADY_REGISTERED` | Phone number already in use |
| `422` | `VALIDATION_ERROR` | Missing required field or invalid enum value |

---

## POST `/register-sms-only`

Registers a patient without a smartphone (no password). Intended to be called on a patient's behalf by facility staff — though note this endpoint itself requires **no authentication or role** (it's public). The staff-scoped equivalent used by the web dashboard is `POST /facility-admin/enroll-patient` (see `docs/web/facility-admin.md`), which additionally links the patient to the calling facility. Prefer that one for the web dashboard's "enroll patient" flow.

**Request Body** — Same fields as `/register`, minus `password`.
```json
{
  "phone_number": "+254712345678",
  "full_name": "Amina Hassan",
  "role": "USER",
  "date_of_birth": "1998-06-20",
  "gender": "FEMALE",
  "county": "Mombasa"
}
```

**Response `201 Created`** — Same shape as `/register`.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `409` | `PHONE_ALREADY_REGISTERED` | Phone number already in use |
| `422` | `VALIDATION_ERROR` | Missing required field or invalid enum value |

---

## POST `/login`

Authenticates a user and returns access + refresh tokens. Used by both apps.

**Request Body**
```json
{
  "phone_number": "+254712345678",
  "password": "SecurePass123"
}
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "User logged in successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "staff_memberships": null
  },
  "meta": {}
}
```

| Field | Type | Notes |
|---|---|---|
| `access_token` | string | |
| `refresh_token` | string | |
| `token_type` | string | Always `"bearer"` |
| `user_id` | uuid | |
| `staff_memberships` | array \| null | **Web dashboard only.** Populated when `role` is `CLINICIAN` or `FACILITY_ADMIN`. `null` for `USER` (mother) accounts. See shape below. |

**`staff_memberships` item shape** (web dashboard)
```json
{
  "facility_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "facility_name": "Kilifi County Hospital",
  "role": "CLINICIAN",
  "status": "ACTIVE"
}
```

If the user has a staff invite in `INVITE_PENDING` status at the time of login, it is automatically flipped to `ACTIVE` (and `joined_at` is stamped) as part of this call. The web dashboard should use this array to render a facility selector and set `X-Facility-Context` on subsequent calls (see `docs/shared/conventions.md`).

**Token lifetimes**
- `access_token` — 7 days
- `refresh_token` — 30 days

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `INVALID_CREDENTIALS` | Wrong phone number or password |
| `401` | `UNAUTHORIZED` | Account is inactive |

---

## POST `/refresh`

Issues a new access token using a valid refresh token.

**Request Body**
```json
{ "refresh_token": "eyJhbGciOiJIUzI1NiIs..." }
```

**Response `200 OK`** — same shape as `/login`. Note: `staff_memberships` is always `null` on refresh (it is only computed during `/login`), even for clinician/facility-admin accounts — the web dashboard should cache it from the login response rather than expecting it here.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `INVALID_CREDENTIALS` | Token is invalid, expired, or not a refresh token |

---

## POST `/logout` 🔒

Logs out the current user. The client must discard both tokens on receipt of this response.

**Request Body**
```json
{ "refresh_token": "eyJhbGciOiJIUzI1NiIs..." }
```

**Response `204 No Content`**

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |

---

## GET `/me` 🔒

Returns the currently authenticated user's own `User` record (not the extended `Profile` — mobile clients should follow up with `GET /profile/me`, see `docs/mobile/profile.md`).

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
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
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token, or account inactive |

---

## GET `/me/landing-summary` 🔒 — Web dashboard only

Post-login landing summary — active alert count, active labour session count, and pending referral count. Meant for the web dashboard to populate its shell immediately after login; a mother's mobile session has no practical use for this endpoint.

**Headers**
```
Authorization: Bearer <access_token>
X-Facility-Context: <facility_id>   (optional)
```

If `X-Facility-Context` is provided and is a valid UUID, counts are scoped to that facility. If omitted or not a valid UUID, it is silently ignored and counts are unscoped.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "activeAlertCount": 3,
    "activeLabourSessionCount": 1,
    "pendingReferralCount": 2
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token, or account inactive |

---

## Enum Reference

| Enum | Values |
|---|---|
| `role` | `USER`, `CLINICIAN`, `FACILITY_ADMIN` |
| `gender` | `MALE`, `FEMALE` |
| `account_type` | `FULL`, `SMS_ONLY` *(set automatically by the server — not accepted in requests)* |
| `staff_memberships[].role` | `CLINICIAN`, `FACILITY_ADMIN` |
| `staff_memberships[].status` | `ACTIVE`, `INVITE_PENDING`, `DEACTIVATED` |

See `docs/shared/conventions.md` for the response envelope and standard error codes.
