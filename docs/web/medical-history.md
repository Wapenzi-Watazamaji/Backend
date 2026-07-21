# Medical History — API Reference (Web Dashboard)

**Base path:** `/api/v1/medical-history`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` · 🔑 `CLINICIAN` (unless noted) · 🏢 `X-Facility-Context: <facility_id>` (facility custom-field endpoints only)

> A mother reads her own record via `GET /profile/medical-history` — see [`docs/mobile/medical-history.md`](../mobile/medical-history.md).

---

## GET `/patients/{user_id}/medical-history`

Returns a patient's medical history record.

**Path Parameters:** `user_id` (UUID)

**Response `200 OK`** — `MedicalHistoryRecordRead` object (same shape as the mobile `GET /profile/medical-history`).

> **Note:** this endpoint only requires a valid access token, not specifically the `CLINICIAN` role at the route level — but it's intended for clinical use, so keep it behind your app's role-gated navigation regardless.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | No medical history record exists for this patient |

---

## POST `/patients/{user_id}/medical-history`

Creates a patient's medical history record.

**Role required:** `CLINICIAN`

**Request Body** (all fields optional)
```json
{
  "blood_type": "O",
  "rh_factor": "+",
  "allergies": ["Penicillin"],
  "chronic_conditions": [],
  "current_medications": [{ "name": "Ferrous sulfate", "dose": "200mg", "frequency": "Once daily" }],
  "surgical_history": [{ "procedure": "Appendectomy", "year": "2015" }],
  "previous_pregnancies": 1,
  "previous_outcomes": [],
  "family_history": [],
  "custom_fields": { "home_bp_monitor": true }
}
```

**Response `201 Created`** — the created `MedicalHistoryRecordRead` object, `created_by`/`last_updated_by` set to the calling clinician.

---

## PUT `/patients/{user_id}/medical-history`

Updates a patient's medical history record (same body shape as `POST`, all fields optional).

**Role required:** `CLINICIAN`

**Response `200 OK`** — the updated record, `last_updated_by` set to the calling clinician.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | No record exists yet — use `POST` first |

---

## Facility Custom Fields

Lets a facility define extra medical-history fields for its own patient population (e.g. a field specific to a local screening program), surfaced back to the mother in `custom_fields` on her own record.

### GET `/facility/medical-history-fields`

Lists custom fields defined for the facility in context.

**Role required:** `CLINICIAN` · 🏢

**Response `200 OK`** — array of `MedicalHistoryCustomFieldRead`:
```json
{
  "success": true,
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "facility_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "key": "home_bp_monitor",
      "label": "Has a home BP monitor?",
      "type": "BOOLEAN",
      "options": null,
      "created_by": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "created_at": "2026-07-01T09:00:00Z"
    }
  ]
}
```

### POST `/facility/medical-history-fields`

Defines a new custom field for the facility.

**Role required:** `CLINICIAN` · 🏢

**Request Body**
```json
{
  "key": "home_bp_monitor",
  "label": "Has a home BP monitor?",
  "type": "BOOLEAN",
  "options": null
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | string | ✅ | Machine key, referenced in `custom_fields` on the patient's record |
| `label` | string | ✅ | Display label |
| `type` | enum | ✅ | See `FieldType` below |
| `options` | string[] | ❌ | Required for `SINGLE_SELECT`/`MULTI_SELECT` types |

**Response `201 Created`** — the created `MedicalHistoryCustomFieldRead` object.

---

## Enum Reference

| Enum | Values |
|---|---|
| `FieldType` | `BOOLEAN`, `TEXT`, `NUMBER`, `SINGLE_SELECT`, `MULTI_SELECT` |
