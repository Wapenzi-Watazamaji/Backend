# Auth Module — API Reference

**Base path:** `/api/v1/auth`
**Authentication:** All endpoints are public unless marked 🔒

---

## POST `/register`

Registers a new user with a password (full account).

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

Registers a patient without a smartphone (no password). Used by facility admins to register patients who will only receive SMS notifications.

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

Authenticates a user and returns access + refresh tokens.

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
    "token_type": "bearer"
  },
  "meta": {}
}
```

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
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `INVALID_CREDENTIALS` | Token is invalid, expired, or not a refresh token |

---

## POST `/logout` 🔒

Logs out the current user. The client must discard both tokens on receipt of this response.

**Headers**
```
Authorization: Bearer <access_token>
```

**Request Body**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response `204 No Content`** — Empty body.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |

---

## GET `/me` 🔒

Returns the profile of the currently authenticated user.

**Headers**
```
Authorization: Bearer <access_token>
```

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
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `401` | `UNAUTHORIZED` | User account is inactive |

---

## Standard Error Response Shape

All errors follow this envelope:

```json
{
  "success": false,
  "data": null,
  "meta": null,
  "error": {
    "code": "PHONE_ALREADY_REGISTERED",
    "message": "Phone number is already registered",
    "fields": {
      "phoneNumber": "Already in use"
    }
  }
}
```

`fields` is only present on validation errors that map to specific request fields.

---

## Enum Reference

| Enum | Values |
|---|---|
| `role` | `USER`, `CLINICIAN`, `FACILITY_ADMIN` |
| `gender` | `MALE`, `FEMALE` |
| `account_type` | `FULL`, `SMS_ONLY` *(set automatically by the server — not accepted in requests)* |
