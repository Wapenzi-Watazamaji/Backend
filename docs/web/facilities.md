# Facilities Module — API Reference (Web Dashboard)

**Base path:** `/api/v1/facilities`
**Authentication:** Varies per endpoint — see the legend below each heading.

- 🔒 Requires `Authorization: Bearer <access_token>`
- 🔑 Requires a specific user role
- 🏢 Requires header `X-Facility-Context: <facility_id>` (the UUID of a facility the caller is an **active** staff member of)

> Public facility browsing/search (`GET /`, `GET /{facility_id}`, `GET /nearby`) is documented in [`docs/mobile/facilities.md`](../mobile/facilities.md) instead — those endpoints work identically for staff callers if you need them, they're just primarily a mobile feature.

---

## POST `/register`

Public endpoint for facilities to register themselves on the platform. This is an atomic operation that:
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
    "readiness": { "bloodBankStocked": true, "maternityBedsAvailable": 12 }
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

## GET `/current`

Retrieve the details of the facility currently set in context.

**Authentication:** 🔒 · 🏢

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

Update the current facility's details or readiness metrics.

**Authentication:** 🔒 · 🔑 `FACILITY_ADMIN` · 🏢

**Request Body** (all fields optional — only send what you want to change)
```json
{
  "email": "new.email@nairobihospital.org",
  "services_offered": ["ANTENATAL_CARE", "DELIVERY", "NEONATAL_ICU"],
  "readiness": { "bloodBankStocked": true, "maternityBedsAvailable": 12 }
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
| `readiness` | object | ❌ | Replaces the full object — this is what powers the mobile "time to nearest care" / facility readiness display |

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

Aggregate counts for the current facility's dashboard: staff headcount, on-duty staff, total assigned patients, and pending emergencies.

**Authentication:** 🔒 · 🔑 `FACILITY_ADMIN` · 🏢

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

List all staff members at the facility.

**Authentication:** 🔒 · 🔑 `FACILITY_ADMIN` · 🏢

**Response `200 OK`** — Array of `StaffMemberRead` objects (see shape below).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `403` | `FORBIDDEN` | Caller is not a `FACILITY_ADMIN`, or `X-Facility-Context` is missing/invalid/not a membership |

---

## GET `/staff/{staff_id}`

Get details for a specific staff member.

**Authentication:** 🔒 · 🔑 `FACILITY_ADMIN` · 🏢

**Response `200 OK`** — `StaffMemberRead` object.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | `staff_id` does not exist, or belongs to a different facility than the one in context |

---

## PUT `/staff/{staff_id}`

Update details for a specific staff member (e.g. changing their role, specialty, or duty/active status).

**Authentication:** 🔒 · 🔑 `FACILITY_ADMIN` · 🏢

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

**Response `200 OK`** — Updated `StaffMemberRead` object.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | `staff_id` does not exist, or belongs to a different facility than the one in context |
| `422` | `VALIDATION_ERROR` | Invalid enum value |

---

## POST `/staff/{staff_id}/assign-patients`

Bulk-assign an array of patient profiles to a specific clinician/staff member. Automatically decrements the patients from their previous doctors (if any), assigns them to the new doctor, and updates the new doctor's `assigned_patient_count` in real time. Also sets each patient's `personal_doctor_request_status` to `ASSIGNED`.

**Authentication:** 🔒 · 🔑 `FACILITY_ADMIN` · 🏢

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

**Response `200 OK`** — The updated `StaffMemberRead` object for the target clinician.

> There is also a simpler user-ID-based bulk-assign endpoint: `POST /facility-admin/bulk-reassign` — see `docs/web/facility-admin.md`. Prefer that one unless you specifically have `Profile.id` values on hand.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | `staff_id` does not exist, or belongs to a different facility than the one in context |
| `422` | `VALIDATION_ERROR` | `patient_profile_ids` missing or contains a non-UUID value |

---

## GET `/staff/{staff_id}/patients`

List all patient profiles currently assigned to the given staff member as their personal doctor.

**Authentication:** 🔒 · 🔑 `FACILITY_ADMIN` · 🏢

**Response `200 OK`** — Array of `ProfileRead` objects.

---

## GET `/clinician/my-patients`

List all patient profiles currently assigned to the **authenticated caller** at the given facility. Self-service equivalent of `GET /staff/{staff_id}/patients` — clinicians use this to fetch their own caseload without needing their own `staff_id`.

**Authentication:** 🔒 · 🔑 `CLINICIAN` or `FACILITY_ADMIN` · 🏢

**Response `200 OK`** — Array of `ProfileRead` objects.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Caller has no staff record at the facility in context |

---

## GET `/qr/scan/{token}`

*(Path lives under `/api/v1/profile`, not `/api/v1/facilities` — grouped here because it's the facility-side half of the QR passport flow described in `docs/mobile/profile.md`.)*

Scans a mother's QR passport token and retrieves her base profile, medical history, and active pregnancy (if any) — used during walk-in/emergency lookups.

**Authentication:** None (Public) — any facility device can call this if it has the token, since the token itself is the credential.

**Path Parameters**

| Param | Type | Notes |
|---|---|---|
| `token` | string | The `qr_passport_token` value the mother's app fetched via `GET /profile/me/qr` |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "QR Passport verified",
  "data": {
    "user": { "...": "UserRead shape" },
    "profile": { "...": "ProfileRead shape" },
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
| `medical_history` | object \| null | `null` if no medical history record exists — see `docs/web/medical-history.md` |
| `active_pregnancy` | object \| null | `null` if the mother has no active pregnancy — see `docs/web/pregnancy-clinical.md` |

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Token does not match any profile (invalid, or was invalidated by a refresh) |

---

## `StaffMemberRead` Shape

Returned by `GET /staff`, `GET /staff/{staff_id}`, `PUT /staff/{staff_id}`, and `POST /staff/{staff_id}/assign-patients`.

> Staff members are **created** via `POST /facility-admin/register-staff`, documented in `docs/web/facility-admin.md` — not in this module.

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

## Enum Reference

| Enum | Values |
|---|---|
| `facility.type` | `PUBLIC`, `PRIVATE`, `MISSION`, `NGO` |
| `facility.status` | `PENDING_VERIFICATION`, `VERIFIED`, `SUSPENDED` *(read-only — set by server/verification process)* |
| `staff.role` | `CLINICIAN`, `FACILITY_ADMIN` |
| `staff.status` | `ACTIVE`, `INVITE_PENDING`, `DEACTIVATED` |
