# Medical History Module — API Reference

**Authentication:** All endpoints require a valid Bearer token 🔒

---

## GET `/patients/{user_id}/medical-history` 🔒

Retrieves the medical history record for a specific patient.

**Headers**
```
Authorization: Bearer <access_token>
```

**Path Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `user_id` | string (UUID) | ✅ | The ID of the patient |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "c1f13b63-1d0b-46db-ab61-821f57076de1",
    "patient_user_id": "778b6c71-77af-492e-8165-9aae62545469",
    "created_by": "00000000-0000-0000-0000-000000000000",
    "last_updated_by": "00000000-0000-0000-0000-000000000000",
    "blood_type": "A",
    "rh_factor": "+",
    "allergies": ["Penicillin"],
    "chronic_conditions": ["Gestational hypertension"],
    "current_medications": [
      {
        "name": "Ferrous Sulfate",
        "dose": "200mg",
        "frequency": "Once daily"
      }
    ],
    "surgical_history": [
      {
        "procedure": "Appendectomy",
        "year": "2015"
      }
    ],
    "previous_pregnancies": 1,
    "previous_outcomes": ["LIVE_BIRTH"],
    "family_history": ["Hypertension"],
    "custom_fields": {
      "vision": "Myopia"
    },
    "created_at": "2026-07-21T19:55:00Z",
    "updated_at": "2026-07-21T19:55:00Z"
  },
  "meta": null
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |
| `404` | `NOT_FOUND` | Medical history not found |

---

## POST `/patients/{user_id}/medical-history` 🔒 👩‍⚕️

Creates a medical history record for a specific patient. Requires Clinician or Facility Admin privileges.

**Headers**
```
Authorization: Bearer <access_token>
```

**Path Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `user_id` | string (UUID) | ✅ | The ID of the patient |

**Request Body**
```json
{
  "blood_type": "A",
  "rh_factor": "+",
  "allergies": ["Penicillin"],
  "chronic_conditions": [],
  "current_medications": [],
  "surgical_history": [],
  "previous_pregnancies": 0,
  "previous_outcomes": [],
  "family_history": [],
  "custom_fields": {}
}
```

**Response `200 OK`**
Returns the created `MedicalHistoryRecordRead` object.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |
| `403` | `FORBIDDEN` | User is not a clinician |
| `409` | `CONFLICT` | Medical history record already exists for this patient |

---

## PUT `/patients/{user_id}/medical-history` 🔒 👩‍⚕️

Updates an existing medical history record for a specific patient. Requires Clinician or Facility Admin privileges.

**Headers**
```
Authorization: Bearer <access_token>
```

**Path Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `user_id` | string (UUID) | ✅ | The ID of the patient |

**Request Body**
*(Same as POST `/patients/{user_id}/medical-history`, all fields optional)*

**Response `200 OK`**
Returns the updated `MedicalHistoryRecordRead` object.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |
| `403` | `FORBIDDEN` | User is not a clinician |
| `404` | `NOT_FOUND` | Medical history record not found |

---

## GET `/facility/medical-history-fields` 🔒 🏥 👩‍⚕️

Lists medical history custom fields defined by the facility. Requires Clinician or Facility Admin privileges, and an active facility context.

**Headers**
```
Authorization: Bearer <access_token>
X-Facility-Context: <facility_uuid>
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "e6f423ab-2423-4411-9a7e-12822a1f434a",
      "facility_id": "00000000-0000-0000-0000-000000000000",
      "created_by": "00000000-0000-0000-0000-000000000000",
      "key": "bmi_at_booking",
      "label": "BMI at Booking",
      "type": "NUMBER",
      "options": null,
      "created_at": "2026-07-21T19:55:00Z"
    }
  ],
  "meta": null
}
```

---

## POST `/facility/medical-history-fields` 🔒 🏥 👩‍⚕️

Defines a new medical history custom field for the facility. Requires Clinician or Facility Admin privileges, and an active facility context.

**Headers**
```
Authorization: Bearer <access_token>
X-Facility-Context: <facility_uuid>
```

**Request Body**
```json
{
  "key": "blood_sugar_fasting",
  "label": "Fasting Blood Sugar",
  "type": "NUMBER",
  "options": null
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | string | ✅ | Identifier used in `custom_fields` dictionary |
| `label` | string | ✅ | Human-readable label for the UI |
| `type` | string | ✅ | Valid `FieldType` enum (e.g., `TEXT`, `NUMBER`, `SINGLE_SELECT`, `MULTI_SELECT`, `DATE`, `BOOLEAN`) |
| `options` | array of strings | ❌ | Required if type is `SINGLE_SELECT` or `MULTI_SELECT` |

**Response `200 OK`**
Returns the created `MedicalHistoryCustomFieldRead` object.

---

## GET `/profile/medical-history` 🔒

Retrieves the authenticated patient's own medical history record.

**Headers**
```
Authorization: Bearer <access_token>
```

**Response `200 OK`**
Returns the patient's `MedicalHistoryRecordRead` object.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing or invalid access token |
| `404` | `NOT_FOUND` | Medical history not found |
