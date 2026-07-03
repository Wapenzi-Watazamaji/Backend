# Postpartum Module — API Reference

**Base path:** `/api/v1/postpartum`
**Authentication:** All endpoints require a valid Bearer token 🔒

---

## GET `/maternal-checkins/form-template` 🔒

Retrieves the dynamic form schema used by the frontend to render the postpartum maternal check-in form.

**Headers**
```
Authorization: Bearer <access_token>
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "abc-123",
    "slug": "tmpl_postpartum_checkin_v1",
    "context": "MATERNAL_CHECKIN",
    "fields": { "bleedingLevel": { "type": "enum", "options": ["NONE", "LIGHT"] } },
    "version": "1.0",
    "is_active": true
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid token |

---

## POST `/maternal-checkins` 🔒

Submits a postpartum maternal check-in (e.g., bleeding, pain levels).

**Request Body**
```json
{
  "templateId": "tmpl_postpartum_checkin_v1",
  "answers": {
    "bleedingLevel": "MODERATE",
    "painLevel": 4,
    "symptoms": ["FATIGUE"]
  },
  "clientGeneratedId": "uuid-123",
  "clientCreatedAt": "2026-07-02T10:00:00Z"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `templateId` | string | ✅ | Matches the `slug` of the template |
| `answers` | object | ✅ | Dictionary of answers |
| `clientGeneratedId` | string | ❌ | Deduplication key |
| `clientCreatedAt` | datetime | ❌ | When the user filled it offline |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "chk-123",
    "template_id": "tmpl-abc",
    "user_id": "usr-456",
    "context": "MATERNAL_CHECKIN",
    "answers": {
      "bleedingLevel": "MODERATE",
      "painLevel": 4,
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
| `401` | `UNAUTHORIZED` | Missing token |
| `404` | `NOT_FOUND` | Template not found |
| `422` | `VALIDATION_ERROR` | Missing required answers |

---

## GET `/maternal-checkins` 🔒

Retrieves a list of submitted maternal check-ins.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "chk-123",
      "template_id": "tmpl-abc",
      "user_id": "usr-456",
      "context": "MATERNAL_CHECKIN",
      "answers": {
        "bleedingLevel": "MODERATE"
      },
      "created_at": "2026-07-02T10:00:00Z",
      "updated_at": "2026-07-02T10:00:00Z"
    }
  ],
  "meta": {}
}
```

---

## GET `/maternal-checkins/{checkin_id}` 🔒

Retrieves a specific maternal check-in submission.

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Check-in not found |

---

## POST `/depression-screening` 🔒

Submits answers to the Edinburgh Postnatal Depression Scale (EPDS) screening.

**Request Body**
```json
{
  "responses": [
    { "questionId": "q1", "answerValue": 1 },
    { "questionId": "q2", "answerValue": 2 },
    { "questionId": "q10", "answerValue": 3 }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `responses` | list[object] | ✅ | Contains answers to the screening |
| `questionId` | string | ✅ | "q1" through "q10" |
| `answerValue` | int | ✅ | Valid range: 0-3 |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "epds-123",
    "totalScore": 14,
    "suggestsSupportBeneficial": true,
    "immediateConcernFlag": true,
    "completedAt": "2026-07-02T10:00:00Z"
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `422` | `VALIDATION_ERROR` | Answer outside 0-3 range |

---

## GET `/depression-screening/history` 🔒

Retrieves the user's historical EPDS screening results.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "epds-123",
      "totalScore": 14,
      "immediateConcernFlag": true,
      "completedAt": "2026-07-02T10:00:00Z"
    }
  ],
  "meta": {}
}
```

---

## GET `/depression-screening/flag` 🔒

Checks if the mother currently has an active clinical flag (e.g., for self-harm responses on the EPDS).

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "isActive": true
  },
  "meta": {}
}
```

---

## POST `/baby/profile` 🔒

Creates a new baby profile and automatically generates the standardized vaccination schedule for the infant.

**Request Body**
```json
{
  "name": "Amani",
  "dateOfBirth": "2026-06-17",
  "timeOfBirth": "09:42",
  "sex": "FEMALE",
  "birthWeightKg": 3.2,
  "birthLengthCm": 49,
  "deliveryType": "VAGINAL",
  "placeOfBirth": "Outspan Hospital",
  "notes": "Healthy",
  "pregnancyId": "e61d8b62..."
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | ✅ | Baby's name |
| `dateOfBirth` | date (YYYY-MM-DD) | ✅ | |
| `timeOfBirth` | string (HH:MM) | ❌ | |
| `sex` | enum | ❌ | `"MALE"` \| `"FEMALE"` |
| `birthWeightKg` | float | ❌ | |
| `birthLengthCm` | float | ❌ | |
| `deliveryType` | enum | ❌ | `"VAGINAL"` \| `"CAESAREAN"` |
| `pregnancyId` | uuid | ❌ | Linking back to pregnancy module |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "bab-123",
    "user_id": "usr-456",
    "pregnancy_id": "preg-789",
    "name": "Amani",
    "date_of_birth": "2026-06-17",
    "time_of_birth": "09:42:00",
    "gender": "FEMALE",
    "delivery_type": "VAGINAL",
    "birth_weight_kg": 3.2,
    "birth_length_cm": 49,
    "place_of_birth": "Outspan Hospital",
    "notes": "Healthy",
    "created_at": "2026-07-02T10:00:00Z",
    "updated_at": "2026-07-02T10:00:00Z"
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `422` | `VALIDATION_ERROR` | Missing name or DOB |

---

## GET `/baby/profiles` 🔒

Lists all baby profiles registered to the current mother.

**Response `200 OK`**
Returns a list of `BabyProfileRead` objects.

---

## GET `/baby/profiles/{baby_id}` 🔒

Retrieves the details of a specific baby profile.

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Baby not found |

---

## PUT `/baby/profiles/{baby_id}` 🔒

Updates a specific baby profile.

**Request Body**
```json
{
  "birthWeightKg": 3.4
}
```

---

## GET `/baby/vitals/form-template` 🔒

Retrieves the dynamic form schema for the baby vitals tracking form.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "abc-123",
    "slug": "tmpl_baby_vitals_v1",
    "context": "BABY_VITALS",
    "fields": { "temperatureCelsius": { "type": "number" } },
    "version": "1.0",
    "is_active": true
  },
  "meta": {}
}
```

---

## POST `/baby/{baby_id}/vitals` 🔒

Logs vitals/health data for a specific baby.

**Request Body**
```json
{
  "templateId": "tmpl_baby_vitals_v1",
  "answers": {
    "temperatureCelsius": 36.8,
    "feedingType": "BREASTFEEDING"
  },
  "clientGeneratedId": "uuid-123"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `templateId` | string | ✅ | Matches the `slug` |
| `answers` | object | ✅ | Dynamic based on schema |

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Baby or Template not found |

---

## GET `/baby/{baby_id}/vitals` 🔒

Retrieves the historical vitals submissions for a specific baby.

---

## GET `/baby/{baby_id}/vitals/alerts` 🔒

Retrieves active health alerts automatically generated from abnormal baby vitals submissions.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "alt-123",
      "type": "HIGH_TEMPERATURE",
      "message": "Fever detected, please seek medical attention.",
      "createdAt": "2026-07-02T10:00:00Z"
    }
  ],
  "meta": {}
}
```

---

## POST `/baby/{baby_id}/milestones` 🔒

Records a developmental milestone for a specific baby.

**Request Body**
```json
{
  "category": "MOVEMENT",
  "title": "Lifted head",
  "achievedAt": "2026-07-15",
  "note": "So proud!",
  "photoUrl": "https://example.com/photo.jpg"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `category` | enum | ✅ | `"MOVEMENT"`, `"SOCIAL"`, etc. |
| `title` | string | ✅ | |
| `achievedAt` | date | ✅ | |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "ms-123",
    "baby_id": "e61d8b62...",
    "user_id": "usr-456",
    "category": "MOVEMENT",
    "title": "Lifted head",
    "achieved_at": "2026-07-15",
    "note": "So proud!",
    "photo_url": "https://example.com/photo.jpg",
    "created_at": "2026-07-15T10:00:00Z"
  },
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Baby not found |

---

## GET `/baby/{baby_id}/milestones` 🔒

Retrieves the list of recorded developmental milestones for a specific baby.

**Query Parameters:**
- `category`: enum (`MOVEMENT`, `SOCIAL`, `LANGUAGE`, `COGNITIVE`)

---

## POST `/baby/{baby_id}/vaccinations` 🔒

Records an ad-hoc or historical vaccination outside of the generated schedule.

**Request Body**
```json
{
  "vaccineId": "vac_bcg",
  "givenAt": "2026-06-17T10:00:00Z",
  "facilityId": "fac_1029",
  "batchNumber": "BCG-123"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `vaccineId` | string | ✅ | e.g. `"vac_bcg"` |
| `givenAt` | datetime | ✅ | |
| `facilityId` | string | ❌ | |

**Response `201 Created`**
Returns the generated `VaccinationRecordRead` object.

---

## GET `/baby/{baby_id}/vaccinations/schedule` 🔒

Retrieves the complete vaccination schedule for a specific baby, including past, upcoming, and overdue visits.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "vis-123",
      "vaccineId": "vac_bcg",
      "name": "BCG",
      "ageMilestone": "Birth",
      "status": "OVERDUE",
      "scheduledAt": "2026-06-17T00:00:00Z",
      "givenAt": null
    }
  ],
  "meta": {}
}
```

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Baby not found |

---

## PUT `/baby/{baby_id}/vaccinations/{visit_id}/mark-given` 🔒

Marks a scheduled vaccination visit as administered.

**Request Body**
```json
{
  "givenAt": "2026-07-15T10:00:00Z",
  "facilityId": "fac_1029",
  "batchNumber": "BCG-2026-0091"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `givenAt` | datetime | ✅ | |

**Response `200 OK`**
Returns the updated vaccination schedule item.

**Errors**
| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Baby or Vaccination visit not found |

---

## GET `/clinic-visits/schedule` 🔒

Retrieves the combined postnatal clinic-visit schedule for the mother and baby.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "vis-123",
      "label": "2 Week Checkup",
      "scheduledAt": "2026-07-01T00:00:00Z",
      "covers": ["MOTHER", "BABY"],
      "status": "UPCOMING"
    }
  ],
  "meta": {}
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
