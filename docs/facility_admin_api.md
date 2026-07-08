# Facility Admin API Reference

All endpoints are scoped to the facility identified in the `X-Facility-Context` header. Only users with the `FACILITY_ADMIN` role can access these endpoints unless otherwise specified.

---

## Authentication & Required Headers

| Header | Type | Required | Description |
|---|---|---|---|
| `Authorization` | `Bearer <access_token>` | ✅ Yes | JWT access token from `/api/auth/login` |
| `X-Facility-Context` | `UUID` | ✅ Yes | The UUID of the facility being administered. The user must be an active staff member at this facility. |

### Allowed Roles
- `FACILITY_ADMIN` — required for all endpoints unless noted

---

## Base URL
```
/api/facility-admin
```

---

## Endpoints

---

### 1. `GET /facility-admin/overview`
**Get facility admin dashboard overview**

Returns high-level KPIs for the facility admin dashboard.

**Role required:** `FACILITY_ADMIN`

#### No Query Parameters

#### Response Body `200 OK`
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

### 2. `GET /facility-admin/patients`
**Get facility-wide patient directory**

Returns all patients registered at this facility. Supports search and tab-based filtering. Includes the assigned clinician's name for each patient.

**Role required:** `FACILITY_ADMIN`

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `string` | No | — | Search by full name (case-insensitive, partial match) |
| `tab` | `string` | No | All patients | Filter tab. See values below. |

**`tab` values:**
| Value | Description |
|---|---|
| *(omitted)* | All patients at the facility |
| `unassigned` | Patients with no assigned clinician |
| `pregnant` | Patients in the PREGNANT stage |
| `postpartum` | Patients in the POSTPARTUM stage |
| `cycle_tracking` | Patients in the CYCLE_TRACKING stage |
| `high_risk` | Patients with a HIGH active pregnancy risk score |

#### Response Body `200 OK`
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

| Field | Type | Description |
|---|---|---|
| `riskLevel` | `string` | One of: `LOW`, `MEDIUM`, `HIGH` |
| `stage` | `string` | One of: `PREGNANT`, `POSTPARTUM`, `CYCLE_TRACKING`, `UNKNOWN` |
| `assignedClinicianName` | `string` | Name of assigned clinician, or `"Unassigned"` if none |

---

### 3. `GET /facility-admin/unassigned-patients`
**List patients with no assigned clinician**

Returns patients at this facility who have not yet been assigned a personal doctor (`personal_doctor_id` is null).

**Role required:** `FACILITY_ADMIN`

#### No Query Parameters

#### Response Body `200 OK`
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

### 4. `POST /facility-admin/bulk-reassign`
**Bulk reassign patients to a clinician**

Reassigns a list of patients to a specified clinician in a single operation.

**Role required:** `FACILITY_ADMIN`

#### Request Body
```json
{
  "patientUserIds": [
    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ],
  "clinicianId": "9f14d8a2-3c3b-4d70-91a5-3e1a2b3c4d5e"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `patientUserIds` | `list[UUID]` | ✅ Yes | List of patient user IDs to reassign |
| `clinicianId` | `UUID` | ✅ Yes | The clinician to assign these patients to |

#### Response Body `200 OK`
```json
{
  "success": true,
  "data": {
    "status": "success",
    "reassignedCount": 2
  }
}
```

---

### 5. `POST /facility-admin/enroll-patient`
**Manually enroll a patient via SMS account**

Creates a new patient user with a minimal SMS-only account and links them to the facility.

**Role required:** `CLINICIAN` or `FACILITY_ADMIN`

#### Request Body
```json
{
  "phone_number": "+254712345678",
  "role": "MOTHER",
  "full_name": "Grace Njeri",
  "date_of_birth": "1999-03-15",
  "gender": "FEMALE",
  "preferred_language": "sw",
  "county": "Kilifi"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | `string` | ✅ Yes | Patient's phone number (unique) |
| `role` | `string` | ✅ Yes | Must be `MOTHER` |
| `full_name` | `string` | ✅ Yes | Patient's full name |
| `date_of_birth` | `date` | No | Format: YYYY-MM-DD |
| `gender` | `string` | No | One of: `MALE`, `FEMALE`, `OTHER` |
| `preferred_language` | `string` | No | Default: `"en"` |
| `county` | `string` | No | Patient's county |

#### Response Body `201 Created`
```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "phone_number": "+254712345678",
    "full_name": "Grace Njeri",
    "role": "MOTHER",
    "is_active": true,
    "created_at": "2026-07-08T10:00:00Z",
    "updated_at": "2026-07-08T10:00:00Z"
  }
}
```

---

### 6. `GET /facility-admin/clinician-workloads`
**List clinicians and their patient workloads**

Returns all clinicians and their current assigned patient count.

**Role required:** `FACILITY_ADMIN`

#### No Query Parameters

#### Response Body `200 OK`
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

| Field | Type | Description |
|---|---|---|
| `assignedPatientCount` | `int` | Number of patients currently assigned to this clinician |
| `maxCapacity` | `int` | Configured max patient capacity for this clinician |

---

### 7. `GET /facility-admin/staff`
**List all facility staff**

Returns all users with role `CLINICIAN` or `FACILITY_ADMIN` at this facility.

**Role required:** `FACILITY_ADMIN`

#### No Query Parameters

#### Response Body `200 OK`
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

### 8. `POST /facility-admin/invite-staff`
**Invite a new staff member**

Sends an invitation to a new staff member to join the facility.

**Role required:** `FACILITY_ADMIN`

#### Request Body
```json
{
  "email": "doctor.jane@example.com",
  "role": "CLINICIAN",
  "specialty": "Midwifery"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | `string` | ✅ Yes | Email address to send the invitation to |
| `role` | `string` | ✅ Yes | One of: `CLINICIAN`, `FACILITY_ADMIN` |
| `specialty` | `string` | No | Clinical specialty (for clinicians) |

#### Response Body `200 OK`
```json
{
  "success": true,
  "data": {
    "status": "success",
    "message": "Invited doctor.jane@example.com successfully."
  }
}
```

---

## Standard Error Responses

All endpoints return a consistent error shape:

```json
{
  "success": false,
  "message": "Error description here",
  "data": null
}
```

| Status | Meaning |
|---|---|
| `401` | Missing, expired, or invalid Bearer token |
| `403` | Missing `X-Facility-Context`, user not a staff member at the facility, or insufficient role (`FACILITY_ADMIN` required) |
| `400` | Malformed request body or query parameter |
| `404` | Resource not found |
