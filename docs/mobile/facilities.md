# Facilities Module — API Reference (Mobile / Mother-facing)

**Base path:** `/api/v1/facilities`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` (role `USER`)

> Facility **registration** and **management** (staff roster, patient assignment, readiness stats) are done from the web dashboard — see [`docs/web/facilities.md`](../web/facilities.md). This doc only covers what the mobile app needs: browsing and searching for facilities.

---

## GET `/`

Fetch a list of all facilities. Used to populate a facility picker (e.g. when setting `preferred_facility_id` on the profile).

**Query Parameters**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `search` | string | ❌ | Optional search term to filter facilities by name |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Facilities fetched successfully",
  "data": [
    {
      "id": "fac-uuid",
      "name": "Nairobi Hospital",
      "type": "PRIVATE",
      "county": "Nairobi",
      "address": "Argwings Kodhek Rd",
      "phone_number": "+254700000001",
      "email": "info@nairobihospital.org",
      "latitude": -1.2921,
      "longitude": 36.8219,
      "status": "VERIFIED",
      "is_active": true,
      "services_offered": ["ANTENATAL_CARE", "DELIVERY"],
      "readiness": {},
      "updated_at": "2026-07-01T12:00:00Z"
    }
  ],
  "meta": {}
}
```

---

## GET `/{facility_id}`

Retrieve the details of a specific facility by its UUID — e.g. a facility detail screen.

**Path Parameters**
- `facility_id` (uuid): The ID of the facility to fetch.

**Response `200 OK`** — same `FacilityRead` shape as `GET /`.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Facility does not exist |

---

## GET `/nearby`

Finds all active facilities within a specified radius of the mother's current coordinates, using straight-line (Haversine) distance. Results are ordered closest-first. Facilities without coordinates set are excluded. This is what powers the "find care near me" / emergency facility picker.

**Query Parameters**

| Parameter | Type | Required | Default | Notes |
|---|---|---|---|---|
| `lat` | float | ✅ | | Latitude of the patient/user |
| `lng` | float | ✅ | | Longitude of the patient/user |
| `radius_km` | float | ❌ | `50.0` | Maximum search radius in kilometers |
| `limit` | int | ❌ | `20` | Max number of results to return |

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Nearby facilities fetched successfully",
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Nairobi Hospital",
      "type": "PRIVATE",
      "county": "Nairobi",
      "address": "Argwings Kodhek Rd",
      "phone_number": "+254700000001",
      "email": "info@nairobihospital.org",
      "latitude": -1.295,
      "longitude": 36.805,
      "status": "VERIFIED",
      "is_active": true,
      "services_offered": ["ANTENATAL_CARE", "DELIVERY"],
      "readiness": {},
      "updated_at": "2026-07-01T12:00:00Z",
      "distance_km": 2.45
    }
  ],
  "meta": {}
}
```

**Note:** unlike the rest of this module, `nearby` is not restricted from any particular role — clinicians could call it too — but in practice it's a mobile "find care" feature, which is why it's documented here.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| `422` | `VALIDATION_ERROR` | `lat`/`lng` missing or not numeric |

---

## Enum Reference

| Enum | Values |
|---|---|
| `facility.type` | `PUBLIC`, `PRIVATE`, `MISSION`, `NGO` |
| `facility.status` | `PENDING_VERIFICATION`, `VERIFIED`, `SUSPENDED` *(read-only)* |
