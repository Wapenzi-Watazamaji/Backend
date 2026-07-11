import pytest
import uuid
from httpx import AsyncClient
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_education_tracking_endpoints(authenticated_client: AsyncClient, clinician_client: AsyncClient):
    # 1. Clinician registers a facility
    facility_payload = {
        "facility": {
            "name": f"Education Facility {uuid.uuid4().hex[:6]}",
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
            "full_name": "Education Admin",
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
    
    headers = {"X-Facility-Context": facility_id}

    # 2. Create Education Content
    content_payload = {
        "title": "Healthy Diet During Pregnancy",
        "category": "NUTRITION",
        "body": "Eat vegetables...",
        "target_stages": ["PREGNANT"]
    }
    res_content = await clinician_client.post("/api/v1/education/content", json=content_payload, headers=headers)
    assert res_content.status_code == 201, f"Failed: {res_content.text}"
    content_id = res_content.json()["data"]["id"]

    # 3. List Education Content
    res_list_content = await authenticated_client.get(f"/api/v1/education/content?facility_id={facility_id}&category=NUTRITION")
    assert res_list_content.status_code == 200, f"Failed: {res_list_content.text}"

    # 4. Get Education Content
    res_get_content = await authenticated_client.get(f"/api/v1/education/content/{content_id}")
    assert res_get_content.status_code == 200, f"Failed: {res_get_content.text}"

    # 5. Update Education Content
    update_content_payload = {
        "title": "Updated Healthy Diet During Pregnancy"
    }
    res_update_content = await clinician_client.put(f"/api/v1/education/content/{content_id}", json=update_content_payload, headers=headers)
    assert res_update_content.status_code == 200, f"Failed: {res_update_content.text}"

    # 6. Create Education Event
    event_payload = {
        "title": "Antenatal Class",
        "event_date": datetime.now(timezone.utc).isoformat(),
        "description": "Weekly antenatal class."
    }
    res_event = await clinician_client.post("/api/v1/education/events", json=event_payload, headers=headers)
    assert res_event.status_code == 201, f"Failed: {res_event.text}"
    event_id = res_event.json()["data"]["id"]

    # 7. List Education Events
    res_list_events = await authenticated_client.get(f"/api/v1/education/events?facility_id={facility_id}")
    assert res_list_events.status_code == 200, f"Failed: {res_list_events.text}"

    # 8. Get Education Event
    res_get_event = await authenticated_client.get(f"/api/v1/education/events/{event_id}")
    assert res_get_event.status_code == 200, f"Failed: {res_get_event.text}"

    # 9. Get Feed
    res_feed = await authenticated_client.get(f"/api/v1/education/feed?facility_id={facility_id}&filter_type=all")
    assert res_feed.status_code == 200, f"Failed: {res_feed.text}"
