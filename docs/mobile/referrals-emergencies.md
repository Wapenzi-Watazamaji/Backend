# Referrals & Emergency SOS — API Reference (Mobile / Mother-facing)

**Base paths:** `/api/v1/referrals`, `/api/v1/emergencies`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` (role `USER`)

These are two related but separate resources: a **Referral** is a facility-to-facility transfer request (`toFacilityId`/`fromFacilityId`) that a mother can also initiate herself (e.g. "I need to go to a different facility"), while an **Emergency Request** is a lighter-weight patient-initiated SOS aimed at a single facility with just a location and a note. Both can be flagged urgent; a `Referral` additionally supports `isEmergency: true` for a facility-routed emergency transfer.

> Accepting/rejecting/completing a referral, the facility's referral inbox, and the facility's emergency inbox are clinician/facility-admin actions — see [`docs/web/referrals.md`](../web/referrals.md) and [`docs/web/emergencies.md`](../web/emergencies.md).

---

## Referrals (`/api/v1/referrals`)

### POST `/`

Creates a referral or emergency transfer request.

**Request Body**
```json
{
  "toFacilityId": "b071e013-9e82-4143-bca1-2b15ac6498c9",
  "fromFacilityId": "a90100a0-6644-4363-9517-f570e3cb27f8",
  "reason": "REDUCED_FETAL_MOVEMENT",
  "notes": "Patient reports significantly reduced movement since this morning",
  "isEmergency": true,
  "offlineQueued": false,
  "clientCreatedAt": "2026-07-03T08:00:00Z"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `toFacilityId` | UUID | ✅ | Destination facility |
| `fromFacilityId` | UUID | ✅ | Origin facility (typically the mother's preferred/current facility) |
| `reason` | enum | ✅ | `HEAVY_BLEEDING` \| `SEVERE_PAIN` \| `REDUCED_FETAL_MOVEMENT` \| `LABOUR_STARTED` \| `SOMETHING_FEELS_WRONG` \| `ROUTINE_TRANSFER` \| `SPECIALIST_REFERRAL` |
| `notes` | string | ❌ | Free-text context |
| `isEmergency` | boolean | ❌ | Default `false` |
| `offlineQueued` | boolean | ❌ | Default `false` — set `true` if this request was created while offline and is being sent now that connectivity returned |
| `clientCreatedAt` | datetime | ❌ | The true creation time, if `offlineQueued` |

**Response `201 Created`**
```json
{
  "success": true,
  "data": {
    "id": "ref_4471",
    "patient_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
    "to_facility_id": "b071e013-9e82-4143-bca1-2b15ac6498c9",
    "from_facility_id": "a90100a0-6644-4363-9517-f570e3cb27f8",
    "reason": "REDUCED_FETAL_MOVEMENT",
    "notes": "Patient reports significantly reduced movement since this morning",
    "is_emergency": true,
    "status": "PENDING",
    "rejection_reason": null,
    "completed_at": null,
    "created_at": "2026-07-03T08:00:00Z",
    "updated_at": "2026-07-03T08:00:00Z"
  }
}
```

`status`: `PENDING` \| `ACCEPTED` \| `REJECTED` \| `COMPLETED` — advanced by the receiving facility (see `docs/web/referrals.md`).

---

### GET `/{referral_id}`

Retrieves a specific referral (mother can view her own).

**Response `200 OK`** — `ReferralRead` object (same shape as the `POST /` response).

---

### GET `/`

Lists referrals with optional filters.

**Query Parameters:** `status` (enum), `facilityId` (UUID), `direction` (`INCOMING`\|`OUTGOING`, relative to a facility — mostly a web-side concept), `page` (default 1), `pageSize` (default 20)

**Response `200 OK`** — array of `ReferralRead` objects.

---

## Emergency SOS (`/api/v1/emergencies`)

### POST `/`

Triggers an emergency alert routed to a single facility (typically the mother's preferred facility).

**Request Body**
```json
{
  "facility_id": "b071e013-9e82-4143-bca1-2b15ac6498c9",
  "location_lat": "-1.2833",
  "location_lng": "36.8167",
  "notes": "Severe abdominal pain"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `facility_id` | UUID | ✅ | |
| `location_lat` | string | ❌ | |
| `location_lng` | string | ❌ | |
| `notes` | string | ❌ | |

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Emergency request created successfully",
  "data": {
    "id": "uuid",
    "patient_id": "uuid",
    "facility_id": "uuid",
    "status": "PENDING",
    "location_lat": "-1.2833",
    "location_lng": "36.8167",
    "notes": "Severe abdominal pain",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

**Side effect:** if the mother has an emergency contact configured on her profile, an SMS notification is automatically sent to them — see `docs/web/notifications-system.md`.

---

### GET `/my-requests`

Fetches the mother's own emergency request history.

**Response `200 OK`** — array of `EmergencyRequestRead` objects.

---

## Consent — sharing your records with a facility

Whether an accepted referral or emergency actually grants the receiving facility access to the mother's full record depends on her `emergency_sharing_preference` (set via `PUT /profile/me` — see `docs/mobile/profile.md`):

| Preference | Behavior |
|---|---|
| `ALWAYS_SHARE` | The facility's access request is auto-approved |
| `NEVER_SHARE` | The facility is hard-blocked; only the referral/emergency `notes` field is visible to them |
| `ASK_FIRST` (default) | The mother must explicitly approve access — the facility's request shows as pending until she does |

The mother can revoke a facility's standing access at any time via `PUT /profile/me/consents/{grantee_id}/revoke` — see `docs/mobile/profile.md`. Revocation is immediate and blocks all future access by that facility.

---

## Enum Reference

| Enum | Values |
|---|---|
| `Referral.reason` | `HEAVY_BLEEDING`, `SEVERE_PAIN`, `REDUCED_FETAL_MOVEMENT`, `LABOUR_STARTED`, `SOMETHING_FEELS_WRONG`, `ROUTINE_TRANSFER`, `SPECIALIST_REFERRAL` |
| `Referral.status` | `PENDING`, `ACCEPTED`, `REJECTED`, `COMPLETED` |
| `EmergencyRequest.status` | `PENDING`, `DISPATCHED`, `RESOLVED`, `FALSE_ALARM` |
| `Profile.emergency_sharing_preference` | `ASK_FIRST`, `ALWAYS_SHARE`, `NEVER_SHARE` |

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
