# Medical History — API Reference (Mobile / Mother-facing)

**Base path:** `/api/v1/medical-history`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` (role `USER`)

A mother's medical history record is created/edited by clinicians, not by the mother herself — see [`docs/web/medical-history.md`](../web/medical-history.md). This is a read-only self-service view.

---

## GET `/profile/medical-history`

Returns the authenticated user's own medical history record.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "patient_user_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
    "blood_type": "O",
    "rh_factor": "+",
    "allergies": ["Penicillin"],
    "chronic_conditions": [],
    "current_medications": [{ "name": "Ferrous sulfate", "dose": "200mg", "frequency": "Once daily" }],
    "surgical_history": [],
    "previous_pregnancies": 1,
    "previous_outcomes": [],
    "family_history": [],
    "custom_fields": null,
    "created_by": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
    "last_updated_by": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
    "created_at": "2026-07-01T09:00:00Z",
    "updated_at": "2026-07-01T09:00:00Z"
  }
}
```

`custom_fields` holds any facility-specific fields a clinician has recorded (see `docs/web/medical-history.md` for how those are defined).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | No medical history record exists yet for this user |
