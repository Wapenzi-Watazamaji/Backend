# Universal Referral Network

The Universal Referral Network module in BintiCare enables seamless, secure routing of patients between healthcare facilities. It allows clinics to transfer a patient's care while strictly respecting the patient's data privacy preferences through a robust consent layer.

---

## Core Architecture

### 1. The `Referral` Model
This model acts as the central state machine for a patient transfer. It connects three core entities:
*   **Patient** (`patient_id`): The user being transferred.
*   **Sending Facility** (`sending_facility_id`): The clinic initiating the transfer.
*   **Receiving Facility** (`receiving_facility_id`): The destination clinic.

**Key Fields:**
*   `reason`: Categorizes the referral (`EMERGENCY_COMPLICATION`, `SPECIALIST_CARE`, `LACK_OF_EQUIPMENT`, `PATIENT_PREFERENCE`).
*   `priority`: Urgency level (`ROUTINE`, `URGENT`, `EMERGENCY`).
*   `status`: Follows a strict pipeline (`PENDING` -> `ACCEPTED` -> `IN_TRANSIT` -> `ARRIVED` -> `COMPLETED`). It can also be marked as `REJECTED` or `CANCELLED`.
*   `clinical_notes`: Important context from the sending doctor.
*   `rejection_reason`: Mandatory if the receiving facility rejects the transfer (e.g., "ICU full").

---

## Data Privacy & Consent Engine

Just because a referral is `ACCEPTED` by a receiving clinic does not automatically grant them access to the patient's full BintiCare health passport. Access is governed by the patient's `Profile.emergency_sharing_preference`.

### The Three Preference States:
1.  **`ALWAYS_SHARE`**: The backend automatically generates an active `Consent` record for the receiving facility when they request access.
2.  **`NEVER_SHARE`**: The backend throws an HTTP 403 Forbidden. The patient's data is hard-locked, and the facility must rely on the provided `clinical_notes`.
3.  **`ASK_FIRST` (Default)**: The backend returns a pending status, simulating a push notification to the patient's mobile app asking them to tap "Approve" or "Deny".

### Consent Revocation
Patients retain ultimate control over their data. Using the `Consent` model, a patient can open their app at any time and revoke a facility's access. The backend immediately flips `active = False` and stamps a `revoked_at` timestamp. Future requests by that facility will be instantly blocked.

---

## API Endpoints

All endpoints require standard Bearer Authentication via the `Authorization` header. Facility endpoints also require the `x-facility-context` header.

### Facility Operations (`/api/v1/referrals`)

#### 1. Create a Referral
Initiate a patient transfer from the current facility (Clinic A) to a destination facility (Clinic B).
*   **Method:** `POST /`
*   **Headers:**
    *   `Authorization`: `Bearer {token}`
    *   `x-facility-context`: `{sending_facility_uuid}`
*   **Request Body (`ReferralCreate`)**:
    ```json
    {
      "patient_id": "uuid",
      "receiving_facility_id": "uuid",
      "reason": "EMERGENCY_COMPLICATION | SPECIALIST_CARE | LACK_OF_EQUIPMENT | PATIENT_PREFERENCE | OTHER",
      "priority": "ROUTINE | URGENT | EMERGENCY",
      "clinical_notes": "string"
    }
    ```
*   **Response Body (`APIResponse[ReferralRead]`)**:
    ```json
    {
      "success": true,
      "message": "Referral created successfully",
      "data": {
        "id": "uuid",
        "patient_id": "uuid",
        "sending_facility_id": "uuid",
        "receiving_facility_id": "uuid",
        "reason": "string",
        "priority": "string",
        "status": "PENDING",
        "clinical_notes": "string",
        "rejection_reason": null,
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    }
    ```

#### 2. Get Facility Inbox
Fetch all incoming referrals for the current facility.
*   **Method:** `GET /inbox`
*   **Headers:**
    *   `Authorization`: `Bearer {token}`
    *   `x-facility-context`: `{receiving_facility_uuid}`
*   **Response Body (`APIResponse[list[ReferralRead]]`)**: Array of ReferralRead objects.

#### 3. Get Facility Outbox
Fetch all outgoing referrals initiated by the current facility.
*   **Method:** `GET /outbox`
*   **Headers:**
    *   `Authorization`: `Bearer {token}`
    *   `x-facility-context`: `{sending_facility_uuid}`
*   **Response Body (`APIResponse[list[ReferralRead]]`)**: Array of ReferralRead objects.

#### 4. Update Referral Status
Allows the receiving facility (Clinic B) to Accept, Reject, or mark the referral as Completed.
*   **Method:** `PUT /{id}`
*   **Headers:**
    *   `Authorization`: `Bearer {token}`
    *   `x-facility-context`: `{receiving_facility_uuid}`
*   **Request Body (`ReferralUpdate`)**:
    ```json
    {
      "status": "ACCEPTED | REJECTED | IN_TRANSIT | ARRIVED | COMPLETED | CANCELLED",
      "rejection_reason": "string (required if REJECTED, otherwise null)"
    }
    ```
*   **Response Body (`APIResponse[ReferralRead]`)**: The updated ReferralRead object.

#### 5. Request Records Access
Allows the receiving facility to request access to the patient's BintiCare passport after accepting the referral.
*   **Method:** `POST /{id}/request-records-access`
*   **Headers:**
    *   `Authorization`: `Bearer {token}`
    *   `x-facility-context`: `{receiving_facility_uuid}`
*   **Response Body (`APIResponse[dict]`)**:
    *   *If ALWAYS_SHARE*: `{"success": true, "message": "Access granted via ALWAYS_SHARE preference", "data": {"status": "access_granted"}}`
    *   *If ASK_FIRST*: `{"success": true, "message": "Push notification sent to patient asking for consent", "data": {"status": "pending_consent"}}`
    *   *If NEVER_SHARE*: Returns HTTP 403 Forbidden.

---

### Patient Operations (`/api/v1/profile/me/consents`)

#### 1. Revoke Facility Consent
Allows the patient to immediately kill a facility's access to their data.
*   **Method:** `PUT /{grantee_id}/revoke`
*   **Headers:**
    *   `Authorization`: `Bearer {patient_token}`
*   **Response Body (`APIResponse[ConsentRead]`)**:
    ```json
    {
      "success": true,
      "message": "Consent revoked successfully",
      "data": {
        "id": "uuid",
        "user_id": "uuid",
        "consent_type": "FACILITY_AUTO_SHARE",
        "grantee_id": "uuid",
        "grantee_name": "string",
        "active": false,
        "granted_at": "datetime",
        "revoked_at": "datetime"
      }
    }
    ```

---

## Part 3: Emergency SOS System (`/api/v1/emergencies`)

This module handles patient-initiated emergency requests routed directly to a chosen facility (often their preferred facility).

### 1. Trigger Emergency SOS (Patient)
Allows a patient to trigger an emergency alert.
*   **Method:** `POST /`
*   **Headers:** `Authorization: Bearer {patient_token}`
*   **Request Body (`EmergencyRequestCreate`)**:
    ```json
    {
      "facility_id": "uuid",
      "location_lat": "-1.2833",
      "location_lng": "36.8167",
      "notes": "Severe abdominal pain"
    }
    ```
*   **Response Body (`APIResponse[EmergencyRequestRead]`)**:
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

### 2. View My Emergencies (Patient)
Fetches the patient's own emergency request history.
*   **Method:** `GET /my-requests`
*   **Headers:** `Authorization: Bearer {patient_token}`
*   **Response Body**: Array of `EmergencyRequestRead` objects.

### 3. Emergency Inbox (Facility)
Fetches all incoming patient SOS alerts directed to the authenticated facility.
*   **Method:** `GET /inbox`
*   **Headers:** 
    *   `Authorization`: `Bearer {staff_token}`
    *   `x-facility-context`: `uuid` (Required)
*   **Response Body**: Array of `EmergencyRequestRead` objects.

### 4. Update Emergency Status (Facility)
Allows the receiving facility to update the status of the emergency (e.g., when an ambulance is dispatched).
*   **Method:** `PUT /{id}`
*   **Headers:**
    *   `Authorization`: `Bearer {staff_token}`
    *   `x-facility-context`: `uuid` (Required)
*   **Request Body (`EmergencyRequestUpdate`)**:
    ```json
    {
      "status": "DISPATCHED" 
    }
    ```
    *Status Options:* `PENDING`, `DISPATCHED`, `RESOLVED`, `FALSE_ALARM`
*   **Response Body**: Updated `EmergencyRequestRead` object.
