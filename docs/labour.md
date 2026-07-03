# Labour & Birth Monitor Module — API Reference

**Base path:** `/api/v1/labour`
**Authentication:** All endpoints require a valid Bearer token 🔒
**Clinician Access:** Endpoints that write to the database require a `CLINICIAN` or `FACILITY_ADMIN` role ⚕️.

---

## POST `/sessions` 🔒⚕️

Opens a new active labour session for a pregnant mother.

**Headers**
```
Authorization: Bearer <access_token>
```

**Request Body**
```json
{
  "pregnancyId": "800eb70b-4e2a-45d5-8ddc-43e7127dcdb3",
  "facilityId": "b071e013-9e82-4143-bca1-2b15ac6498c9",
  "activeLabourStartedAt": "2026-07-03T08:00:00Z"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `pregnancyId` | UUID | ✅ | ID of the active pregnancy record |
| `facilityId` | UUID | ✅ | Facility where the session is taking place |
| `activeLabourStartedAt` | datetime (ISO 8601) | ✅ | |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "7719e249-c628-4b33-9511-b6a0fdd75310",
    "pregnancy_id": "800eb70b-4e2a-45d5-8ddc-43e7127dcdb3",
    "facility_id": "b071e013-9e82-4143-bca1-2b15ac6498c9",
    "clinician_id": "f1571b88-0d48-4e88-800c-87bfa0249c81",
    "status": "ACTIVE",
    "outcome": null,
    "delivery_type": null,
    "active_labour_started_at": "2026-07-03T08:00:00Z",
    "closed_at": null,
    "created_at": "2026-07-03T08:00:00Z",
    "updated_at": "2026-07-03T08:00:00Z"
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `403` | `FORBIDDEN` | Missing clinician role |
| `404` | `NOT_FOUND` | Associated pregnancy or facility not found |

---

## GET `/sessions/{session_id}` 🔒

Retrieves a specific labour session.

**Response `200 OK`**
Returns the `LabourSessionRead` object (same structure as above).

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | Labour session does not exist |

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
| `outcome` | enum | ✅ | `"LIVE_BIRTH"`, `"STILLBIRTH"`, `"REFERRED"`, `"OTHER"` |
| `deliveryType` | enum | ✅ | `"VAGINAL"`, `"C_SECTION"`, `"ASSISTED"` |

**Response `200 OK`**
Returns the updated `LabourSessionRead` object with `status`="CLOSED".

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Session is already closed |
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `403` | `FORBIDDEN` | Missing clinician role |
| `404` | `NOT_FOUND` | Labour session does not exist |

---

## POST `/sessions/{session_id}/readings/dilation` 🔒⚕️

Logs a cervical dilation reading. Will trigger partograph alert logic.

**Request Body**
```json
{
  "value": 4,
  "recordedAt": "2026-07-03T08:00:00Z"
}
```

**Response `201 Created`**
Returns the created `LabourReadingRead` object.

---

## POST `/sessions/{session_id}/readings/fhr` 🔒⚕️

Logs a fetal heart rate (FHR) reading. Triggers alert logic if outside 110–160 bpm.

**Request Body**
```json
{
  "value": 152,
  "recordedAt": "2026-07-03T08:00:00Z"
}
```

---

## POST `/sessions/{session_id}/readings/maternal-vitals` 🔒⚕️

Logs maternal blood pressure. Triggers `PREECLAMPSIA_RISK` alert if systolic >= 140.

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

## GET `/sessions/{session_id}/partograph` 🔒

Retrieves the computed partograph data points, alert lines, and action lines for plotting on the frontend.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "dilationReadings": [
      { "hoursElapsed": 0.0, "value": 4.0, "recordedAt": "2026-07-03T08:00:00Z" }
    ],
    "fhrReadings": [
      { "hoursElapsed": 0.0, "value": 152.0, "recordedAt": "2026-07-03T08:00:00Z" }
    ],
    "alertLine":  { "startHour": 0, "startCm": 4.0, "slopeCmPerHour": 1.0 },
    "actionLine": { "startHour": 4, "startCm": 4.0, "slopeCmPerHour": 1.0 },
    "hasAlertLineCrossed": false,
    "hasActionLineCrossed": false
  },
  "meta": {}
}
```

---

## GET `/sessions/{session_id}/alerts` 🔒

Lists all auto-generated clinical alerts for the labour session.

**Response `200 OK`**
Returns a list of `LabourAlertRead` objects.

---

## POST `/sessions/{session_id}/alerts/{alert_id}/acknowledge` 🔒⚕️

Marks a labour alert as acknowledged by the clinician.

**Response `200 OK`**
Returns the updated `LabourAlertRead` object with `acknowledged_at` and `acknowledged_by` populated.

---

## POST `/sessions/{session_id}/alerts/{alert_id}/escalate` 🔒⚕️

Escalates an alert to a higher level or triggers a referral flow.

**Request Body**
```json
{
  "escalateTo": "SPECIALIST"
}
```

**Response `200 OK`**
Returns a dictionary containing the escalated target.

---

## GET `/resuscitation-protocol` 🔒

Retrieves the WHO neonatal resuscitation protocol steps.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "steps": [
      {
        "order": 1,
        "title": "Dry, warm, and position the baby",
        "timerSeconds": null,
        "instructions": null
      }
    ]
  },
  "meta": {}
}
```

---

## POST `/sessions/{session_id}/resuscitation-log` 🔒⚕️

Logs a completed resuscitation step during delivery.

**Request Body**
```json
{
  "stepOrder": 1,
  "completedAt": "2026-07-03T10:00:00Z",
  "vitalsAtStep": {
    "heartRateBpm": 90,
    "respiratoryEffort": "GASPING"
  }
}
```

**Response `201 Created`**
Returns the created `ResuscitationLogRead` object.

---

## Standard Error Response Shape

All errors follow this envelope:

```json
{
  "success": false,
  "message": "Detailed error message",
  "data": null,
  "meta": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Detailed error message"
  }
}
```
