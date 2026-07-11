import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_emergency_tracking_endpoints(authenticated_client: AsyncClient, clinician_client: AsyncClient):
    patient_client = authenticated_client
    
    # 1. Clinician registers a facility (to get facility ID)
    facility_payload = {
        "facility": {
            "name": f"Emergency Facility {uuid.uuid4().hex[:6]}",
            "type": "PUBLIC",
            "county": "Nairobi",
            "phone_number": f"+254722{uuid.uuid4().int % 1000000:06d}",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "address": "Nairobi, Kenya"
        },
        "admin_account": {
            "phone_number": f"+254711{uuid.uuid4().int % 1000000:06d}",
            "password": "SecurePassword123!",
            "full_name": "Emergency Admin",
            "role": "FACILITY_ADMIN"
        }
    }
    res_fac = await clinician_client.post("/api/v1/facilities/register", json=facility_payload)
    assert res_fac.status_code == 201
    facility_id = res_fac.json()["data"]["facility"]["id"]

    # Login as the facility admin
    admin_login = await clinician_client.post("/api/v1/auth/login", json={
        "phone_number": facility_payload["admin_account"]["phone_number"],
        "password": facility_payload["admin_account"]["password"]
    })
    assert admin_login.status_code == 200
    token = admin_login.json()["data"]["access_token"]
    clinician_client.headers.update({"Authorization": f"Bearer {token}"})

    # 2. Patient creates an emergency request
    emergency_payload = {
        "facility_id": facility_id,
        "location_lat": "-1.2921",
        "location_lng": "36.8219",
        "notes": "Severe bleeding"
    }
    res_emergency = await patient_client.post("/api/v1/emergencies", json=emergency_payload)
    assert res_emergency.status_code == 200, f"Failed: {res_emergency.text}"
    emergency_id = res_emergency.json()["data"]["id"]

    # 3. Patient gets their emergency requests
    res_my_emergencies = await patient_client.get("/api/v1/emergencies/my-requests")
    assert res_my_emergencies.status_code == 200, f"Failed: {res_my_emergencies.text}"

    # 4. Clinician gets facility emergencies (inbox)
    headers = {"X-Facility-Context": facility_id}
    res_inbox = await clinician_client.get("/api/v1/emergencies/inbox", headers=headers)
    assert res_inbox.status_code == 200, f"Failed: {res_inbox.text}"

    # 5. Clinician updates emergency status
    update_payload = {
        "status": "DISPATCHED"
    }
    res_update = await clinician_client.put(f"/api/v1/emergencies/{emergency_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200, f"Failed: {res_update.text}"
