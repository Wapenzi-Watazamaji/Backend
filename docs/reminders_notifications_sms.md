# Reminders, Notifications & SMS Module — API Reference

This module covers custom reminders management, device token registry, SMS preferences, and inbound webhooks.

## Base Paths:
* Reminders API: `/api/v1/reminders`
* Devices & Notifications API: `/api/v1/devices` / `/api/v1/notifications`

**Authentication:** Most endpoints require 🔒 `Authorization: Bearer <access_token>` (except inbound SMS webhook and template SMS send).

---

## 1. Reminders Endpoints (`/api/v1/reminders`)

### POST `/`
Creates a custom user reminder (e.g. pills, blood pressure check).

**Request Body**
```json
{
  "title": "Take folic acid",
  "type": "MEDICATION",
  "dueAt": "2026-07-15T08:00:00Z"
}
```

**Response `201 Created`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "userId": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "title": "Take folic acid",
    "type": "MEDICATION",
    "dueAt": "2026-07-15T08:00:00Z",
    "isDone": false,
    "createdAt": "2026-07-13T10:00:00Z",
    "updatedAt": "2026-07-13T10:00:00Z"
  },
  "meta": {}
}
```

---

### GET `/`
Lists reminders for the authenticated user.

**Query Parameters**
* `upcomingOnly` (boolean, optional): Filter only incomplete upcoming reminders.
* `reminderType` (string, optional): Filter by type (`MEDICATION`, `APPOINTMENT`, `CYCLE`, `VACCINATION`, `OTHER`).

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": [
    {
      "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "title": "Take folic acid",
      "type": "MEDICATION",
      "dueAt": "2026-07-15T08:00:00Z",
      "isDone": false
    }
  ]
}
```

---

### PUT `/`
Updates a custom reminder.

**Request Body**
```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "title": "Take folic acid (morning)",
  "dueAt": "2026-07-15T07:30:00Z"
}
```

---

### PUT `/{id}/done`
Marks a reminder as completed.

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "isDone": true
  }
}
```

---

### DELETE `/{id}`
Deletes a reminder.

**Response `204 No Content`**

---

## 2. Devices & Push Notification Endpoints

### POST `/api/v1/devices/register`
Registers a mobile device FCM token to receive real-time push alerts.

**Request Body**
```json
{
  "deviceToken": "fcm_token_12345abcdef",
  "platform": "ANDROID"
}
```
*`platform` values:* `ANDROID`, `IOS`, `WEB`

**Response `201 Created`**
```json
{
  "success": true,
  "data": {
    "tokenId": "5e8e8e8e-5717-4562-b3fc-2c963f66afa6"
  }
}
```

---

### DELETE `/api/v1/devices/{tokenId}`
Unregisters a push token.

**Response `204 No Content`**

---

## 3. In-App Notifications History

### GET `/api/v1/notifications`
Retrieves in-app notifications inbox list.

**Query Parameters**
* `unreadOnly` (boolean, optional): Default `false`. Filter read status.
* `pageSize` (integer, default `20`).
* `page` (integer, default `1`).

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "f5f5f5f5-f5f5-f5f5-f5f5-f5f5f5f5f5f5",
      "userId": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "category": "APPOINTMENT_REMINDER",
      "title": "Upcoming Visit Reminder",
      "body": "Hi Jane, you have a scheduled visit at Karen Health Center tomorrow.",
      "isRead": false,
      "relatedEntityType": "SCHEDULED_VISIT",
      "relatedEntityId": "a2a2a2a2-a2a2-a2a2-a2a2-a2a2a2a2a2a2",
      "createdAt": "2026-07-13T08:00:00Z"
    }
  ]
}
```

---

### PUT `/api/v1/notifications/{id}/read`
Marks an inbox notification as read.

**Response `200 OK`**

---

## 4. SMS & User Preferences

### GET `/api/v1/notifications/sms/preferences`
Retrieves the user's preferred notification channel. 
If the user doesn't have a profile yet, one is automatically bootstrapped.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "contactPreference": "BOTH"
  }
}
```
*`contactPreference` values:* `SMS`, `APP_NOTIFICATIONS`, `BOTH`

---

### PUT `/api/v1/notifications/sms/preferences`
Updates the notification channel preference.

**Request Body**
```json
{
  "contactPreference": "SMS"
}
```

---

## 5. Webhook and Internal APIs

### POST `/api/v1/notifications/sms/send` (Internal)
Sends a templated SMS. Used by system components/workers.

**Request Body**
```json
{
  "toPhoneNumber": "+254712345678",
  "templateId": "appointment_reminder",
  "variables": {
    "motherName": "Jane Doe",
    "facilityName": "Karen Health Center",
    "appointmentDate": "2026-07-14 09:00"
  }
}
```

---

### POST `/api/v1/notifications/sms/inbound-webhook` (Public)
Webhook endpoint to receive replies from Africa's Talking. 

**Behavior 1: Check-in Reminders Replies**
Processes check-in response numbers (e.g. `1` or `2`) and completes cycle or maternal reminders.
*   **Request Body:**
    ```json
    {
      "from": "+254712345678",
      "text": "1",
      "linkedReminderId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
    }
    ```

**Behavior 2: Offline SMS Vitals Logging**
If the message starts with `"vitals"` (case-insensitive), it extracts the blood pressure reading and weight using regular expressions, creates a `FormSubmission` (PREGNANCY_VITALS context) and a `PregnancyVitalsEntry`, runs risk calculation, and sends a confirmation SMS back to the patient.
*   **Command syntax:** `vitals <systolic_bp>/<diastolic_bp> <weight_kg>`
*   **Example text:** `"vitals bp 130/85 weight 74.5"` or `"vitals 130/85 74"`
*   **Request Body:**
    ```json
    {
      "from": "+254712345678",
      "text": "vitals bp 130/85 weight 74.5"
    }
    ```

**Behavior 3: Offline Clinic Listing & Registration**
Allows patients to query available health facilities and register with their choice:
*   **`GET FACILITIES [county]`**: Returns up to 5 facilities, including their names, counties, and short IDs.
    *   *SMS text:* `"get facilities nairobi"` or `"get facilities"`
*   **`REGISTER FACILITY <name_or_id>`**: Sets their preferred facility in their Profile.
    *   *SMS text:* `"register facility Test Facility West"`
*   **`REQUEST DOCTOR`**: Assigns the first available clinician at their preferred clinic, or queues it if pending, sending confirmations to both patient and clinician.
    *   *SMS text:* `"request doctor"`
*   **Request Body Example:**
    ```json
    {
      "from": "+254712345678",
      "text": "request doctor"
    }
    ```

---

## 6. Clinician & Facility Admin SMS Alerts

Since clinicians and facility admins access BintiCare through the Web Application rather than a mobile app, critical real-time alerts are sent to their registered mobile numbers via SMS (and logged in the web dashboard's inbox):

1.  **Patient Doctor Assignment:** Dispatches an SMS alert when a patient registers or is assigned to them by a clinic administrator.
2.  **Danger Signs Detected:** Dispatches an SMS immediately when an assigned patient submits daily vitals that contain flagged danger signs, so the clinician can follow up right away.
3.  **Emergency Broadcasts:** Broadcasts a critical emergency SMS to all registered clinic clinicians and admins when a mother requests urgent emergency assistance at their facility.

---

## 7. Real-Time WebSockets Channel (`ws://.../api/v1/notifications/ws/{user_id}`)

Allows web clients (like the Clinician Web App) to listen to a persistent WebSocket pipe for immediate, non-blocking notification alerts (enabling custom frontend warning cards and audio alert chimes).

*   **URL Scheme:** `ws://[hostname]/api/v1/notifications/ws/{user_id}`
*   **Path Parameters:**
    *   `user_id` (UUID, required): The ID of the authenticated clinician, admin, or user.
*   **Response Payload (JSON):**
    ```json
    {
      "id": "e4f8b9d3-6e42-4f3b-8d1a-4c2b9a1d8e5f",
      "userId": "d2a6b3f7-9c8e-4a1d-8f2b-9e4a3b1d7f6c",
      "category": "EMERGENCY_ALERT",
      "title": "Emergency Assistance Requested",
      "body": "CRITICAL EMERGENCY: Patient Jane Doe has requested emergency assistance. Notes: Severe labor pain. Phone: +254712345678.",
      "isRead": false,
      "relatedEntityType": "EMERGENCY_REQUEST",
      "relatedEntityId": "f7a6b2c8-9d4e-4a3b-8f1a-2c9b6a1d8e5f",
      "createdAt": "2026-07-13T08:35:00Z"
    }
    ```


