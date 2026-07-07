# Education & Community Engagement API

This module handles the distribution of educational content and the scheduling of community events by clinicians and facility administrators. Content and events are specific to a facility and are served directly to the mothers.

---

## Content Management

### POST `/api/v1/education/content`

Creates a new piece of educational content.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `CLINICIAN` or `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body**
```json
{
  "title": "Why hydration matters more during pregnancy",
  "category": "HYDRATION",
  "body": "Full article content goes here...",
  "target_stages": ["PREGNANT", "POSTPARTUM"]
}
```
*Note: `category` can be `HYDRATION`, `NUTRITION`, `EXERCISE`, `MENTAL_HEALTH`, or `GENERAL`.*

**Response `201 Created`**
Returns the created `EducationContent` object.

---

### GET `/api/v1/education/content`

Lists educational content for the facility.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Query Parameters (Optional):**
- `category`: Filter by a specific category (e.g. `HYDRATION`)
- `skip`: Pagination offset (default: 0)
- `limit`: Pagination limit (default: 100)

**Response `200 OK`**
Returns an array of `EducationContent` objects.

---

### GET `/api/v1/education/content/{id}`

Fetches a specific piece of educational content.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`

**Response `200 OK`**
Returns the specific `EducationContent` object.

---

### PUT `/api/v1/education/content/{id}`

Updates an existing piece of educational content.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `CLINICIAN` or `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body (All fields optional)**
```json
{
  "title": "Updated title",
  "category": "NUTRITION",
  "body": "Updated body...",
  "target_stages": ["PREGNANT"]
}
```

**Response `200 OK`**
Returns the updated `EducationContent` object.

---

### DELETE `/api/v1/education/content/{id}`

Deletes a specific piece of educational content.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `CLINICIAN` or `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `204 No Content`**
Returns empty body on success.

---

## Events Management

### POST `/api/v1/education/events`

Creates a new community or facility event.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🔑 Required Role: `CLINICIAN` or `FACILITY_ADMIN`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Request Body**
```json
{
  "title": "Free antenatal screening day",
  "event_date": "2026-07-05T09:00:00Z",
  "description": "Free BP and weight screening for all registered mothers"
}
```

**Response `201 Created`**
Returns the created `EducationEvent` object.

---

### GET `/api/v1/education/events`

Lists upcoming events for the facility.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Response `200 OK`**
Returns an array of `EducationEvent` objects.

---

### GET `/api/v1/education/events/{id}`

Fetches a specific event.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`

**Response `200 OK`**
Returns the specific `EducationEvent` object.

---

## The Feed

### GET `/api/v1/education/feed`

Returns a chronological feed combining both `EducationContent` and `EducationEvent` entities. This is the primary endpoint the frontend should use to build the "Timeline" or "Discover" tab for mothers.

**Authentication:** 
- 🔒 `Authorization: Bearer <access_token>`
- 🏢 Header: `X-Facility-Context: <facility_id>`

**Query Parameters (Optional):**
- `filter_type`: Can be `"all"`, `"content"`, or `"events"` (default: `"all"`). Controls what types of items are returned in the timeline.

**Response `200 OK`**
Returns an array of mixed objects. Each object contains a `type` field to distinguish between content and events.

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
