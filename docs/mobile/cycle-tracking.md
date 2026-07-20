# Cycle Tracking Module — API Reference

**Base path:** `/api/v1/cycles`
**Authentication:** All endpoints require a valid Bearer token 🔒

---

## GET `/entries/form-template` 🔒

Retrieves the active form template for logging a cycle entry.

**Headers**
```
Authorization: Bearer <access_token>
```

**Query Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `facility_id` | string (UUID) | ❌ | Passing a facility ID attempts to fetch a custom template for that clinic. Falls back to the global template if none is found. |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "e6f423ab-2423-4411-9a7e-12822a1f434a",
    "slug": "tmpl_cycle_entry_v1",
    "context": "CYCLE_ENTRY",
    "fields": { ... },
    "version": "v1",
    "is_active": true,
    "facility_id": null,
    "created_at": "2026-07-01T07:05:37Z"
  },
  "meta": {}
}
```

---

## POST `/entries` 🔒

Logs the start of a period and its initial characteristics.

**Headers**
```
Authorization: Bearer <access_token>
```

**Request Body**
```json
{
  "startDate": "2026-07-01",
  "templateSlug": "tmpl_cycle_entry_v1",
  "answers": {
    "flowLevel": "MODERATE",
    "clotLevel": "NONE",
    "flags": []
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `startDate` | date (YYYY-MM-DD) | ✅ | |
| `templateSlug` | string | ✅ | Use `"tmpl_cycle_entry_v1"` |
| `answers` | object | ✅ | Must match the fields defined in the template |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "86361714-41dd-4bad-9cb7-01c8e53f68d0",
    "user_id": "f1571b88-0d48-4e88-800c-87bfa0249c81",
    "submission_id": "e8825613-ca13-482d-9592-061a8fdd439b",
    "start_date": "2026-07-01",
    "end_date": null,
    "pbac_score": 0,
    "submission": {
      "answers": {
        "flowLevel": "MODERATE",
        "clotLevel": "NONE",
        "flags": []
      }
    },
    "created_at": "2026-07-01T07:05:37Z",
    "updated_at": "2026-07-01T07:05:37Z"
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |
| `404` | `NOT_FOUND` | Template slug does not exist |
| `422` | `VALIDATION_ERROR` | Missing required field or invalid data |

---

## GET `/entries` 🔒

Retrieves a paginated list of the user's cycle entries.

**Headers**
```
Authorization: Bearer <access_token>
```

**Query Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `page` | integer | ❌ | Default: `1` |
| `pageSize` | integer | ❌ | Default: `20` |
| `from` | date (YYYY-MM-DD) | ❌ | Filter entries after date |
| `to` | date (YYYY-MM-DD) | ❌ | Filter entries before date |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "86361714-41dd-4bad-9cb7-01c8e53f68d0",
      "start_date": "2026-07-01",
      "pbac_score": 0
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 1,
    "totalPages": 1
  }
}
```

---

## POST `/symptoms` 🔒

Logs symptoms experienced on a specific day.

**Headers**
```
Authorization: Bearer <access_token>
```

**Request Body**
```json
{
  "date": "2026-07-01",
  "templateSlug": "tmpl_symptom_entry_v1",
  "answers": {
    "symptoms": ["CRAMPS", "BLOATING"],
    "notes": "Feeling a bit tired today"
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `date` | date (YYYY-MM-DD) | ✅ | |
| `templateSlug` | string | ✅ | Use `"tmpl_symptom_entry_v1"` |
| `answers` | object | ✅ | Must match the fields defined in the template |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "92269422-2492-4f6d-ac9f-1de67890fca3",
    "context": "CYCLE_SYMPTOM",
    "answers": {
      "symptoms": ["CRAMPS", "BLOATING"],
      "notes": "Feeling a bit tired today"
    },
    "client_created_at": "2026-07-01T00:00:00Z",
    "symptom_date": "2026-07-01",
    "created_at": "2026-07-01T07:25:17Z"
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |
| `404` | `NOT_FOUND` | Template slug does not exist |
| `422` | `VALIDATION_ERROR` | Missing required field or invalid data |

---

## GET `/symptoms` 🔒

Retrieves a paginated list of the user's logged symptoms.

**Headers**
```
Authorization: Bearer <access_token>
```

**Query Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `page` | integer | ❌ | Default: `1` |
| `pageSize` | integer | ❌ | Default: `20` |
| `from` | date (YYYY-MM-DD) | ❌ | Filter symptoms after date |
| `to` | date (YYYY-MM-DD) | ❌ | Filter symptoms before date |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "92269422-2492-4f6d-ac9f-1de67890fca3",
      "context": "CYCLE_SYMPTOM",
      "answers": {
        "symptoms": ["CRAMPS", "BLOATING"],
        "notes": "Feeling a bit tired today"
      },
      "client_created_at": "2026-07-01T00:00:00Z",
      "symptom_date": "2026-07-01",
      "created_at": "2026-07-01T07:25:17Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 1,
    "totalPages": 1
  }
}
```

---

## GET `/predictions` 🔒

Calculates the start date of the next period and estimated ovulation window based on the user's historical cycle length.

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
    "nextPeriodPredictedDate": "2026-07-29",
    "ovulationWindowStart": "2026-07-11",
    "ovulationWindowEnd": "2026-07-15",
    "averageCycleLengthDays": 28,
    "currentCycleDay": 1
  },
  "meta": {}
}
```
*(Note: Fields will return `null` if the user has fewer than two logged cycle entries.)*

---

## GET `/trends` 🔒

Provides statistical analysis and insights into cycle lengths over a given duration.

**Headers**
```
Authorization: Bearer <access_token>
```

**Query Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `months` | integer | ❌ | Default: `6`. Max: `24` |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "averageCycleLength": 28,
    "shortestCycleLength": 26,
    "longestCycleLength": 29,
    "insights": [
      "Your cycles are highly regular."
    ]
  },
  "meta": {}
}
```

---

## POST `/entries/{entry_id}/pbac-items` 🔒

Logs individual feminine hygiene products to calculate the Heavy Menstrual Bleeding (PBAC) score.

**Headers**
```
Authorization: Bearer <access_token>
```

**Path Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `entry_id` | string (UUID) | ✅ | The ID of the cycle entry to attach this item to |

**Request Body**
```json
{
  "date": "2026-07-01",
  "itemType": "PAD",
  "soakLevel": "FULLY_SOAKED",
  "pointValue": 20
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `date` | date (YYYY-MM-DD) | ✅ | |
| `itemType` | enum | ✅ | `PAD` \| `TAMPON` \| `CLOT` |
| `soakLevel` | enum | ✅ | `LIGHTLY_SOAKED` \| `MODERATELY_SOAKED` \| `FULLY_SOAKED` |
| `pointValue` | integer | ✅ | Points assigned for this soak level |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "25d8cef2-014b-4ef7-95e9-1aea8d2d9e60",
    "cycle_entry_id": "128cfea0-5962-4b6a-8203-d02e191ea30c",
    "date": "2026-07-01",
    "item_type": "PAD",
    "soak_level": "FULLY_SOAKED",
    "point_value": 20,
    "created_at": "2026-07-01T08:38:50Z"
  },
  "meta": {}
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |
| `404` | `NOT_FOUND` | Cycle entry does not exist |

---

## GET `/entries/{entry_id}/pbac-score` 🔒

Returns the aggregated PBAC score for a specific cycle entry and triggers an alert if the score exceeds the clinical safety threshold (80).

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
    "entryId": "128cfea0-5962-4b6a-8203-d02e191ea30c",
    "totalScore": 25,
    "isHmbRisk": false
  },
  "meta": {}
}
```

---

## GET `/hmb-status` 🔒

Retrieves the current Heavy Menstrual Bleeding (HMB) alert status. The frontend uses this to determine if it should render the "Talk to Doctor" popup.

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
    "hasActiveAlert": false,
    "lastTriggeredEntryId": null
  },
  "meta": {}
}
```

---

## POST `/hmb-acknowledge` 🔒

Acknowledges an active HMB alert, dismissing it so it no longer shows on the frontend until triggered by a future cycle.

**Headers**
```
Authorization: Bearer <access_token>
```

**Request Body**
```json
{
  "action": "TALK_TO_DOCTOR",
  "entryId": "128cfea0-5962-4b6a-8203-d02e191ea30c"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `action` | enum | ✅ | `DISMISSED` \| `TALK_TO_DOCTOR` |
| `entryId` | string (UUID) | ✅ | |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "hasActiveAlert": false,
    "lastTriggeredEntryId": null
  },
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
    "message": "Detailed error message",
    "fields": {
      "templateSlug": "Missing required field"
    }
  }
}
```

`fields` is only present on validation errors that map to specific request payload fields.

---

## Enum Reference

| Enum | Values |
|---|---|
| `PbacItemType` | `PAD`, `TAMPON`, `CLOT` |
| `PbacSoakLevel` | `LIGHTLY_SOAKED`, `MODERATELY_SOAKED`, `FULLY_SOAKED` |
| `HmbAcknowledgeAction` | `DISMISSED`, `TALK_TO_DOCTOR` |
