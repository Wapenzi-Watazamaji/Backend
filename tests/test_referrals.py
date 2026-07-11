import pytest
import uuid
from httpx import AsyncClient
from datetime import datetime

@pytest.mark.asyncio
async def test_referral_tracking_endpoints(authenticated_client: AsyncClient, clinician_client: AsyncClient):
    patient_client = authenticated_client
    
    # 1. Clinician registers Facility A
    fac_a_payload = {
        "facility": {
            "name": f"Facility A {uuid.uuid4().hex[:6]}",
            "type": "PUBLIC",
            "county": "Nairobi",
            "phone_number": f"+254700{uuid.uuid4().int % 1000000:06d}",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "address": "Nairobi, Kenya"
        },
        "admin_account": {
            "phone_number": f"+254711{uuid.uuid4().int % 1000000:06d}",
            "password": "SecurePassword123!",
            "full_name": "Admin A",
            "role": "FACILITY_ADMIN"
        }
    }
    res_fac_a = await clinician_client.post("/api/v1/facilities/register", json=fac_a_payload)
    assert res_fac_a.status_code == 201
    fac_a_id = res_fac_a.json()["data"]["facility"]["id"]

    # 2. Clinician registers Facility B
    fac_b_payload = {
        "facility": {
            "name": f"Facility B {uuid.uuid4().hex[:6]}",
            "type": "PUBLIC",
            "county": "Nairobi",
            "phone_number": f"+254700{uuid.uuid4().int % 1000000:06d}",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "address": "Nairobi, Kenya"
        },
        "admin_account": {
            "phone_number": f"+254711{uuid.uuid4().int % 1000000:06d}",
            "password": "SecurePassword123!",
            "full_name": "Admin B",
            "role": "FACILITY_ADMIN"
        }
    }
    res_fac_b = await clinician_client.post("/api/v1/facilities/register", json=fac_b_payload)
    assert res_fac_b.status_code == 201
    fac_b_id = res_fac_b.json()["data"]["facility"]["id"]

    # 3. Patient creates a referral
    referral_payload = {
        "fromFacilityId": fac_a_id,
        "toFacilityId": fac_b_id,
        "reason": "SPECIALIST_REFERRAL",
        "notes": "Needs cardiologist",
        "isEmergency": False
    }
    res_ref = await patient_client.post("/api/v1/referrals", json=referral_payload)
    assert res_ref.status_code == 201, f"Failed: {res_ref.text}"
    referral_id = res_ref.json()["data"]["id"]

    # 4. Get Referral
    res_get_ref = await patient_client.get(f"/api/v1/referrals/{referral_id}")
    assert res_get_ref.status_code == 200, f"Failed: {res_get_ref.text}"

    # 5. List Referrals
    res_list = await patient_client.get(f"/api/v1/referrals?facilityId={fac_a_id}")
    assert res_list.status_code == 200, f"Failed: {res_list.text}"

    # Login as Admin B
    admin_login = await clinician_client.post("/api/v1/auth/login", json={
        "phone_number": fac_b_payload["admin_account"]["phone_number"],
        "password": fac_b_payload["admin_account"]["password"]
    })
    assert admin_login.status_code == 200
    token = admin_login.json()["data"]["access_token"]
    clinician_client.headers.update({"Authorization": f"Bearer {token}"})

    # 6. Incoming Inbox for Facility B
    headers_b = {"X-Facility-Context": fac_b_id}
    res_inbox_b = await clinician_client.get("/api/v1/referrals/inbox/incoming", headers=headers_b)
    assert res_inbox_b.status_code == 200, f"Failed: {res_inbox_b.text}"

    # 7. Accept Referral
    res_accept = await clinician_client.put(f"/api/v1/referrals/{referral_id}/accept", headers=headers_b)
    assert res_accept.status_code == 200, f"Failed: {res_accept.text}"

    # 8. Complete Referral
    res_complete = await clinician_client.put(f"/api/v1/referrals/{referral_id}/complete", headers=headers_b)
    assert res_complete.status_code == 200, f"Failed: {res_complete.text}"

    # 9. Get Patient Summary
    res_summary = await clinician_client.get(f"/api/v1/referrals/{referral_id}/patient-summary", headers=headers_b)
    assert res_summary.status_code == 200, f"Failed: {res_summary.text}"
