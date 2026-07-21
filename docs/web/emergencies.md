# Emergency SOS — API Reference (Web Dashboard)

**Base path:** `/api/v1/emergencies`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` · 🏢 `X-Facility-Context: <facility_id>` · 🔑 `CLINICIAN` or `FACILITY_ADMIN`

> A mother triggers an emergency and views her own history from the mobile app — see [`docs/mobile/referrals-emergencies.md`](../mobile/referrals-emergencies.md) for `POST /` and `GET /my-requests`.

---

## GET `/inbox`

Fetches all incoming patient SOS alerts directed to the authenticated facility.

**Role required:** `CLINICIAN` or `FACILITY_ADMIN` · 🏢

**Response `200 OK`** — array of `EmergencyRequestRead` objects.

---

## PUT `/{emergency_id}`

Updates the status of an emergency (e.g. once an ambulance is dispatched, or once resolved).

**Role required:** `CLINICIAN` or `FACILITY_ADMIN` · 🏢

**Request Body**
```json
{ "status": "DISPATCHED" }
```

`status`: `PENDING` \| `DISPATCHED` \| `RESOLVED` \| `FALSE_ALARM`

**Response `200 OK`** — Updated `EmergencyRequestRead` object.

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
