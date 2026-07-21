# Referrals — API Reference (Web Dashboard)

**Base path:** `/api/v1/referrals`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` · 🏢 `X-Facility-Context: <facility_id>` · 🔑 `CLINICIAN` for status-changing actions

> A mother creates and views her own referrals from the mobile app — see [`docs/mobile/referrals-emergencies.md`](../mobile/referrals-emergencies.md) for `POST /` and the `ReferralRead` shape. This doc covers what the receiving/sending facility does with a referral once it exists.

---

## GET `/{referral_id}`

Retrieves a specific referral. Same endpoint mobile uses — any authenticated caller involved in the referral can read it.

---

## GET `/`

Lists referrals with optional filters.

**Query Parameters:** `status` (`PENDING`\|`ACCEPTED`\|`REJECTED`\|`COMPLETED`), `facilityId` (UUID), `direction` (`INCOMING`\|`OUTGOING`, relative to `facilityId`), `page`, `pageSize`

**Response `200 OK`** — array of `ReferralRead` objects, paginated.

---

## GET `/inbox/incoming`

Facility-scoped incoming-referral inbox, pre-formatted for the UI (patient name/age, gestational week, ETA — not just raw `ReferralRead` fields).

**Role required:** `CLINICIAN` · 🏢

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "fromFacilityName": "Malindi Sub County Hospital",
      "toFacilityName": "Current Facility",
      "patientName": "Patience Moraa",
      "patientAge": 32,
      "pregnancyWeek": 38,
      "reason": "Suspected preeclampsia, BP 158/102 on last reading.",
      "requestedAt": "2026-07-08T15:45:00Z",
      "isEmergency": true,
      "status": "PENDING",
      "estimatedArrivalMinutes": 25
    }
  ]
}
```

---

## GET `/inbox/outgoing`

Facility-scoped outgoing-referral inbox — referrals this facility has sent to others, same shape as `GET /inbox/incoming`.

**Role required:** `CLINICIAN` · 🏢

---

## PUT `/{referral_id}/accept`

Accepts a referral. Advances the mobile status tracker from "Facility reviewing your request" to "Accepted — they're preparing for your arrival." Also enables consent-gated data sharing (see `GET /{referral_id}/patient-summary` below).

**Role required:** `CLINICIAN`

**Response `200 OK`** — Updated `ReferralRead`, `status: "ACCEPTED"`.

---

## PUT `/{referral_id}/reject`

Rejects a referral.

**Role required:** `CLINICIAN`

**Request Body**
```json
{ "reason": "No theatre capacity available" }
```

**Response `200 OK`** — Updated `ReferralRead`, `status: "REJECTED"`, `rejection_reason` set.

---

## PUT `/{referral_id}/complete`

Marks a referral as completed (the patient has arrived and been received).

**Role required:** `CLINICIAN`

**Response `200 OK`** — Updated `ReferralRead`, `status: "COMPLETED"`, `completed_at` set.

---

## GET `/{referral_id}/patient-summary`

Returns a condensed clinician-readable "emergency brief" — not the full record. Requires either active consent from the mother or `emergency_sharing_preference: ALWAYS_SHARE` (see `docs/mobile/referrals-emergencies.md`).

**Role required:** `CLINICIAN`

**Response `200 OK`** (consent granted)
```json
{
  "success": true,
  "data": {
    "patient": { "fullName": "Wanjiru Kamau", "age": 24, "bloodType": "O+" },
    "gestationalAgeWeeks": 31,
    "activeRiskFlags": ["REDUCED_FETAL_MOVEMENT"],
    "reasonForVisit": "REDUCED_FETAL_MOVEMENT",
    "recentVitals": { "bloodPressure": "122/80", "lastRecordedAt": "2026-06-29T08:10:00Z" },
    "allergies": [],
    "emergencyContact": { "name": "James Kamau", "phoneNumber": "+254721556002" }
  }
}
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `403` | `CONSENT_REQUIRED` (or `FORBIDDEN`) | Mother has not consented and preference is not `ALWAYS_SHARE` |
| `403` | `FORBIDDEN` | Caller does not have the `CLINICIAN` role |

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
