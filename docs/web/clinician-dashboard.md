# Clinician Dashboard API Reference (Web Dashboard)

**Base path:** `/api/v1/dashboard`
All endpoints are scoped to the authenticated clinician. Data returned is **strictly limited to patients whose `personal_doctor_id` matches the authenticated clinician's ID** — unless otherwise noted (see `GET /directory`).

---

## Authentication & Required Headers

| Header | Type | Required | Description |
|---|---|---|---|
| `Authorization` | `Bearer <access_token>` | ✅ Yes | JWT access token from `POST /auth/login` — see `docs/shared/auth.md` |
| `X-Facility-Context` | `UUID` | ✅ Yes | The UUID of the facility the clinician is operating under. Must be a facility where the user is an active staff member. |

### Allowed Roles
- `CLINICIAN`
- `FACILITY_ADMIN`

---

## Endpoints

### 1. `GET /summary`
**Get dashboard summary stats**

Returns high-level KPIs for the clinician's dashboard, all computed only for the authenticated clinician's assigned patients.

**Query Parameters:** `target_date` (date, default today) — reference date for computing daily metrics

**Response `200 OK`**
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

| Field | Description |
|---|---|
| `assignedPatientCount` | Total patients assigned to this clinician |
| `assignedPatientCountDeltaThisWeek` | New patients assigned in the last 7 days |
| `activeAlertCount` | Sum of unacknowledged labour alerts, high-risk postpartum screenings, and missed ANC visits — this clinician's patients only |
| `ancVisitsToday` | Scheduled ANC visits for today (`SCHEDULED`) |
| `ancVisitsCompletedToday` | ANC visits marked `COMPLETED` today |
| `pendingReferralCount` | Pending referrals to this facility for this clinician's patients |

---

### 2. `GET /alerts`
**Get unified alerts feed**

Merged, time-sorted list of all active alerts (labour, postpartum, missed ANC visits) for the clinician's patients only. Max 50 alerts, sorted by `createdAt` descending.

**Response `200 OK`**
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

`type`: `LABOUR`\|`POSTPARTUM`\|`MISSED_VISIT`. `severity`: `CRITICAL`\|`WARNING`\|`INFO`. `acknowledgedAt: null` means still active.

---

### 3. `PUT /alerts/{alert_id}/acknowledge`
**Acknowledge a specific alert**

Marks a labour alert as acknowledged, stamping `acknowledgedAt`. Once acknowledged it drops out of the active feed above.

**Response `200 OK`**
```json
{ "success": true, "data": { "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "acknowledgedAt": "2026-07-10T08:30:00Z" } }
```

---

### 4. `GET /directory`
**Facility-wide patient search**

Searches **all patients** registered at the clinician's facility (not just their own) — the "Find a Patient" view.

**Query Parameters:** `search` (string), `tab` (see values below)

**`tab` values:** *(omitted)* all · `assigned` · `unassigned` · `pregnant` · `postpartum` · `cycle_tracking` · `high_risk`

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

---

### 5. `GET /patients`
**Get the authenticated clinician's assigned patients only**

Same `PatientDirectoryItem` shape as `/directory`, but always filtered to `personal_doctor_id == caller` at the database level — no query parameter bypasses this.

**Query Parameters:** `search` (string), `tab` (`pregnant`\|`postpartum`\|`cycle_tracking`\|`high_risk`, omitted = all assigned)

---

### 6. `GET /timeline`
**Get clinician's activity timeline**

Chronological list of recent clinical events for the clinician's patients (completed ANC visits, referrals, labour sessions).

**Response `200 OK`**
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

`type`: `ANC_VISIT`\|`REFERRAL`\|`LABOUR`.

---

### 7. `GET /anc-visits-today`
**Get today's ANC visit schedule**

**Query Parameters:** `target_date` (date, default today)

**Response `200 OK`**
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

`status`: `SCHEDULED`\|`COMPLETED`\|`MISSED`\|`CANCELLED`.

---

### 8. `GET /patients/{patient_user_id}/overview`
**Get a single patient's overview**

Identity, active pregnancy summary (if pregnant), care team, and emergency contact — powers the patient detail sidebar.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "patient": {
      "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "fullName": "Wanjiru Kamau",
      "phoneNumber": "+254712345678",
      "dateOfBirth": "2001-03-14",
      "stage": "PREGNANT"
    },
    "pregnancySummary": {
      "dueDate": "2026-08-27",
      "gestationalAge": "31 weeks, 2 days",
      "ancVisitsCompleted": 6,
      "ancVisitsTotal": 8,
      "lastBloodPressure": "122/80",
      "lastWeightKg": 68.4
    },
    "careTeam": [
      { "userId": "...", "fullName": "Dr. Achieng Otieno", "role": "Assigned clinician" }
    ],
    "emergencyContact": {
      "name": "James Kamau",
      "relationship": "Husband",
      "phoneNumber": "+254721556002"
    }
  }
}
```

`pregnancySummary` is `null` if the patient is not currently pregnant.

---

### 9. `GET /patients/{patient_user_id}/timeline`
**Get a patient's cross-module timeline**

Merged, time-sorted feed of all clinical events for a single patient: scheduled visits, vitals submissions, and labour sessions.

**Query Parameters:** `filter` (`ALL`\|`VITALS`\|`VISITS`\|`FLAGS`, default `ALL`), `page` (default 1), `page_size` (default 20)

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "type": "FORM_SUBMISSION",
      "isFlagged": true,
      "title": "Vitals / Check-in submitted",
      "summary": "Patient submitted a Pregnancy Vitals form",
      "occurredAt": "2026-07-09T08:10:00Z",
      "sourceId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "actions": ["RESPOND"]
    }
  ]
}
```

`type`: `FORM_SUBMISSION`\|`SCHEDULED_VISIT`\|`LABOUR_EVENT`.

---

### 10. `GET /patients/{patient_user_id}/pregnancy-vitals`
**Get a patient's pregnancy vitals (clinician read view)**

All pregnancy vitals/maternal check-in submissions for a patient, including flagging status and feedback count.

**Query Parameters:** `filter` (`ALL`\|`FLAGGED`\|`VITALS_ONLY`\|`SYMPTOMS_ONLY`), `page`, `page_size`

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "submissionId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "submittedAt": "2026-07-09T08:10:00Z",
      "answers": { "systolicBP": 135, "diastolicBP": 90, "weightKg": 70.2 },
      "isFlagged": true,
      "flaggedReasons": ["Elevated blood pressure"],
      "feedbackCount": 1
    }
  ]
}
```

---

## Standard Error Responses

| Status | Meaning |
|---|---|
| `401` | Missing, expired, or invalid Bearer token |
| `403` | Missing `X-Facility-Context`, user not a staff member at the facility, or insufficient role |
| `400` | Malformed request body or query parameter |
| `404` | Resource not found |
