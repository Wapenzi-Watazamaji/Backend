# Pregnancy Module — API Reference

**Base path:** `/api/v1/pregnancy`
**Authentication:** All endpoints require a valid Bearer token 🔒

---

## POST `/start` 🔒

Starts a new pregnancy record and automatically generates the ANC (Antenatal Care) visit schedule.

**Headers**
```
Authorization: Bearer <access_token>
```

**Request Body**
```json
{
  "dateInputType": "LMP",
  "lastMenstrualPeriod": "2025-09-10",
  "dueDate": null,
  "isFirstPregnancy": false
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `dateInputType` | enum | ✅ | `"LMP"` \| `"DUE_DATE"` |
| `lastMenstrualPeriod` | date (YYYY-MM-DD) | ❌ | Required if `dateInputType` is `"LMP"` |
| `dueDate` | date (YYYY-MM-DD) | ❌ | Required if `dateInputType` is `"DUE_DATE"` |
| `isFirstPregnancy` | boolean | ❌ | Default: `false` |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "e61d8b62-5de2-4ca5-903a-262ed44b06ac",
    "user_id": "f1571b88-0d48-4e88-800c-87bfa0249c81",
    "last_menstrual_period": "2025-09-10",
    "due_date": "2026-06-17",
    "is_first_pregnancy": false,
    "status": "ACTIVE",
    "outcome": null,
    "ended_at": null,
    "created_at": "2026-07-02T10:00:00Z",
    "updated_at": "2026-07-02T10:00:00Z"
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `400` | `BAD_REQUEST` | Active pregnancy already exists |
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `422` | `VALIDATION_ERROR` | Missing required date fields based on `dateInputType` |

---

## GET `/current` 🔒

Retrieves the user's currently active pregnancy record.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "e61d8b62-5de2-4ca5-903a-262ed44b06ac",
    "user_id": "f1571b88-0d48-4e88-800c-87bfa0249c81",
    "last_menstrual_period": "2025-09-10",
    "due_date": "2026-06-17",
    "is_first_pregnancy": false,
    "status": "ACTIVE",
    "outcome": null,
    "ended_at": null,
    "created_at": "2026-07-02T10:00:00Z",
    "updated_at": "2026-07-02T10:00:00Z"
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | No active pregnancy found |

---

## PUT `/current` 🔒

Updates the current pregnancy due date.

**Request Body**
```json
{
  "dueDate": "2026-06-18"
}
```

**Response `200 OK`**
Returns the updated `PregnancyRecordRead` object (same structure as above).

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | No active pregnancy found |
| `422` | `VALIDATION_ERROR` | Invalid date format |

---

## POST `/end` 🔒

Marks a pregnancy as ended (e.g., delivered) and triggers the transition to postpartum workflows.

**Request Body**
```json
{
  "endedAt": "2026-06-17T10:00:00Z",
  "outcome": "LIVE_BIRTH"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `endedAt` | datetime (ISO 8601) | ✅ | |
| `outcome` | enum | ✅ | `"LIVE_BIRTH"`, `"STILLBIRTH"`, `"MISCARRIAGE"`, `"ABORTION"` |

**Response `200 OK`**
Returns the updated `PregnancyRecordRead` object with `status`="ENDED".

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | No active pregnancy found |
| `422` | `VALIDATION_ERROR` | Invalid enum or datetime |

---

## GET `/week-info` 🔒

Returns contextual medical and developmental information for the user's current week of pregnancy.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "weekNumber": 24,
    "trimester": 2,
    "babySizeComparison": "Ear of corn",
    "developmentNote": "Baby's lungs are forming.",
    "imageUrl": "https://example.com/fetus_week_24.png"
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | No active pregnancy found |

---

## GET `/vitals/form-template` 🔒

Retrieves the dynamic form schema used by the frontend to render the maternal vitals entry form.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "abc-123",
    "slug": "tmpl_preg_vitals_v1",
    "context": "PREGNANCY_VITALS",
    "fields": { "weightKg": { "type": "number", "label": "Weight (kg)" } },
    "version": "1.0",
    "is_active": true
  },
  "meta": {}
}
```

---

## POST `/vitals` 🔒

Logs maternal vitals (e.g., blood pressure, weight) during pregnancy.

**Request Body**
```json
{
  "templateSlug": "tmpl_preg_vitals_v1",
  "answers": {
    "systolicBp": 120,
    "diastolicBp": 80,
    "weightKg": 68.0,
    "symptoms": ["FATIGUE"]
  },
  "clientGeneratedId": "uuid-123",
  "clientCreatedAt": "2026-07-02T10:00:00Z"
}
```

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "def-456",
    "pregnancy_id": "e61d8b62...",
    "submission_id": "ghi-789",
    "is_flagged": false,
    "flagged_reasons": [],
    "answers": {
      "systolicBp": 120,
      "diastolicBp": 80,
      "weightKg": 68.0,
      "symptoms": ["FATIGUE"]
    },
    "created_at": "2026-07-02T10:00:00Z",
    "updated_at": "2026-07-02T10:00:00Z"
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |
| `404` | `NOT_FOUND` | No active pregnancy or template found |
| `422` | `VALIDATION_ERROR` | Schema mismatch |

---

## GET `/vitals` 🔒

Retrieves a paginated list of logged vitals.

**Query Parameters:**
- `page`: integer (default: 1)
- `pageSize`: integer (default: 20)
- `flaggedOnly`: boolean (default: false)

**Response `200 OK`**
Returns a list of `VitalsEntryRead` objects.

---

## GET `/vitals/{entry_id}` 🔒

Retrieves a specific vitals entry.

---

## PUT `/vitals/{entry_id}` 🔒

Updates a specific vitals entry.

**Request Body**
```json
{
  "answers": {
    "systolicBp": 118,
    "diastolicBp": 78
  }
}
```

---

## GET `/patients/{patient_id}/vitals` 🔒⚕️ *(Clinician Only)*

Retrieves a paginated list of vitals for a specific patient. 

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing token |
| `403` | `FORBIDDEN` | User does not have clinician role |

---

## POST `/vitals/{entry_id}/feedback` 🔒⚕️ *(Clinician Only)*

Allows a clinician to leave medical feedback on a patient's vitals submission.

**Request Body**
```json
{
  "message": "Blood pressure looks good, keep resting."
}
```

**Response `201 Created`**
```json
{
  "success": true,
  "data": {
    "id": "jkl-012",
    "vitals_entry_id": "def-456",
    "clinician_id": "doc-789",
    "message": "Blood pressure looks good, keep resting.",
    "created_at": "2026-07-02T10:05:00Z"
  },
  "meta": {}
}
```

---

## GET `/vitals/{entry_id}/feedback` 🔒

Retrieves all feedback left by clinicians for a specific vitals entry.

---

## GET `/anc-visits` 🔒

Retrieves the schedule of Antenatal Care (ANC) visits.

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "vis-123",
      "pathway_template_id": "anc_1",
      "milestone_order": 1,
      "label": "First ANC Visit",
      "scheduled_at": "2025-10-10T00:00:00Z",
      "status": "COMPLETED",
      "facility_id": null,
      "purpose": "First Trimester Screening",
      "summary": "All normal"
    }
  ]
}
```

---

## POST `/anc-visits/manual` 🔒⚕️ *(Clinician Only)*

Manually adds an ad-hoc ANC visit to the patient's schedule.

**Request Body**
```json
{
  "scheduledAt": "2026-02-15T09:00:00Z",
  "facilityId": "fac-123",
  "purpose": "Follow-up Ultrasound"
}
```

---

## PUT `/anc-visits/{visit_id}` 🔒

Updates an ANC visit (e.g., marking it as completed or rescheduling).

**Request Body**
```json
{
  "status": "COMPLETED",
  "summary": "Patient is healthy",
  "scheduledAt": "2026-02-15T10:00:00Z"
}
```

---

## GET `/nutrition-guidance` 🔒

Retrieves categorized nutrition guidance tailored for pregnancy.

**Query Parameters:**
- `category`: enum (e.g. `MACRONUTRIENTS`, `VITAMINS`, `HYDRATION`)

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "nut-123",
      "category": "VITAMINS",
      "title": "Folic Acid",
      "summary": "Take 400mcg daily.",
      "trimester_relevance": [1, 2, 3],
      "icon_url": null
    }
  ]
}
```

---

## GET `/risk-score` 🔒

Calculates and retrieves the mother's current composite risk score based on recent vitals.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "score": 15,
    "level": "MODERATE",
    "calculatedAt": "2026-07-02T10:00:00Z",
    "clinicianOverride": null,
    "factors": [
      {
        "label": "Elevated Blood Pressure",
        "weight": 15,
        "severity": "MODERATE",
        "description": "Systolic > 140"
      }
    ]
  }
}
```

---

## GET `/risk-score/history` 🔒

Retrieves the historical trend of the mother's risk score over time.

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "calculatedAt": "2026-06-01T10:00:00Z",
      "score": 0,
      "level": "LOW"
    },
    {
      "calculatedAt": "2026-07-01T10:00:00Z",
      "score": 15,
      "level": "MODERATE"
    }
  ]
}
```

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
