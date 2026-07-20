# Reports — API Reference (Web Dashboard)

**Base path:** `/api/v1/reports`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` · 🔑 `CLINICIAN` · 🏢 `X-Facility-Context: <facility_id>`

---

## GET `/population-snapshot`

Returns an aggregated snapshot of the facility's patient population — pregnancy risk distribution, ANC attendance, referral volume.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "facilityId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "periodStart": "2026-06-01",
    "periodEnd": "2026-07-01",
    "ancAttendanceRate": [{ "week": "2026-W26", "rate": 0.82 }],
    "topRiskFlags": [{ "flag": "REDUCED_FETAL_MOVEMENT", "count": 6 }],
    "referralVolumeByMonth": [{ "month": "2026-06", "count": 4 }],
    "totals": { "totalPatients": 120, "activePregnancies": 34 }
  }
}
```

`ancAttendanceRate`, `topRiskFlags`, `referralVolumeByMonth`, and `totals` are free-form arrays/objects — shape may evolve; treat as opaque chart-ready data rather than a fixed contract.

---

## POST `/`

Requests generation of a downloadable report.

**Request Body**
```json
{
  "type": "MONTHLY_FACILITY_SUMMARY",
  "format": "PDF",
  "dateRangeStart": "2026-06-01",
  "dateRangeEnd": "2026-07-01"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | enum | ✅ | `MONTHLY_FACILITY_SUMMARY` \| `ANC_ATTENDANCE` \| `REFERRAL_ACTIVITY` \| `RISK_FLAG_SUMMARY` \| `MOH_RMNCAH_SUBMISSION` |
| `format` | enum | ✅ | `PDF` \| `CSV` \| `EXCEL` |
| `dateRangeStart` | date | ❌ | |
| `dateRangeEnd` | date | ❌ | |

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "facility_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
    "type": "MONTHLY_FACILITY_SUMMARY",
    "date_range_start": "2026-06-01",
    "date_range_end": "2026-07-01",
    "format": "PDF",
    "status": "GENERATING",
    "file_url": null,
    "generated_at": null,
    "created_at": "2026-07-10T08:00:00Z"
  }
}
```

`status`: `GENERATING` \| `READY` \| `FAILED`. Generation is asynchronous — poll `GET /` or `GET /{report_id}/download` until `status: "READY"`.

---

## GET `/`

Lists past generated reports for the facility.

**Query Parameters:** `limit` (default 20), `offset` (default 0)

**Response `200 OK`** — array of `ReportRead` objects (same shape as the `POST /` response).

---

## GET `/{report_id}/download`

Retrieves the download URL for a completed report.

**Response `200 OK`**
```json
{ "success": true, "data": { "downloadUrl": "https://..." } }
```

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Report doesn't exist, or isn't `READY` yet |

---

## Enum Reference

| Enum | Values |
|---|---|
| `ReportType` | `MONTHLY_FACILITY_SUMMARY`, `ANC_ATTENDANCE`, `REFERRAL_ACTIVITY`, `RISK_FLAG_SUMMARY`, `MOH_RMNCAH_SUBMISSION` |
| `ReportFormat` | `PDF`, `CSV`, `EXCEL` |
| `ReportStatus` | `GENERATING`, `READY`, `FAILED` |
