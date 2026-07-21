# API Conventions

Shared conventions that apply across every module, regardless of whether the caller is the mobile app (mother) or the web dashboard (clinician / facility admin).

**Base URL:** `/api/v1` — every path in every doc under `docs/mobile/`, `docs/web/`, and `docs/shared/` is relative to this prefix. For example "`POST /register`" documented under `auth.md` really means `POST /api/v1/auth/register`.

**Protocol:** REST over HTTPS. Real-time features (AI chat, live facility notifications) use WebSockets under the same host.

---

## Authentication

Unless explicitly marked public, every endpoint requires:

```
Authorization: Bearer <access_token>
```

Tokens are issued by `POST /auth/login` (see `shared/auth.md`) and carry a `role` claim: `USER` (mother), `CLINICIAN`, or `FACILITY_ADMIN`.

Web-dashboard endpoints (anything under `docs/web/`) additionally require:

```
X-Facility-Context: <facility_id>
```

...the UUID of a facility the caller is an **active** staff member of. Missing, invalid, or non-membership values return `403 FORBIDDEN`. Mobile endpoints never require this header.

## Response Envelope

All responses follow this shape:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { },
  "meta": { },
  "error": null
}
```

On failure:

```json
{
  "success": false,
  "message": "Detailed error message",
  "data": null,
  "meta": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Detailed error message",
    "fields": { "phoneNumber": "Already in use" }
  }
}
```

`fields` is only present on validation errors that map to specific request fields. `message` is always present (defaults to `"Operation successful"` on success).

## Pagination

List endpoints that support paging accept `page` / `pageSize` query parameters and return:

```json
{
  "page": 1,
  "pageSize": 20,
  "total": 134,
  "totalPages": 7
}
```

in `meta`. Not every list endpoint paginates — check the individual module doc.

## Timestamps

All timestamps are ISO 8601 UTC strings, e.g. `"2026-07-18T08:30:00Z"`.

## Offline Sync Fields

Some `POST` endpoints that create a record accept an optional `clientGeneratedId` and `clientCreatedAt`, used by the mobile app to log entries while offline and sync later without duplicating records. This is **not universal** — it currently appears on cycle entries/symptoms, pregnancy vitals, and postpartum check-ins/vitals only. Check the individual endpoint before relying on it.

## Common Error Codes

| Status | Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Field-level validation failure — see `error.fields` |
| 401 | `UNAUTHORIZED` | Missing, expired, or invalid access token |
| 401 | `INVALID_CREDENTIALS` | Login phone/password mismatch |
| 403 | `FORBIDDEN` | Authenticated but lacks permission (wrong role, or not a staff member of the facility in `X-Facility-Context`) |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `PHONE_ALREADY_REGISTERED` / `CONFLICT` | Unique-constraint violation |
| 422 | `VALIDATION_ERROR` | Pydantic-level schema validation failure |

## Roles

| Role | Who | App |
|---|---|---|
| `USER` | The pregnant/postpartum/cycle-tracking mother | Mobile app |
| `CLINICIAN` | Doctor/nurse/midwife at a registered facility | Web dashboard |
| `FACILITY_ADMIN` | Manages a facility's staff, patients, and settings | Web dashboard |

An account can hold staff membership at a facility (`CLINICIAN`/`FACILITY_ADMIN`) via the `StaffMember` join — see `shared/auth.md` for how `staff_memberships` surfaces at login.

---

## Where to look next

- **Building the mobile (mother-facing) app?** Start at `docs/mobile/README.md`.
- **Building the web dashboard (clinician / facility admin)?** Start at `docs/web/README.md`.
- Both apps share login/registration — see `docs/shared/auth.md`.
