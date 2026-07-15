# Facilities Module — API Reference

**Base path:** `/api/v1/facilities`
**Authentication:** Varies per endpoint — see the legend below each heading.

- 🔒 Requires `Authorization: Bearer <access_token>`
- 🔑 Requires a specific user role
- 🏢 Requires header `X-Facility-Context: <facility_id>` (the UUID of a facility the caller is an **active** staff member of)

---

## POST `/register`

Public endpoint for facilities to register themselves on the Binti Care platform.
This is an atomic operation that:
1. Creates the `Facility` record (status: `PENDING_VERIFICATION`).
2. Creates an `AccountType.FULL` user with role `FACILITY_ADMIN`.
3. Links the user to the facility via a `StaffMember` record.
4. Logs the user in and returns auth tokens.

**Authentication:** None (Public)

**Request Body**
```json
{
  "facility": {
    "name": "Nairobi Hospital",
    "type": "PRIVATE",
    "county": "Nairobi",
    "address": "Argwings Kodhek Rd",
    "phone_number": "+254700000001",
    "email": "info@nairobihospital.org",
    "latitude": -1.2921,
    "longitude": 36.8219,
    "services_offered": ["ANTENATAL_CARE", "DELIVERY"],
    "readiness": {
      "bloodBankStocked": true,
      "maternityBedsAvailable": 12
    }
  },
  "admin_account": {
    "full_name": "Dr. Jane Doe",
    "phone_number": "+254712345678",
    "email": "jane.doe@nairobihospital.org",
    "password": "SecurePassword123!"
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `facility.name` | string | ✅ | |
| `facility.type` | enum | ✅ | `PUBLIC` \| `PRIVATE` \| `MISSION` \| `NGO` |
| `facility.county` | string | ✅ | |
| `facility.address` | string | ✅ | |
| `facility.phone_number` | string | ✅ | |
| `facility.email` | string | ❌ | Must be unique across facilities |
| `facility.latitude` | float | ❌ | Must be between `-90` and `90` |
| `facility.longitude` | float | ❌ | Must be between `-180` and `180` |
| `facility.services_offered` | string[] | ❌ | Default `[]` |
| `facility.readiness` | object | ❌ | Free-form key/value readiness metrics. Default `{}` |
| `admin_account.full_name` | string | ✅ | |
| `admin_account.phone_number` | string | ✅ | Must not already be registered |
| `admin_account.email` | string | ❌ | |
| `admin_account.password` | string | ✅ | |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Facility registered successfully",
  "data": {
    "facility": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Nairobi Hospital",
      "type": "PRIVATE",
      "county": "Nairobi",
      "address": "Argwings Kodhek Rd",
      "phone_number": "+254700000001",
      "email": "info@nairobihospital.org",
      "latitude": -1.2921,
      "longitude": 36.8219,
      "status": "PENDING_VERIFICATION",
      "is_active": true,
      "services_offered": ["ANTENATAL_CARE", "DELIVERY"],
      "readiness": { "bloodBankStocked": true, "maternityBedsAvailable": 12 },
      "updated_at": "2026-07-01T09:00:00Z"
    },
    "admin_user_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
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
| `400` | `VALIDATION_ERROR` | `facility.email` is already registered to another facility |
| `409` | `PHONE_ALREADY_REGISTERED` | `admin_account.phone_number` is already registered |
| `422` | `VALIDATION_ERROR` | Missing required field, invalid enum value, or `latitude`/`longitude` out of range |

---

## GET `/`

Fetch a list of all facilities.

**Authentication:** None (Public) or 🔒 `Authorization: Bearer <access_token>` depending on setup.

**Query Parameters**
| Parameter | Type | Required | Default | Notes |
|---|---|---|---|---|
| `search` | string | ❌ | | Optional search term to filter facilities by name |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Facilities fetched successfully",
  "data": [
    {
      "id": "fac-uuid",
      "name": "Nairobi Hospital",
      "type": "PRIVATE",
      "county": "Nairobi",
      "status": "VERIFIED",
      "is_active": true,
      "...": "..."
    }
  ],
  "meta": {}
}
```

---

## GET `/{facility_id}`

Retrieve the details of a specific facility by its UUID.

**Authentication:** None (Public) or 🔒 `Authorization: Bearer <access_token>` depending on setup.

**Path Parameters**
- `facility_id` (uuid): The ID of the facility to fetch.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Facility fetched successfully",
  "data": {
    "id": "fac-uuid",
    "name": "Nairobi Hospital",
    "type": "PRIVATE",
    "county": "Nairobi",
    "status": "VERIFIED",
    "is_active": true,
    "...": "..."
  },
  "meta": {}
}
```

---

## GET `/nearby`

Finds all active facilities within a specified radius, calculating straight-line distance using the Haversine formula based on the user's provided coordinates. The results are ordered by distance (closest first). Facilities without coordinates set are excluded.

**Authentication:** 🔒 `Authorization: Bearer <access_token>` (any role)

**Query Parameters**

| Parameter | Type | Required | Default | Notes |
|---|---|---|---|---|
| `lat` | float | ✅ | | Latitude of the patient/user |
| `lng` | float | ✅ | | Longitude of the patient/user |
| `radius_km` | float | ❌ | `50.0` | Maximum search radius in kilometers |
| `limit` | int | ❌ | `20` | Max number of results to return |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Nearby facilities fetched successfully",
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Nairobi Hospital",
      "type": "PRIVATE",
      "county": "Nairobi",
      "address": "Argwings Kodhek Rd",
      "phone_number": "+254700000001",
      "email": "info@nairobihospital.org",
      "latitude": -1.295,
      "longitude": 36.805,
      "status": "VERIFIED",
      "is_active": true,
      "services_offered": ["ANTENATAL_CARE", "DELIVERY"],
      "readiness": {},
      "updated_at": "2026-07-01T12:00:00Z",
      "distance_km": 2.45
    }
  ],
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `422` | `VALIDATION_ERROR` | `lat`/`lng` missing or not numeric |

---

## GET `/current`

Retrieve the details of the facility currently set in context. Intended for staff (clinicians/facility admins) viewing their own facility, not for `USER`-role mothers.

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Facility fetched successfully",
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Nairobi Hospital",
    "type": "PRIVATE",
    "county": "Nairobi",
    "address": "Argwings Kodhek Rd",
    "phone_number": "+254700000001",
    "email": "info@nairobihospital.org",
    "latitude": -1.295,
    "longitude": 36.805,
    "status": "VERIFIED",
    "is_active": true,
    "services_offered": ["ANTENATAL_CARE", "DELIVERY"],
    "readiness": {},
    "updated_at": "2026-07-01T12:00:00Z"
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | `X-Facility-Context` header is missing, not a valid UUID, or caller is not an active staff member of that facility |
| `404` | `NOT_FOUND` | Facility ID from the header does not exist |

---

## PUT `/current`

Update a facility's details or readiness metrics.

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body** (all fields optional — only send what you want to change)
```json
{
  "email": "new.email@nairobihospital.org",
  "services_offered": ["ANTENATAL_CARE", "DELIVERY", "NEONATAL_ICU"],
  "readiness": {
    "bloodBankStocked": true,
    "maternityBedsAvailable": 12
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | ❌ | |
| `county` | string | ❌ | |
| `address` | string | ❌ | |
| `phone_number` | string | ❌ | |
| `email` | string | ❌ | |
| `latitude` | float | ❌ | Must be between `-90` and `90` |
| `longitude` | float | ❌ | Must be between `-180` and `180` |
| `services_offered` | string[] | ❌ | Replaces the full list |
| `readiness` | object | ❌ | Replaces the full object |

Note: `type` and `status` cannot be changed via this endpoint.

**Response `200 OK`** — Updated `FacilityRead` object (same shape as `GET /current`).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |
| `404` | `NOT_FOUND` | Facility ID from the header does not exist |
| `422` | `VALIDATION_ERROR` | `latitude`/`longitude` out of range |

---

## GET `/current/stats`

Returns aggregate counts for the current facility's dashboard: staff headcount, on-duty staff, total assigned patients, and pending emergencies.

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Facility stats fetched successfully",
  "data": {
    "total_staff": 14,
    "staff_on_duty": 6,
    "total_assigned_patients": 132,
    "pending_emergencies": 2
  },
  "meta": {}
}
```

| Field | Type | Notes |
|---|---|---|
| `total_staff` | integer | All staff members at the facility, regardless of status |
| `staff_on_duty` | integer | Staff with `is_on_duty: true` |
| `total_assigned_patients` | integer | Sum of `assigned_patient_count` across all staff |
| `pending_emergencies` | integer | Emergency requests routed to this facility with status `PENDING` |

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |

---

## GET `/staff`

Get a list of all staff members at the facility.

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`** — Array of `StaffMemberRead` objects (see shape below).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |

---

## GET `/staff/{staff_id}`

Get details for a specific staff member.

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`** — `StaffMemberRead` object (see shape below).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |
| `404` | `NOT_FOUND` | `staff_id` does not exist, or belongs to a different facility than the one in context |

---

## PUT `/staff/{staff_id}`

Update details for a specific staff member (e.g. changing their role, specialty, or duty/active status).

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body** (all fields optional)
```json
{
  "role": "CLINICIAN",
  "specialty": "Pediatrics",
  "status": "DEACTIVATED",
  "is_on_duty": false
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | enum | ❌ | `CLINICIAN` \| `FACILITY_ADMIN` |
| `specialty` | string | ❌ | |
| `status` | enum | ❌ | `ACTIVE` \| `INVITE_PENDING` \| `DEACTIVATED` |
| `is_on_duty` | boolean | ❌ | |

**Response `200 OK`** — Updated `StaffMemberRead` object (see shape below).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |
| `404` | `NOT_FOUND` | `staff_id` does not exist, or belongs to a different facility than the one in context |
| `422` | `VALIDATION_ERROR` | Invalid enum value |

---

## POST `/staff/{staff_id}/assign-patients`

Bulk assign an array of patient profiles to a specific clinician/staff member. This automatically decrements the patients from their previous doctors (if any), assigns them to the new doctor, and updates the new doctor's `assigned_patient_count` in real-time. Also sets each patient's `personal_doctor_request_status` to `ASSIGNED`.

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body**
```json
{
  "patient_profile_ids": [
    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed"
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `patient_profile_ids` | UUID[] | ✅ | List of `Profile.id` values (not user IDs) |

**Response `200 OK`** — The updated `StaffMemberRead` object for the target clinician, reflecting their new `assigned_patient_count` load.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |
| `404` | `NOT_FOUND` | `staff_id` does not exist, or belongs to a different facility than the one in context |
| `422` | `VALIDATION_ERROR` | `patient_profile_ids` missing or contains a non-UUID value |

---

## GET `/staff/{staff_id}/patients`

List all patient profiles currently assigned to the given staff member as their personal doctor.

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`** — Array of `ProfileRead` objects (see `profile.md` for the shape).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |
| `404` | `NOT_FOUND` | `staff_id` does not exist, or belongs to a different facility than the one in context |

---

## GET `/clinician/my-patients`

List all patient profiles currently assigned to the **authenticated caller** (as personal doctor) at the given facility. Self-service equivalent of `GET /staff/{staff_id}/patients` — clinicians use this to fetch their own caseload without needing their own `staff_id`.

**Authentication:**
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `CLINICIAN` or `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`** — Array of `ProfileRead` objects (see `profile.md` for the shape).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `CLINICIAN`/`FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |
| `404` | `NOT_FOUND` | Caller has no staff record at the facility in context |

---

## `StaffMemberRead` Shape

Returned by `GET /staff`, `GET /staff/{staff_id}`, `PUT /staff/{staff_id}`, and `POST /staff/{staff_id}/assign-patients`.

> Staff members are **created** via `POST /api/v1/facility-admin/register-staff`, documented in `facility_admin_api.md` — not in this module.

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "facility_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
  "user_id": "9c8c092e-1234-4562-b3fc-2c963f66afa6",
  "role": "CLINICIAN",
  "specialty": "Pediatrics",
  "assigned_patient_count": 8,
  "status": "ACTIVE",
  "is_on_duty": true,
  "invited_at": "2026-06-01T09:00:00Z",
  "joined_at": "2026-06-02T10:15:00Z"
}
```

| Field | Type | Notes |
|---|---|---|
| `user_id` | UUID \| null | `null` if the invite hasn't been claimed by a user account yet |
| `role` | enum | `CLINICIAN` \| `FACILITY_ADMIN` |
| `status` | enum | `ACTIVE` \| `INVITE_PENDING` \| `DEACTIVATED` |
| `assigned_patient_count` | integer | Maintained automatically by the assignment endpoints |
| `joined_at` | datetime \| null | `null` until the staff member's status becomes `ACTIVE` |

---

## Note on Staff Logins

When a user with role `CLINICIAN` or `FACILITY_ADMIN` logs in via `POST /api/v1/auth/login`, the response token now includes their active `staff_memberships`:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "staff_memberships": [
    {
      "facility_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "facility_name": "Nairobi Hospital",
      "role": "FACILITY_ADMIN",
      "status": "ACTIVE"
    }
  ]
}
```
Frontends should use this array to display the facility selector, and set the `X-Facility-Context` header to the selected `facility_id` on subsequent API calls.

---

## Enum Reference

| Enum | Values |
|---|---|
| `facility.type` | `PUBLIC`, `PRIVATE`, `MISSION`, `NGO` |
| `facility.status` | `PENDING_VERIFICATION`, `VERIFIED`, `SUSPENDED` *(read-only — set by server/verification process)* |
| `staff.role` | `CLINICIAN`, `FACILITY_ADMIN` |
| `staff.status` | `ACTIVE`, `INVITE_PENDING`, `DEACTIVATED` |
