# System Templates Module — API Reference (Web Dashboard)

**Base path:** `/api/v1/templates`
**Authentication:** All endpoints require a valid Bearer token 🔒. `GET` endpoints work for any authenticated role; creating/updating a form template requires `FACILITY_ADMIN` + `X-Facility-Context` (🏢).

> The mobile app never calls this generic listing endpoint directly — it fetches the active template for a specific form via each module's own `.../form-template` endpoint (e.g. `GET /pregnancy/vitals/form-template`, see `docs/mobile/pregnancy.md`), which already resolves the facility-specific override vs. platform default for the current patient. This module is the admin tooling behind that resolution: where facility-specific overrides are configured.

---

## GET `/forms` 🔒

Fetches all active Form Templates from the database. Form Templates define the dynamic schema for forms across various modules (e.g., Pregnancy Vitals, Cycle Entries).

**Query Parameters**
- `context` (string, optional): Filter templates by context (e.g., `PREGNANCY_VITALS`, `CYCLE_ENTRY`).

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "e6f423ab-2423-4411-9a7e-12822a1f434a",
      "slug": "tmpl_cycle_entry_v1",
      "context": "CYCLE_ENTRY",
      "fields": { "flowLevel": { "type": "select", "options": ["LIGHT", "MODERATE", "HEAVY"] } },
      "version": "v1",
      "is_active": true,
      "facility_id": null,
      "created_at": "2026-07-01T07:05:37Z"
    }
  ],
  "meta": {}
}
```

---

## GET `/care-pathways` 🔒

Fetches all Care Pathway Templates from the database. Care Pathways define the standard scheduled visits and milestones for patient journeys (e.g., MOH Antenatal Care, MOH Postnatal Care).

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "moh_pregnancy",
      "name": "MOH Standard ANC Schedule",
      "description": "Standard 4-visit ANC schedule",
      "milestones": [
        { "name": "ANC 1", "weeks_pregnant": 16 },
        { "name": "ANC 2", "weeks_pregnant": 24 }
      ],
      "is_active": true,
      "created_at": "2026-07-01T07:05:37Z"
    }
  ],
  "meta": {}
}
```

---

## POST `/forms` 🏢

Creates a new form template for the active facility.

**Authentication:**
- 🔒 Authorization: Bearer <access_token>
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body**
```json
{
  "slug": "tmpl_cycle_entry_v1",
  "context": "CYCLE_ENTRY",
  "fields": {
    "flowLevel": { "type": "select", "options": ["LIGHT", "MODERATE", "HEAVY"] }
  },
  "version": "v1",
  "is_active": true
}
```

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Form template created successfully",
  "data": {
    "id": "e6f423ab-2423-4411-9a7e-12822a1f434a",
    "slug": "tmpl_cycle_entry_v1",
    "context": "CYCLE_ENTRY",
    "fields": { "flowLevel": { "type": "select", "options": ["LIGHT", "MODERATE", "HEAVY"] } },
    "version": "v1",
    "is_active": true,
    "facility_id": "a90100a0-6644-4363-9517-f570e3cb27f8",
    "created_at": "2026-07-01T07:05:37Z"
  },
  "meta": {}
}
```

---

## PUT `/forms/{template_id}` 🏢

Updates an existing form template belonging to the active facility.

**Authentication:**
- 🔒 Authorization: Bearer <access_token>
- 🔑 Required Role: `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body (All fields optional)**
```json
{
  "is_active": false,
  "fields": {
    "flowLevel": { "type": "select", "options": ["NONE", "LIGHT", "MODERATE", "HEAVY"] }
  }
}
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Form template updated successfully",
  "data": {
    "id": "e6f423ab-2423-4411-9a7e-12822a1f434a",
    "slug": "tmpl_cycle_entry_v1",
    "context": "CYCLE_ENTRY",
    "fields": { "flowLevel": { "type": "select", "options": ["NONE", "LIGHT", "MODERATE", "HEAVY"] } },
    "version": "v1",
    "is_active": false,
    "facility_id": "a90100a0-6644-4363-9517-f570e3cb27f8",
    "created_at": "2026-07-01T07:05:37Z"
  },
  "meta": {}
}
```
