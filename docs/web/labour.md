# Labour & Birth Monitor Module — API Reference (Web Dashboard)

**Base path:** `/api/v1/labour`
**Authentication:** All endpoints require a valid Bearer token 🔒. Endpoints that write to the database require a `CLINICIAN` role ⚕️; facility-wide feed endpoints require `FACILITY_ADMIN` where noted.

> The mother's simplified, read-only labour status view lives in [`docs/mobile/labour.md`](../mobile/labour.md).

---

## POST `/sessions` 🔒⚕️

Opens a new active labour session for a pregnant mother.

**Request Body**
```json
{
  "pregnancyId": "800eb70b-4e2a-45d5-8ddc-43e7127dcdb3",
  "facilityId": "b071e013-9e82-4143-bca1-2b15ac6498c9",
  "activeLabourStartedAt": "2026-07-03T08:00:00Z",
  "room": "Delivery Room 2"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `pregnancyId` | UUID | ✅ | ID of the active pregnancy record |
| `facilityId` | UUID | ✅ | Facility where the session is taking place |
| `activeLabourStartedAt` | datetime (ISO 8601) | ✅ | |
| `room` | string | ❌ | Room/bed assignment |

**Response `201 Created`** — `LabourSessionRead` object (see `GET /sessions/{session_id}` in the mobile doc for the base shape, plus `room`).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `403` | `FORBIDDEN` | Missing clinician role |
| `404` | `NOT_FOUND` | Associated pregnancy or facility not found |

---

## PUT `/sessions/{session_id}/close` 🔒⚕️

Closes a labour session after delivery or transfer.

**Request Body**
```json
{
  "closedAt": "2026-07-03T14:00:00Z",
  "outcome": "LIVE_BIRTH",
  "deliveryType": "VAGINAL"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `closedAt` | datetime (ISO 8601) | ✅ | |
| `outcome` | enum | ✅ | `LIVE_BIRTH` \| `STILLBIRTH` \| `REFERRED` \| `OTHER` |
| `deliveryType` | enum | ✅ | `VAGINAL` \| `C_SECTION` \| `ASSISTED` |

**Response `200 OK`** — Updated `LabourSessionRead` object, `status: "CLOSED"`.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Session is already closed |
| `403` | `FORBIDDEN` | Missing clinician role |
| `404` | `NOT_FOUND` | Labour session does not exist |

---

## PUT `/sessions/{session_id}/room`

Assigns/updates the room or bed for a labour session (facility-wide bed-management view).

**Role required:** `CLINICIAN`

**Request Body**
```json
{ "room": "Delivery Room 3" }
```

**Response `200 OK`**
```json
{ "success": true, "data": { "status": "success" } }
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Session not found |

---

## POST `/sessions/{session_id}/readings/dilation` 🔒⚕️

Logs a cervical dilation reading. Triggers partograph alert logic (action-line crossing).

**Request Body**
```json
{ "value": 4, "recordedAt": "2026-07-03T08:00:00Z" }
```

**Response `201 Created`**
```json
{
  "success": true,
  "data": {
    "id": "b2c3d4e5-f6a7-4ca5-903a-262ed44b06ac",
    "session_id": "7719e249-c628-4b33-9511-b6a0fdd75310",
    "type": "DILATION",
    "value": 4.0,
    "meta": null,
    "recorded_at": "2026-07-03T08:00:00Z",
    "created_at": "2026-07-03T08:00:00Z"
  }
}
```

---

## POST `/sessions/{session_id}/readings/fhr` 🔒⚕️

Logs a fetal heart rate (FHR) reading. Triggers a `FETAL_DISTRESS` alert if outside the normal range.

**Request Body**
```json
{ "value": 152, "recordedAt": "2026-07-03T08:00:00Z" }
```

---

## POST `/sessions/{session_id}/readings/maternal-vitals` 🔒⚕️

Logs maternal blood pressure. Triggers a `PREECLAMPSIA_RISK` alert if systolic ≥ 140.

**Request Body**
```json
{
  "bloodPressureSystolic": 124,
  "bloodPressureDiastolic": 82,
  "recordedAt": "2026-07-03T08:00:00Z"
}
```

---

## POST `/sessions/{session_id}/readings/contractions` 🔒⚕️

Logs a contraction reading.

**Request Body**
```json
{
  "frequencyPer10Min": 4,
  "durationSeconds": 50,
  "recordedAt": "2026-07-03T08:00:00Z"
}
```

---

## POST `/sessions/{session_id}/alerts/{alert_id}/acknowledge` 🔒⚕️

Marks a labour alert as acknowledged by the clinician.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "96ed30ff-c54c-477f-86f6-21daad1ed9b1",
    "session_id": "7719e249-c628-4b33-9511-b6a0fdd75310",
    "type": "ACTION_LINE_CROSSED",
    "severity": "CRITICAL",
    "message": "Labour progress is now 4 hours behind the expected rate",
    "acknowledged_at": "2026-07-03T14:38:45Z",
    "acknowledged_by": "f1571b88-0d48-4e88-800c-87bfa0249c81",
    "escalated_to": null,
    "created_at": "2026-07-03T13:00:00Z"
  }
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `403` | `FORBIDDEN` | Missing clinician role |
| `404` | `NOT_FOUND` | Alert does not exist or does not belong to session |

---

## POST `/sessions/{session_id}/alerts/{alert_id}/escalate` 🔒⚕️

Escalates an alert (e.g. to a referral flow).

**Request Body**
```json
{ "escalateTo": "SPECIALIST" }
```

**Response `200 OK`**
```json
{ "success": true, "data": { "referralId": null, "escalatedTo": "SPECIALIST" } }
```

---

## POST `/sessions/{session_id}/resuscitation-log` 🔒⚕️

Logs a completed resuscitation step during delivery (relative to the WHO protocol steps returned by `GET /resuscitation-protocol`).

**Request Body**
```json
{
  "stepOrder": 1,
  "completedAt": "2026-07-03T10:00:00Z",
  "vitalsAtStep": { "heartRateBpm": 90, "respiratoryEffort": "GASPING" }
}
```

**Response `201 Created`**
```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-4ca5-903a-262ed44b06ac",
    "session_id": "7719e249-c628-4b33-9511-b6a0fdd75310",
    "step_order": 1,
    "completed_at": "2026-07-03T10:00:00Z",
    "vitals_at_step": { "heartRateBpm": 90, "respiratoryEffort": "GASPING" },
    "created_at": "2026-07-03T10:00:00Z"
  }
}
```

---

## GET `/active` — Facility Admin

Lists every active labour session at the facility (bed-management/overview board).

**Role required:** `FACILITY_ADMIN` · 🏢

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "patientName": "string",
      "room": "string | null",
      "hoursInLabour": 0.0,
      "dilationCm": 0.0,
      "fhr": 0.0,
      "status": "string",
      "assignedClinicianName": "string"
    }
  ]
}
```

---

## GET `/alerts-summary`

Facility-wide summary of active labour sessions and their alerts.

**Role required:** `CLINICIAN` · 🏢

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "activeLabourCount": 0,
    "criticalAlertCount": 0,
    "watchAlertCount": 0,
    "recentAlerts": [
      {
        "id": "uuid",
        "type": "string",
        "severity": "string",
        "message": "string",
        "acknowledged_at": null,
        "created_at": "datetime"
      }
    ]
  }
}
```

---

## Standard Error Response Shape

```json
{
  "success": false,
  "message": "Detailed error message",
  "data": null,
  "meta": null,
  "error": { "code": "VALIDATION_ERROR", "message": "Detailed error message" }
}
```
