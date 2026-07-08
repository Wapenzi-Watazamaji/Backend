# Web-Side Management API Documentation

This document outlines the endpoints, request/response bodies, and headers added for the Web-Side Management dashboard.

## Global Headers
All endpoints require authentication using a Bearer token.
- `Authorization: Bearer <token>`
- `X-Facility-Context: <facility_uuid>`

---

## 1. Dashboard Routes
**Base Path:** `/dashboard`

### 1.1 Get Dashboard Summary
Aggregates statistics for a specific clinician and facility.

**Endpoint:** `GET /dashboard/summary`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query
- `target_date` (date, optional, default: today)

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  {
    "assignedPatientCount": 0,
    "assignedPatientCountDeltaThisWeek": 0,
    "activeAlertCount": 0,
    "ancVisitsToday": 0,
    "ancVisitsCompletedToday": 0,
    "pendingReferralCount": 0
  }
}
```

### 1.2 Get Unified Alerts
Retrieves a unified feed of active alerts (Labour and Postpartum) for the facility.

**Endpoint:** `GET /dashboard/alerts`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  [
    {
      "id": "uuid",
      "patientUserId": "uuid",
      "patientName": "string",
      "type": "LABOUR | POSTPARTUM",
      "severity": "CRITICAL | WARNING | NORMAL",
      "message": "string",
      "sourceSubmissionId": "uuid | null",
      "createdAt": "datetime",
      "acknowledgedAt": "datetime | null"
    }
  ]
}
```

### 1.3 Get Patient Directory
Lists patients assigned to the facility, with optional search.

**Endpoint:** `GET /dashboard/directory`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query
- `search` (string, optional)

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  [
    {
      "userId": "uuid",
      "fullName": "string",
      "age": 0,
      "patientCode": "string",
      "phoneNumber": "string",
      "stage": "string",
      "stageDetail": "string",
      "riskLevel": "string",
      "assignedClinicianName": "string",
      "lastActivityAt": "datetime | null",
      "preferredFacilityName": "string"
    }
  ]
}
```

### 1.4 Get Global Timeline
Gets a unified timeline of recent activities in the facility (e.g. ANC visits).

**Endpoint:** `GET /dashboard/timeline`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  [
    {
      "type": "ANC_VISIT",
      "isFlagged": false,
      "title": "string",
      "summary": "string",
      "occurredAt": "datetime",
      "sourceId": "string",
      "actions": ["string"]
    }
  ]
}
```

---

## 2. Report Routes
**Base Path:** `/reports`

### 2.1 Get Population Snapshot
Retrieves an aggregated snapshot of the facility's population.

**Endpoint:** `GET /reports/population-snapshot`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  {
    "totalPregnancies": 0,
    "highRiskCount": 0,
    "mediumRiskCount": 0,
    "lowRiskCount": 0,
    "trimesterBreakdown": {
      "T1": 0,
      "T2": 0,
      "T3": 0
    },
    "postpartumCount": 0,
    "snapshotDate": "date"
  }
}
```

### 2.2 Generate Report
Requests asynchronous generation of a report.

**Endpoint:** `POST /reports/`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Request Body:**
```json
{
  "type": "string (e.g., POPULATION, OUTCOMES)",
  "format": "string (e.g., PDF, CSV)",
  "parameters": {}
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  {
    "id": "uuid",
    "facility_id": "uuid",
    "generated_by_id": "uuid",
    "type": "string",
    "format": "string",
    "status": "string (e.g., PENDING, COMPLETED)",
    "file_url": "string | null",
    "parameters": {},
    "completed_at": "datetime | null",
    "created_at": "datetime"
  }
}
```

### 2.3 List Reports
Lists past generated reports for the facility.

**Endpoint:** `GET /reports/`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query
- `limit` (integer, default: 20)
- `offset` (integer, default: 0)

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  [
    {
      "id": "uuid",
      "facility_id": "uuid",
      "generated_by_id": "uuid",
      "type": "string",
      "format": "string",
      "status": "string",
      "file_url": "string | null",
      "parameters": {},
      "completed_at": "datetime | null",
      "created_at": "datetime"
    }
  ]
}
```

### 2.4 Download Report
Retrieves the download URL for a completed report.

**Endpoint:** `GET /reports/{report_id}/download`

**Path Parameters:**
- `report_id` (UUID, required)

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  {
    "downloadUrl": "string"
  }
}
```

---

## 3. Facility Admin Routes
**Base Path:** `/facility-admin`

### 3.1 Enroll Patient Manually
Allows clinicians to manually onboard a patient via SMS-only account.

**Endpoint:** `POST /facility-admin/enroll-patient`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Request Body:**
```json
{
  "phone_number": "string",
  "role": "string",
  "full_name": "string",
  "date_of_birth": "date",
  "gender": "string",
  "preferred_language": "string",
  "county": "string",
  "profile_photo_url": "string"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  {
    "phone_number": "string",
    "role": "string",
    "full_name": "string",
    "date_of_birth": "date",
    "gender": "string",
    "preferred_language": "string",
    "county": "string",
    "profile_photo_url": "string",
    "id": "uuid",
    "is_active": true,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

### 3.2 Bulk Reassign Patients
Allows facility admins to reassign a batch of patients to a different clinician.

**Endpoint:** `POST /facility-admin/bulk-reassign`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Request Body:**
```json
{
  "patientUserIds": ["uuid", "uuid"],
  "clinicianId": "uuid"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
  "data": 
  {
    "status": "success",
    "reassignedCount": 0
  }
}
```

---

## 4. Labour Monitoring Extensions
**Base Path:** `/labour`

### 4.1 Get Active Labour Sessions
Lists facility-wide active labour sessions.

**Endpoint:** `GET /labour/active`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
    "data": [
    {
      "id": "uuid",
      "patientName": "string",
      "room": "string | null",
      "hoursInLabour": 0.0,
      "dilationCm": 0.0,
      "fhr": 0.0,
      "status": "string",
      "assignedClinicianName": "string"
    }
  ]
}
```

### 4.2 Get Alerts Summary
Summarizes labour alerts and active sessions.

**Endpoint:** `GET /labour/alerts-summary`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
    "data": {
    "activeLabourCount": 0,
    "criticalAlertCount": 0,
    "watchAlertCount": 0,
    "recentAlerts": [
      {
        "id": "uuid",
        "type": "string",
        "severity": "string",
        "message": "string",
        "acknowledged_at": "datetime | null",
        "created_at": "datetime"
      }
    ]
  }
}
```

### 4.3 Update Room Assignment
Assigns a room/bed to a labour session.

**Endpoint:** `PUT /labour/sessions/{session_id}/room`

**Path Parameters:**
- `session_id` (UUID, required)

**Request Body:**
```json
{
  "room": "string"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
    "data": {
    "status": "success"
  }
}
```

---

## 5. Postpartum Monitoring Extensions
**Base Path:** `/postpartum`

### 5.1 Get Postpartum Alerts Summary
Summarizes postpartum and newborn alerts.

**Endpoint:** `GET /postpartum/postpartum-alerts/summary`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
    "data": {
    "postpartumPatientCount": 0,
    "criticalAlertCount": 0,
    "watchAlertCount": 0,
    "maternalAlerts": [
      {
        "patientUserId": "uuid",
        "patientName": "string",
        "dayPostpartum": 0,
        "severity": "string",
        "message": "string",
        "sourceSubmissionId": "uuid | null",
        "createdAt": "datetime"
      }
    ],
    "newbornAlerts": [
      {
        "babyId": "uuid",
        "babyName": "string",
        "motherName": "string",
        "dayOfLife": 0,
        "severity": "string",
        "message": "string",
        "createdAt": "datetime"
      }
    ]
  }
}
```

### 5.2 Get Active Postpartum Patients
Lists active postpartum patient caseloads.

**Endpoint:** `GET /postpartum/postpartum-patients`

**Query Parameters:**
- `X-Facility-Context` (UUID) - passed in headers instead of query

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Operation successful",
  "meta": {},
    "data": [
    {
      "patientUserId": "uuid",
      "patientName": "string",
      "dayPostpartum": 0,
      "babyName": "string | null",
      "babySex": "string | null",
      "status": "string",
      "assignedClinicianName": "string | null"
    }
  ]
}
```
