import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_facility_registration_and_retrieval(clinician_client: AsyncClient, async_client: AsyncClient):
    # Register Facility
    admin_phone = f"+254700{uuid.uuid4().int % 1000000:06d}"
    facility_name = f"Test Facility {uuid.uuid4().hex[:6]}"
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
    assert res_reg.status_code == 201, f"Failed to register facility: {res_reg.text}"
    facility_id = res_reg.json()["data"]["facility"]["id"]

    # Test get nearby facilities
    res_nearby = await clinician_client.get("/api/v1/facilities/nearby?lat=-1.2921&lng=36.8219&radius_km=50")
    assert res_nearby.status_code == 200
    facilities = res_nearby.json()["data"]
    assert any(f["id"] == facility_id for f in facilities)

    # Login as admin to test current facility endpoints
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

    # Get current facility
    res_current = await admin_client.get("/api/v1/facilities/current")
    assert res_current.status_code == 200
    assert res_current.json()["data"]["id"] == facility_id
    assert res_current.json()["data"]["name"] == facility_name

    # Update current facility
    update_payload = {
        "name": f"{facility_name} Updated",
        "county": "Mombasa"
    }
    res_update = await admin_client.put("/api/v1/facilities/current", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["data"]["name"] == update_payload["name"]
    assert res_update.json()["data"]["county"] == "Mombasa"

    # Get stats
    res_stats = await admin_client.get("/api/v1/facilities/current/stats")
    assert res_stats.status_code == 200
    assert "total_assigned_patients" in res_stats.json()["data"]
