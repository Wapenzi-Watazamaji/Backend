# Facilities Module — API Reference

**Base path:** `/api/v1/facilities`

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

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Facility registered successfully",
  "data": {
    "facility": {
      "id": "fac-uuid",
      "name": "Nairobi Hospital",
      "type": "PRIVATE",
      "county": "Nairobi",
      "status": "PENDING_VERIFICATION",
      "is_active": true,
      "...": "..."
    },
    "admin_user_id": "user-uuid",
    "access_token": "jwt-token",
    "refresh_token": "jwt-token",
    "token_type": "bearer"
  },
  "meta": {}
}
```

**Errors**
- `400 Bad Request` if the admin's phone number is already registered.
- `422 Validation Error` if the facility email is already in use.

---

## GET `/nearby`

Finds all active facilities within a specified radius, calculating straight-line distance using the Haversine formula based on the user's provided coordinates. The results are ordered by distance (closest first).

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`

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

---

## GET `/current`

Retrieve the details of the facility currently set in context.

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

---

## PUT `/current`

Update a facility's details or readiness metrics.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body** (All fields optional)
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

**Response `200 OK`** — Updated `FacilityRead` object.

---

## POST `/staff`

Add a new staff member (CLINICIAN or FACILITY_ADMIN) to the facility.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body**
```json
{
  "phone_number": "+254711222333",
  "role": "CLINICIAN",
  "specialty": "Pediatrics"
}
```

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Staff member added successfully",
  "data": {
    "id": "staff-uuid",
    "facility_id": "fac-uuid",
    "user_id": "user-uuid",
    "role": "CLINICIAN",
    "specialty": "Pediatrics",
    "assigned_patient_count": 0,
    "status": "INVITE_PENDING",
    "invited_at": "2026-07-01T12:00:00Z",
    "joined_at": null
  },
  "meta": {}
}
```

*Note: If the user doesn't exist on the platform yet, `user_id` will be null and the frontend should inform the user that an SMS invite was sent.*

---

## GET `/staff`

Get a list of all staff members at the facility.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`** — Array of Staff objects (same shape as POST).

---

## GET `/staff/{staff_id}`

Get details for a specific staff member.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`** — Staff object (same shape as POST).

---

## PUT `/staff/{staff_id}`

Update details for a specific staff member (e.g. changing their role or suspending them).

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body**
```json
{
  "role": "FACILITY_ADMIN",
  "specialty": "Pediatrics",
  "status": "SUSPENDED"
}
```
*Note: All fields are optional. `status` can be `ACTIVE`, `SUSPENDED`, etc. `role` can be `CLINICIAN`, `FACILITY_ADMIN`, etc.*

**Response `200 OK`** — Updated Staff object (same shape as POST).

---

## POST `/staff/{staff_id}/assign-patients`

Bulk assign an array of patient profiles to a specific clinician/staff member. This automatically decrements the patients from their previous doctors (if any), assigns them to the new doctor, and updates the new doctor's `assigned_patient_count` in real-time.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body**
```json
{
  "patient_profile_ids": [
    "uuid-1",
    "uuid-2",
    "uuid-3"
  ]
}
```

**Response `200 OK`** — The updated Staff object for the target clinician, reflecting their new `assigned_patient_count` load.

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
      "facility_id": "fac-uuid",
      "facility_name": "Nairobi Hospital",
      "role": "FACILITY_ADMIN",
      "status": "ACTIVE"
    }
  ]
}
```
Frontends should use this array to display the facility selector, and set the `X-Facility-Context` header to the selected `facility_id` on subsequent API calls.
