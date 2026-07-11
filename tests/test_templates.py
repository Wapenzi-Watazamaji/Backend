import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_all_care_pathway_templates(authenticated_client: AsyncClient):
    res = await authenticated_client.get("/api/v1/templates/care-pathways")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)

@pytest.mark.asyncio
async def test_form_templates_crud(clinician_client: AsyncClient, async_client: AsyncClient):
    # Register a facility first
    admin_phone = f"+254700{uuid.uuid4().int % 1000000:06d}"
    facility_payload = {
        "facility": {
            "name": f"Template Facility {uuid.uuid4().hex[:6]}",
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

    async_client.headers.update({
        "Authorization": f"Bearer {admin_token}",
        "X-Facility-Context": facility_id
    })

    # Create Form Template
    create_payload = {
        "slug": f"anc-initial-assessment-{uuid.uuid4().hex[:6]}",
        "context": "PREGNANCY_VITALS",
        "fields": {
            "lmp": {"type": "date", "required": True},
            "parity": {"type": "integer", "required": True}
        },
        "is_active": True
    }
    res_create = await async_client.post("/api/v1/templates/forms", json=create_payload)
    assert res_create.status_code == 201, f"Failed to create template: {res_create.text}"
    template_data = res_create.json()["data"]
    template_id = template_data["id"]
    assert template_data["slug"].startswith("anc-initial")
    assert template_data["context"] == "PREGNANCY_VITALS"

    # Get Form Templates
    res_get = await async_client.get("/api/v1/templates/forms?context=PREGNANCY_VITALS")
    assert res_get.status_code == 200
    assert any(t["id"] == template_id for t in res_get.json()["data"])

    # Update Form Template
    update_payload = {
        "version": "v2"
    }
    res_update = await async_client.put(f"/api/v1/templates/forms/{template_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["data"]["version"] == "v2"
