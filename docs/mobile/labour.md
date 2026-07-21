# Labour & Birth Monitor Module — API Reference (Mobile / Mother-facing)

**Base path:** `/api/v1/labour`
**Authentication:** All endpoints require a valid Bearer token 🔒 (role `USER`)

By design, detailed labour monitoring (logging readings, managing alerts, the partograph write-side) happens on the **web dashboard** — see [`docs/web/labour.md`](../web/labour.md). The mobile app only gets a simplified, **read-only** status view: whether labour is active, the partograph chart, and any alerts raised. A labour session itself is opened by a clinician (`POST /sessions`, web-side), not by the mother.

---

## GET `/sessions/{session_id}`

Retrieves a specific labour session's status.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "7719e249-c628-4b33-9511-b6a0fdd75310",
    "pregnancy_id": "800eb70b-4e2a-45d5-8ddc-43e7127dcdb3",
    "facility_id": "b071e013-9e82-4143-bca1-2b15ac6498c9",
    "clinician_id": "f1571b88-0d48-4e88-800c-87bfa0249c81",
    "status": "ACTIVE",
    "outcome": null,
    "delivery_type": null,
    "active_labour_started_at": "2026-07-03T08:00:00Z",
    "closed_at": null,
    "created_at": "2026-07-03T08:00:00Z",
    "updated_at": "2026-07-03T08:00:00Z"
  }
}
```

`status`: `ACTIVE` \| `CLOSED`.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Labour session does not exist |

---

## GET `/sessions/{session_id}/partograph`

Retrieves the computed partograph data points, alert lines, and action lines — for a simplified progress visualization in the app (not a clinical charting tool; that's the web dashboard's job).

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "dilationReadings": [
      { "hoursElapsed": 0.0, "value": 4.0, "recordedAt": "2026-07-03T08:00:00Z" }
    ],
    "fhrReadings": [
      { "hoursElapsed": 0.0, "value": 152.0, "recordedAt": "2026-07-03T08:00:00Z" }
    ],
    "alertLine":  { "startHour": 0, "startCm": 4.0, "slopeCmPerHour": 1.0 },
    "actionLine": { "startHour": 4, "startCm": 4.0, "slopeCmPerHour": 1.0 },
    "hasAlertLineCrossed": false,
    "hasActionLineCrossed": false
  }
}
```

---

## GET `/sessions/{session_id}/alerts`

Lists all auto-generated clinical alerts for the labour session.

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "96ed30ff-c54c-477f-86f6-21daad1ed9b1",
      "session_id": "7719e249-c628-4b33-9511-b6a0fdd75310",
      "type": "ACTION_LINE_CROSSED",
      "severity": "CRITICAL",
      "message": "Labour progress is now 4 hours behind the expected rate",
      "acknowledged_at": null,
      "acknowledged_by": null,
      "escalated_to": null,
      "created_at": "2026-07-03T13:00:00Z"
    }
  ]
}
```

`type`: `ACTION_LINE_CROSSED` \| `FETAL_DISTRESS` \| `PPH_RISK` \| `PREECLAMPSIA_RISK` \| `SEPSIS_RISK`. `severity`: `CRITICAL` \| `WARNING`. Acknowledging/escalating alerts is a clinician action — see `docs/web/labour.md`.

**Errors**

| Status | Code | Trigger |
|---|---|---|
| `404` | `NOT_FOUND` | Labour session does not exist |

---

## GET `/resuscitation-protocol`

Retrieves the WHO neonatal resuscitation protocol steps (reference content, not scoped to any session).

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "steps": [
      { "order": 1, "title": "Dry, warm, and position the baby", "timerSeconds": null, "instructions": null }
    ]
  }
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
