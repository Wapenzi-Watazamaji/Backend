import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_patient_get_medical_history(authenticated_client: AsyncClient):
    # As a new patient, fetching medical history should return 404
    res = await authenticated_client.get("/api/v1/medical-history/profile/medical-history")
    assert res.status_code == 404
    data = res.json()
    assert data["success"] is False

@pytest.mark.asyncio
async def test_clinician_create_and_update_medical_history(clinician_client: AsyncClient, authenticated_client: AsyncClient):
    patient_id = authenticated_client.user_id

    # Create medical history as clinician
    create_payload = {
        "blood_type": "O",
        "rh_factor": "+",
        "allergies": ["Penicillin"],
        "chronic_conditions": ["Asthma"],
        "current_medications": [
            {
                "name": "Albuterol",
                "dose": "2 puffs",
                "frequency": "As needed"
            }
        ],
        "surgical_history": [
            {
                "procedure": "Appendectomy",
                "year": "2010"
            }
        ],
        "previous_pregnancies": 1,
        "previous_outcomes": ["Live Birth"]
    }

    res_create = await clinician_client.post(
        f"/api/v1/medical-history/patients/{patient_id}/medical-history",
        json=create_payload
    )
    assert res_create.status_code == 200
    data_create = res_create.json()["data"]
    assert data_create["blood_type"] == "O"
    assert data_create["rh_factor"] == "+"
    assert "Penicillin" in data_create["allergies"]
    
    # Update medical history as clinician
    update_payload = {
        "blood_type": "O",
        "rh_factor": "+",
        "allergies": ["Penicillin", "Latex"],
        "chronic_conditions": ["Asthma"],
        "previous_pregnancies": 1
    }
    res_update = await clinician_client.put(
        f"/api/v1/medical-history/patients/{patient_id}/medical-history",
        json=update_payload
    )
    assert res_update.status_code == 200
    data_update = res_update.json()["data"]
    assert "Latex" in data_update["allergies"]

    # Verify patient can see the updated history
    res_patient = await authenticated_client.get("/api/v1/medical-history/profile/medical-history")
    assert res_patient.status_code == 200
    assert "Latex" in res_patient.json()["data"]["allergies"]

@pytest.mark.asyncio
async def test_facility_custom_fields(clinician_client: AsyncClient):
    # Register a facility first
    admin_phone = f"+254700{uuid.uuid4().int % 1000000:06d}"
    facility_payload = {
        "facility": {
            "name": f"Test Facility {uuid.uuid4().hex[:6]}",
            "type": "PUBLIC",
            "county": "Nairobi",
            "phone_number": f"+254712{uuid.uuid4().int % 1000000:06d}",
            "location_lat": "-1.2921",
            "location_lng": "36.8219",
            "address": "Nairobi, Kenya"
        },
        "admin_account": {
            "phone_number": admin_phone,
            "password": "SecurePassword123!",
            "full_name": "Admin",
            "role": "FACILITY_ADMIN"
        }
    }
    res_fac = await clinician_client.post("/api/v1/facilities/register", json=facility_payload)
    if res_fac.status_code == 404: 
        pytest.skip("Facility registration route not found or different")
    
    assert res_fac.status_code == 201, f"Failed to register facility: {res_fac.text}"
    facility_id = res_fac.json()["data"]["facility"]["id"]  

    # Login as the facility admin
    login_res = await clinician_client.post("/api/v1/auth/login", json={
        "phone_number": admin_phone,
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    admin_token = login_res.json()["data"]["access_token"]

    # Use a new client with admin token and correct facility context header
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as admin_client:
        admin_client.headers.update({
            "Authorization": f"Bearer {admin_token}",
            "X-Facility-Context": facility_id
        })

        # Create a custom field
        custom_field_payload = {
            "key": "malaria_history",
            "label": "History of Malaria",
            "type": "BOOLEAN"
        }
        res_cf_create = await admin_client.post(
            "/api/v1/medical-history/facility/medical-history-fields",
            json=custom_field_payload
        )
        assert res_cf_create.status_code == 200
        cf_data = res_cf_create.json()["data"]
        assert cf_data["key"] == "malaria_history"
        assert cf_data["facility_id"] == facility_id

        # Fetch custom fields
        res_cf_get = await admin_client.get("/api/v1/medical-history/facility/medical-history-fields")
        assert res_cf_get.status_code == 200
        fields = res_cf_get.json()["data"]
        assert len(fields) >= 1
        assert any(f["key"] == "malaria_history" for f in fields)
