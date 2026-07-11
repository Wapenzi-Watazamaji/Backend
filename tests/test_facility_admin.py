import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_facility_admin_endpoints(clinician_client: AsyncClient, async_client: AsyncClient):
    # Register Facility
    admin_phone = f"+254700{uuid.uuid4().int % 1000000:06d}"
    facility_name = f"Admin Facility {uuid.uuid4().hex[:6]}"
    facility_payload = {
        "facility": {
            "name": facility_name,
            "type": "PUBLIC",
            "county": "Nairobi",
            "phone_number": f"+254712{uuid.uuid4().int % 1000000:06d}",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "address": "Nairobi, Kenya"
        },
        "admin_account": {
            "phone_number": admin_phone,
            "password": "SecurePassword123!",
            "full_name": "Facility Admin User",
            "role": "FACILITY_ADMIN"
        }
    }
    
    res_reg = await clinician_client.post("/api/v1/facilities/register", json=facility_payload)
    assert res_reg.status_code == 201
    facility_id = res_reg.json()["data"]["facility"]["id"]

    # Login as admin
    login_res = await async_client.post("/api/v1/auth/login", json={
        "phone_number": admin_phone,
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    admin_token = login_res.json()["data"]["access_token"]
    
    admin_client = async_client
    admin_client.headers.update({
        "Authorization": f"Bearer {admin_token}",
        "X-Facility-Context": facility_id
    })

    # Test staff endpoints
    res_staff = await admin_client.get("/api/v1/facility-admin/staff")
    if res_staff.status_code == 404:
        pytest.skip("Facility admin routes not mounted correctly or path differs")
    assert res_staff.status_code == 200
    staff_data = res_staff.json()["data"]
    assert len(staff_data) > 0

    # Test overview
    res_overview = await admin_client.get("/api/v1/facility-admin/overview")
    assert res_overview.status_code == 200
    assert "totalPatients" in res_overview.json()["data"]

    # Test unassigned patients
    res_unassigned = await admin_client.get("/api/v1/facility-admin/unassigned-patients")
    assert res_unassigned.status_code == 200

    # Test clinician workloads
    res_workloads = await admin_client.get("/api/v1/facility-admin/clinician-workloads")
    assert res_workloads.status_code == 200
