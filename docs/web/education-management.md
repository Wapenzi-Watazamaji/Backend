# Education & Community Engagement — API Reference (Web Dashboard)

**Base path:** `/api/v1/education`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` · 🔑 `CLINICIAN` or `FACILITY_ADMIN` · 🏢 `X-Facility-Context: <facility_id>`

> Mothers read content/events via [`docs/mobile/education.md`](../mobile/education.md). This doc covers creating and managing that content from the web dashboard.

---

## POST `/content`

Creates a new piece of educational content, scoped to the facility in context.

**Request Body**
```json
{
  "title": "Why hydration matters more during pregnancy",
  "category": "HYDRATION",
  "body": "Full article content goes here...",
  "target_stages": ["PREGNANT", "POSTPARTUM"]
}
```

`category`: `HYDRATION` \| `NUTRITION` \| `EXERCISE` \| `MENTAL_HEALTH` \| `GENERAL`

**Response `201 Created`** — the created `EducationContent` object.

---

## PUT `/content/{id}`

Updates an existing piece of content (all fields optional).

**Request Body**
```json
{
  "title": "Updated title",
  "category": "NUTRITION",
  "body": "Updated body...",
  "target_stages": ["PREGNANT"]
}
```

**Response `200 OK`** — the updated `EducationContent` object.

---

## DELETE `/content/{id}`

**Response `204 No Content`**

---

## POST `/events`

Creates a new community/facility event.

**Request Body**
```json
{
  "title": "Free antenatal screening day",
  "event_date": "2026-07-05T09:00:00Z",
  "description": "Free BP and weight screening for all registered mothers"
}
```

**Response `201 Created`** — the created `EducationEvent` object.

---

## Reading endpoints

`GET /content`, `GET /content/{id}`, `GET /events`, `GET /events/{id}`, and `GET /feed` all work identically to the mobile-side versions documented in `docs/mobile/education.md` — staff can use them too (e.g. to preview content before publishing further edits), just without the write access above.
