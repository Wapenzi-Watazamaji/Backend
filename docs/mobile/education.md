# Education & Community Engagement — API Reference (Mobile / Mother-facing)

**Base path:** `/api/v1/education`
**Authentication:** 🔒 `Authorization: Bearer <access_token>` (role `USER`)

Content and events are created by clinicians/facility admins (see [`docs/web/education-management.md`](../web/education-management.md)) and served here for mothers to read.

---

## GET `/content`

Lists educational content.

**Query Parameters:** `category` (optional filter: `HYDRATION` \| `NUTRITION` \| `EXERCISE` \| `MENTAL_HEALTH` \| `GENERAL`), `skip` (default 0), `limit` (default 100)

**Response `200 OK`** — array of `EducationContent` objects.

---

## GET `/content/{id}`

Fetches a specific piece of educational content.

**Response `200 OK`** — `EducationContent` object.

---

## GET `/events`

Lists upcoming community/facility events.

**Response `200 OK`** — array of `EducationEvent` objects.

---

## GET `/events/{id}`

Fetches a specific event.

**Response `200 OK`** — `EducationEvent` object.

---

## GET `/feed`

Returns a chronological feed combining both content and events — the primary endpoint for the "Timeline"/"Discover" tab.

**Query Parameters:** `filter_type` (`"all"` \| `"content"` \| `"events"`, default `"all"`)

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Feed fetched successfully",
  "data": [
    {
      "type": "EVENT",
      "id": "uuid...",
      "title": "Free antenatal screening day",
      "event_date": "2026-07-05T09:00:00Z",
      "description": "...",
      "created_at": "2026-07-02T10:00:00Z"
    },
    {
      "type": "CONTENT",
      "id": "uuid...",
      "title": "Why hydration matters more during pregnancy",
      "category": "HYDRATION",
      "body": "...",
      "target_stages": ["PREGNANT", "POSTPARTUM"],
      "created_at": "2026-07-01T14:30:00Z"
    }
  ]
}
```

Each item carries a `type` field (`CONTENT` \| `EVENT`) to distinguish the two shapes.
