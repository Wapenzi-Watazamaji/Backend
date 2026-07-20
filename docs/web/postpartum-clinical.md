# Postpartum Module — API Reference (Web Dashboard / Clinical)

**Base path:** `/api/v1/postpartum`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` · 🔑 `CLINICIAN` · 🏢 `X-Facility-Context: <facility_id>`

> A mother's own postpartum tracking (maternal check-ins, EPDS screening, baby profiles/vitals/milestones/vaccinations) lives in [`docs/mobile/postpartum.md`](../mobile/postpartum.md). All endpoints below read data the mother has already submitted there, gated by an active consent relationship between the patient and the calling facility (see `docs/mobile/referrals-emergencies.md` for how consent works).

---

## GET `/patients/{patient_id}/babies`

Returns a patient's baby profiles (supports twins/multiples — a list, not a single object).

**Path Parameters:** `patient_id` (UUID)

**Response `200 OK`** — array of `BabyProfileRead` objects (same shape as the mobile `GET /baby/profiles`).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `403` | `FORBIDDEN` | Patient has not consented to sharing data with this facility |

---

## GET `/patients/{patient_id}/epds`

Returns a patient's EPDS (Edinburgh Postnatal Depression Scale) screening history.

**Path Parameters:** `patient_id` (UUID)

**Response `200 OK`** — array of `EpdsHistoryItem` objects:
```json
{
  "success": true,
  "data": [
    { "id": "epds-123", "totalScore": 14, "immediateConcernFlag": true, "completedAt": "2026-07-02T10:00:00Z" }
  ]
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `403` | `FORBIDDEN` | Patient has not consented to sharing data with this facility |

---

## GET `/patients/{patient_id}/maternal-checkins`

Returns a patient's submitted maternal check-ins.

**Path Parameters:** `patient_id` (UUID)

**Response `200 OK`** — array of `MaternalCheckinRead` objects (same shape as the mobile `GET /maternal-checkins`).

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `403` | `FORBIDDEN` | Patient has not consented to sharing data with this facility |

---

## GET `/postpartum-alerts/summary`

Facility-wide summary of postpartum alerts — both maternal (e.g. heavy bleeding, fever) and newborn (e.g. jaundice, poor feeding).

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "postpartumPatientCount": 0,
    "criticalAlertCount": 0,
    "watchAlertCount": 0,
    "maternalAlerts": [
      {
        "patientUserId": "uuid",
        "patientName": "string",
        "dayPostpartum": 0,
        "severity": "string",
        "message": "string",
        "sourceSubmissionId": "uuid | null",
        "createdAt": "datetime"
      }
    ],
    "newbornAlerts": [
      {
        "babyId": "uuid",
        "babyName": "string",
        "motherName": "string",
        "dayOfLife": 0,
        "severity": "string",
        "message": "string",
        "createdAt": "datetime"
      }
    ]
  }
}
```

---

## GET `/postpartum-patients`

Lists active postpartum patient caseloads at the facility — the "postpartum ward" overview list.

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "patientUserId": "uuid",
      "patientName": "string",
      "dayPostpartum": 0,
      "babyName": "string | null",
      "babySex": "string | null",
      "status": "string",
      "assignedClinicianName": "string | null"
    }
  ]
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
