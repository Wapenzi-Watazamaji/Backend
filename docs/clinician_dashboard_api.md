# Clinician Dashboard API Reference

All endpoints are scoped to the authenticated clinician. Data returned is **strictly limited to patients whose `personal_doctor_id` matches the authenticated clinician's ID** — unless otherwise noted (see `/directory`).

---

## Authentication & Required Headers

Every endpoint requires the following headers:

| Header | Type | Required | Description |
|---|---|---|---|
| `Authorization` | `Bearer <access_token>` | ✅ Yes | JWT access token from `/api/auth/login` |
| `X-Facility-Context` | `UUID` | ✅ Yes | The UUID of the facility the clinician is operating under. Must be a facility where the user is an active staff member. |

### Allowed Roles
- `CLINICIAN`
- `FACILITY_ADMIN`

---

## Base URL
```
/api/dashboard
```

---

## Endpoints

---

### 1. `GET /dashboard/summary`
**Get dashboard summary stats**

Returns high-level KPIs for the clinician's dashboard, all computed only for the authenticated clinician's assigned patients.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `target_date` | `date` (YYYY-MM-DD) | No | Today | The reference date for computing daily metrics |

#### Response Body `200 OK`
```json
{
  "success": true,
  "data": {
    "assignedPatientCount": 28,
    "assignedPatientCountDeltaThisWeek": 3,
    "activeAlertCount": 5,
    "ancVisitsToday": 4,
    "ancVisitsCompletedToday": 1,
    "pendingReferralCount": 2
  }
}
```

| Field | Type | Description |
|---|---|---|
| `assignedPatientCount` | `int` | Total patients assigned to this clinician |
| `assignedPatientCountDeltaThisWeek` | `int` | New patients assigned in the last 7 days |
| `activeAlertCount` | `int` | Sum of unacknowledged labour alerts, high-risk postpartum screenings, and missed ANC visits — for this clinician's patients only |
| `ancVisitsToday` | `int` | Scheduled ANC visits for today (status: SCHEDULED) |
| `ancVisitsCompletedToday` | `int` | ANC visits marked COMPLETED today |
| `pendingReferralCount` | `int` | Pending referrals to this facility for this clinician's patients |

---

### 2. `GET /dashboard/alerts`
**Get unified alerts feed**

Returns a merged, time-sorted list of all active alerts (labour, postpartum, missed ANC visits) for the clinician's patients only.

#### No Query Parameters

#### Response Body `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "patientUserId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "patientName": "Wanjiru Kamau",
      "type": "LABOUR",
      "severity": "CRITICAL",
      "message": "Prolonged second stage detected",
      "sourceSubmissionId": null,
      "createdAt": "2026-07-08T14:00:00Z",
      "acknowledgedAt": null
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | One of: `LABOUR`, `POSTPARTUM`, `MISSED_VISIT` |
| `severity` | `string` | One of: `CRITICAL`, `WARNING`, `INFO` |
| `acknowledgedAt` | `datetime \| null` | If `null`, the alert is still active |

> **Note:** Maximum of 50 alerts returned, sorted by `createdAt` descending.

---

### 3. `GET /dashboard/directory`
**Facility-wide patient search**

Searches **all patients** registered at the clinician's facility (not just their own). This is the "Find a Patient" view. Use the `tab` parameter to narrow results.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `string` | No | — | Search by full name (case-insensitive, partial match) |
| `tab` | `string` | No | All patients | Filter tab. See values below. |

**`tab` values:**
| Value | Description |
|---|---|
| *(omitted)* | All patients at the facility |
| `assigned` | Only patients assigned to the authenticated clinician |
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
| `assignedClinicianName` | `string \| null` | Name of assigned clinician, or `null` if unassigned |

---

### 4. `GET /dashboard/patients`
**Get the authenticated clinician's assigned patients only**

Returns only patients whose `personal_doctor_id` equals the authenticated clinician's ID. **This filter is always enforced at the database level — no query parameter can bypass it.**

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `string` | No | — | Search by full name (case-insensitive, partial match) |
| `tab` | `string` | No | All assigned | Stage-based filter. See values below. |

**`tab` values:**
| Value | Description |
|---|---|
| *(omitted)* | All assigned patients |
| `pregnant` | Assigned patients in the PREGNANT stage |
| `postpartum` | Assigned patients in the POSTPARTUM stage |
| `cycle_tracking` | Assigned patients in the CYCLE_TRACKING stage |
| `high_risk` | Assigned patients with a HIGH active pregnancy risk score |

#### Response Body `200 OK`
Same `PatientDirectoryItem` schema as `/dashboard/directory`.

---

### 5. `GET /dashboard/timeline`
**Get clinician's activity timeline**

Returns a chronological list of recent clinical events for the clinician's patients (completed ANC visits, referrals, labour sessions).

#### No Query Parameters

#### Response Body `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "type": "ANC_VISIT",
      "isFlagged": false,
      "title": "ANC Visit Completed for Wanjiru Kamau",
      "summary": "Routine visit completed",
      "occurredAt": "2026-07-08T09:30:00Z",
      "sourceId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "actions": []
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | One of: `ANC_VISIT`, `REFERRAL`, `LABOUR` |
| `isFlagged` | `bool` | Whether the event is flagged for attention |
| `sourceId` | `string` | UUID of the underlying record (visit / referral / session) |
| `actions` | `list[string]` | Optional action labels for the UI |

---

### 6. `GET /dashboard/anc-visits-today`
**Get today's ANC visit schedule**

Returns the ANC visits scheduled for today for the clinician's assigned patients, ordered by scheduled time.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `target_date` | `date` (YYYY-MM-DD) | No | Today | Override the target date |

#### Response Body `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "scheduledVisitId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "patientName": "Naomi Mutua",
      "scheduledAt": "2026-07-08T10:00:00Z",
      "purpose": "Routine ANC Check",
      "status": "SCHEDULED"
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `status` | `string` | One of: `SCHEDULED`, `COMPLETED`, `MISSED`, `CANCELLED` |
| `purpose` | `string \| null` | The visit label or purpose |

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
| `403` | Missing `X-Facility-Context`, user not a staff member at the facility, or insufficient role |
| `400` | Malformed request body or query parameter |
| `404` | Resource not found |
