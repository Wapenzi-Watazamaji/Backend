# Facility Admin API Reference (Web Dashboard)

**Base path:** `/api/v1/facility-admin`
All endpoints are scoped to the facility identified in the `X-Facility-Context` header. Only users with the `FACILITY_ADMIN` role can access these endpoints unless otherwise specified.

> Staff-roster CRUD (list/update a specific staff member, bulk-assign by `Profile.id`) lives in [`docs/web/facilities.md`](./facilities.md). This doc covers admin dashboard KPIs, the patient directory, and staff *management* actions (invite/capacity/deactivate) that are specific to the `/facility-admin` namespace.

---

## Authentication & Required Headers

| Header | Type | Required | Description |
|---|---|---|---|
| `Authorization` | `Bearer <access_token>` | ✅ Yes | JWT access token from `POST /auth/login` — see `docs/shared/auth.md` |
| `X-Facility-Context` | `UUID` | ✅ Yes | The UUID of the facility being administered. The user must be an active staff member at this facility. |

### Allowed Roles
- `FACILITY_ADMIN` — required for all endpoints unless noted

---

## Endpoints

### 1. `GET /overview`
**Get facility admin dashboard overview**

Returns high-level KPIs for the facility admin dashboard.

**Role required:** `FACILITY_ADMIN`

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "totalPatients": 120,
    "patientsDeltaThisWeek": 8,
    "unassignedPatientsCount": 15,
    "activeCliniciansCount": 6,
    "facilityWideAlertsCount": 12,
    "thisWeekAtAGlance": {
      "ancVisitsCompleted": 34,
      "ancVisitsScheduled": 42,
      "deliveries": 3,
      "referralsAccepted": 5,
      "referralsSentOut": 2,
      "postnatalFollowUpsDue": 9
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `totalPatients` | `int` | All patients with `preferred_facility_id` matching this facility |
| `patientsDeltaThisWeek` | `int` | New patients registered in the last 7 days |
| `unassignedPatientsCount` | `int` | Patients with no `personal_doctor_id` set |
| `activeCliniciansCount` | `int` | Clinicians with role `CLINICIAN` at this facility |
| `facilityWideAlertsCount` | `int` | Total unacknowledged alerts across the whole facility |

---

### 2. `GET /patients`
**Get facility-wide patient directory**

Returns all patients registered at this facility. Supports search and tab-based filtering. Includes the assigned clinician's name for each patient.

**Role required:** `FACILITY_ADMIN`

**Query Parameters**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `string` | No | — | Search by full name (case-insensitive, partial match) |
| `tab` | `string` | No | All patients | Filter tab — see values below |

**`tab` values:** *(omitted)* all · `unassigned` · `pregnant` · `postpartum` · `cycle_tracking` · `high_risk`

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "fullName": "Wanjiru Kamau",
      "age": 24,
      "patientCode": "A1B2C3",
      "phoneNumber": "+254712345678",
      "stage": "PREGNANT",
      "stageDetail": "",
      "riskLevel": "MEDIUM",
      "assignedClinicianName": "Dr. Achieng Otieno",
      "lastActivityAt": "2026-07-08T12:00:00Z",
      "preferredFacilityName": "Kilifi County Hospital"
    }
  ]
}
```

`riskLevel`: `LOW`\|`MEDIUM`\|`HIGH`. `stage`: `PREGNANT`\|`POSTPARTUM`\|`CYCLE_TRACKING`\|`UNKNOWN`.

---

### 3. `GET /unassigned-patients`
**List patients with no assigned clinician**

**Role required:** `FACILITY_ADMIN`

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "patientUserId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "fullName": "Carol Wambui",
      "stage": "PREGNANT",
      "stageDetail": "Awaiting assessment",
      "registeredAt": "2026-07-05T08:00:00Z",
      "isReferralFromOtherFacility": false,
      "referralFromFacilityName": null
    }
  ]
}
```

---

### 4. `POST /bulk-reassign`
**Bulk reassign patients to a clinician**

**Role required:** `FACILITY_ADMIN`

**Request Body**
```json
{
  "patientUserIds": ["3fa85f64-5717-4562-b3fc-2c963f66afa6", "6ba7b810-9dad-11d1-80b4-00c04fd430c8"],
  "clinicianId": "9f14d8a2-3c3b-4d70-91a5-3e1a2b3c4d5e"
}
```

**Response `200 OK`**
```json
{ "success": true, "data": { "status": "success", "reassignedCount": 2 } }
```

---

### 5. `POST /enroll-patient`
**Manually enroll a patient via SMS account**

Creates a new patient user with a minimal SMS-only account and links them to the facility. Prefer this over the public `POST /auth/register-sms-only` when enrolling from the dashboard, since this one also attaches the patient to the calling facility.

**Role required:** `CLINICIAN` or `FACILITY_ADMIN`

**Request Body**
```json
{
  "phone_number": "+254712345678",
  "role": "USER",
  "full_name": "Grace Njeri",
  "date_of_birth": "1999-03-15",
  "gender": "FEMALE",
  "preferred_language": "sw",
  "county": "Kilifi"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | `string` | ✅ | Patient's phone number (unique) |
| `role` | enum | ✅ | Always `USER` for a patient |
| `full_name` | `string` | ✅ | |
| `date_of_birth` | `date` | No | Format: YYYY-MM-DD |
| `gender` | enum | No | `MALE` \| `FEMALE` |
| `preferred_language` | `string` | No | Default: `"en"` |
| `county` | `string` | No | |

**Response `201 Created`**
```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "phone_number": "+254712345678",
    "full_name": "Grace Njeri",
    "role": "USER",
    "is_active": true,
    "created_at": "2026-07-08T10:00:00Z",
    "updated_at": "2026-07-08T10:00:00Z"
  }
}
```

---

### 6. `GET /clinician-workloads`
**List clinicians and their patient workloads**

**Role required:** `FACILITY_ADMIN`

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "clinicianId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "clinicianName": "Dr. Achieng Otieno",
      "specialty": "Obstetrics",
      "assignedPatientCount": 28,
      "maxCapacity": 40
    }
  ]
}
```

---

### 7. `GET /staff`
**List all facility staff**

**Role required:** `FACILITY_ADMIN`

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Dr. Achieng Otieno",
      "role": "CLINICIAN",
      "specialty": "Obstetrics",
      "assignedPatients": 28,
      "status": "Active",
      "email": null
    }
  ]
}
```

---

### 8. `POST /register-staff`
**Manually register a new staff member**

Creates an account and assigns it to the facility directly (not an email-invite flow — the account is created with a password immediately).

**Role required:** `FACILITY_ADMIN`

**Request Body**
```json
{
  "fullName": "Dr. Jane Doe",
  "phoneNumber": "+254711122233",
  "password": "SecurePassword123!",
  "role": "CLINICIAN",
  "specialty": "Midwifery"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `fullName` | `string` | ✅ | |
| `phoneNumber` | `string` | ✅ | |
| `password` | `string` | ✅ | Initial password |
| `role` | enum | ✅ | `CLINICIAN` \| `FACILITY_ADMIN` |
| `specialty` | `string` | No | Clinical specialty (for clinicians) |

**Response `200 OK`**
```json
{ "success": true, "data": { "status": "success", "message": "Staff member registered successfully." } }
```

---

### 9. `POST /staff/{staff_id}/resend-invite`
**Resend invite to a pending staff member**

Re-triggers an invite notification for a staff member with status `INVITE_PENDING`.

**Role required:** `FACILITY_ADMIN`

**Response `200 OK`**
```json
{ "success": true, "data": { "staffId": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "resentAt": "2026-07-10T08:45:00Z" } }
```

---

### 10. `PUT /staff/{staff_id}/capacity`
**Update a staff member's patient capacity cap**

Advisory soft limit — flags the admin's attention when a clinician is near/over capacity, does not block assignment.

**Role required:** `FACILITY_ADMIN`

**Request Body**
```json
{ "capacity": 35 }
```

**Response `200 OK`**
```json
{ "success": true, "data": { "staffId": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "capacity": 35 } }
```

---

### 11. `PUT /staff/{staff_id}/deactivate`
**Deactivate a staff member**

Sets status to `DEACTIVATED`, revoking login access. Historical records (vitals logged, feedback given) are preserved. Reassign their existing patients first via endpoint 12 below.

**Role required:** `FACILITY_ADMIN`

**Response `200 OK`**
```json
{ "success": true, "data": { "staffId": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "status": "DEACTIVATED" } }
```

---

### 12. `PUT /patients/{patient_user_id}/assign-clinician`
**Assign a single patient to a clinician**

Sets `personal_doctor_id` on a patient's profile. Use `POST /bulk-reassign` (endpoint 4) to assign multiple patients at once.

**Role required:** `FACILITY_ADMIN`

**Request Body**
```json
{ "clinicianId": "3fa85f64-5717-4562-b3fc-2c963f66afa6" }
```

**Response `200 OK`**
```json
{ "success": true, "data": { "patientUserId": "...", "assignedClinicianId": "..." } }
```

---

## Standard Error Responses

| Status | Meaning |
|---|---|
| `401` | Missing, expired, or invalid Bearer token |
| `403` | Missing `X-Facility-Context`, user not a staff member at the facility, or insufficient role (`FACILITY_ADMIN` required) |
| `400` | Malformed request body or query parameter |
| `404` | Resource not found |
