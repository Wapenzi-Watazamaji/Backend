# Pregnancy Module — API Reference (Web Dashboard / Clinical)

**Base path:** `/api/v1/pregnancy`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` · 🔑 `CLINICIAN` (unless noted) · 🏢 `X-Facility-Context: <facility_id>`

> A mother's own pregnancy tracking (starting/ending a pregnancy, logging her own vitals, ANC schedule, risk score, nutrition guidance) lives in [`docs/mobile/pregnancy.md`](../mobile/pregnancy.md).

---

## GET `/patients/{patient_id}/vitals`

Retrieves a paginated list of vitals for a specific patient.

**Role required:** `CLINICIAN`

**Query Parameters:** `page` (default 1), `pageSize` (default 20)

**Response `200 OK`** — list of `VitalsEntryRead` objects, paginated in `meta`.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing token |
| `403` | `FORBIDDEN` | Caller does not have the `CLINICIAN` role |

---

## POST `/vitals/{entry_id}/feedback`

Leaves clinical feedback on a patient's vitals submission. Surfaces to the mother via `GET /vitals/{entry_id}/feedback` in the mobile app.

**Role required:** `CLINICIAN`

**Request Body**
```json
{ "message": "Blood pressure looks good, keep resting." }
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
  }
}
```

---

## POST `/anc-visits/manual/{patient_id}`

Manually adds an ad-hoc ANC visit to a patient's schedule (e.g. an unscheduled follow-up), outside the standard auto-generated MOH schedule.

**Role required:** `CLINICIAN` · 🏢

**Path Parameters:** `patient_id` (UUID) — the patient the visit is being added for.

**Request Body**
```json
{
  "scheduledAt": "2026-02-15T09:00:00Z",
  "facilityId": "fac-123",
  "purpose": "Follow-up Ultrasound"
}
```

`facilityId` is optional; when omitted, the facility from `X-Facility-Context` is used.

**Response `201 Created`** — `VisitRead` object with `pathway_template_id: null` (marking it as manually created, not part of the auto-generated schedule).

---

## PUT `/anc-visits/{visit_id}/patient/{user_id}`

Updates an ANC visit (e.g. marking it as completed, or rescheduling it). Note the path requires **both** the visit ID and the owning patient's user ID.

**Role required:** `CLINICIAN` · 🏢

**Path Parameters:** `visit_id` (UUID), `user_id` (UUID) — the patient who owns the visit.

**Request Body**
```json
{
  "status": "COMPLETED",
  "summary": "Patient is healthy",
  "scheduledAt": "2026-02-15T10:00:00Z"
}
```

All fields optional — `status` (`SCHEDULED`\|`COMPLETED`\|`MISSED`\|`RESCHEDULED`), `summary`, `scheduledAt` (reschedule).

**Response `200 OK`** — Updated `VisitRead` object.

---

## PUT `/patients/{patient_id}/risk-score/override`

Overrides a patient's computed pregnancy risk level with a clinician's clinical judgment call (e.g. downgrading a flagged risk after a follow-up resolves it). The override surfaces to the mother via `clinicianOverride` in `GET /pregnancy/risk-score` (see `docs/mobile/pregnancy.md`).

**Role required:** `CLINICIAN` · 🏢

**Path Parameters:** `patient_id` (UUID)

**Request Body**
```json
{
  "level": "LOW",
  "reason": "Reduced fetal movement resolved after follow-up call"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `level` | enum | ✅ | `LOW` \| `MEDIUM` \| `HIGH` |
| `reason` | string | ✅ | Clinical justification, shown to the mother |

**Response `200 OK`** — Updated `RiskScoreRead` object with `clinicianOverride` populated (`overriddenBy` set to the caller's user ID, `overriddenAt` stamped server-side).

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
