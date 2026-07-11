import pytest
import uuid
from httpx import AsyncClient
from datetime import date, datetime, timedelta

@pytest.mark.asyncio
async def test_labour_tracking_endpoints(authenticated_client: AsyncClient, clinician_client: AsyncClient):
    patient_client = authenticated_client
    
    # 1. Start Pregnancy
    start_payload = {
        "dateInputType": "LMP",
        "lastMenstrualPeriod": str(date.today() - timedelta(days=270)), # almost due
        "dueDate": str(date.today() + timedelta(days=10)),
        "isFirstPregnancy": True
    }
    res_preg = await patient_client.post("/api/v1/pregnancy/start", json=start_payload)
    assert res_preg.status_code == 201
    pregnancy_id = res_preg.json()["data"]["id"]

    # 2. Clinician registers a facility (to get facility ID)
    facility_payload = {
        "facility": {
            "name": f"Labour Facility {uuid.uuid4().hex[:6]}",
            "type": "PUBLIC",
            "county": "Nairobi",
            "phone_number": f"+254712{uuid.uuid4().int % 1000000:06d}",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "address": "Nairobi, Kenya"
        },
        "admin_account": {
            "phone_number": f"+254700{uuid.uuid4().int % 1000000:06d}",
            "password": "SecurePassword123!",
            "full_name": "Admin",
            "role": "FACILITY_ADMIN"
        }
    }
    res_fac = await clinician_client.post("/api/v1/facilities/register", json=facility_payload)
    assert res_fac.status_code == 201
    facility_id = res_fac.json()["data"]["facility"]["id"]

    # 3. Clinician starts a labour session
    session_payload = {
        "pregnancyId": pregnancy_id,
        "facilityId": facility_id,
        "activeLabourStartedAt": datetime.now().isoformat(),
        "room": "Ward 1"
    }
    res_session = await clinician_client.post("/api/v1/labour/sessions", json=session_payload)
    assert res_session.status_code == 201, f"Failed: {res_session.text}"
    session_id = res_session.json()["data"]["id"]

    # 4. Get Labour Session
    res_get_session = await clinician_client.get(f"/api/v1/labour/sessions/{session_id}")
    assert res_get_session.status_code == 200, f"Failed: {res_get_session.text}"

    # 5. Add Dilation Reading
    dilation_payload = {
        "value": 4.5,
        "recordedAt": datetime.now().isoformat()
    }
    res_dilation = await clinician_client.post(f"/api/v1/labour/sessions/{session_id}/readings/dilation", json=dilation_payload)
    assert res_dilation.status_code == 201, f"Failed: {res_dilation.text}"

    # 6. Add FHR Reading
    fhr_payload = {
        "value": 140,
        "recordedAt": datetime.now().isoformat()
    }
    res_fhr = await clinician_client.post(f"/api/v1/labour/sessions/{session_id}/readings/fhr", json=fhr_payload)
    assert res_fhr.status_code == 201, f"Failed: {res_fhr.text}"

    # 7. Get Partograph
    res_partograph = await clinician_client.get(f"/api/v1/labour/sessions/{session_id}/partograph")
    assert res_partograph.status_code == 200, f"Failed: {res_partograph.text}"

    # 8. Get Alerts
    res_alerts = await clinician_client.get(f"/api/v1/labour/sessions/{session_id}/alerts")
    assert res_alerts.status_code == 200, f"Failed: {res_alerts.text}"

    # 9. Get Resuscitation Protocol
    res_proto = await clinician_client.get("/api/v1/labour/resuscitation-protocol")
    assert res_proto.status_code == 200, f"Failed: {res_proto.text}"

    # 10. Close Session
    close_payload = {
        "closedAt": datetime.now().isoformat(),
        "outcome": "LIVE_BIRTH",
        "deliveryType": "VAGINAL"
    }
    res_close = await clinician_client.put(f"/api/v1/labour/sessions/{session_id}/close", json=close_payload)
    assert res_close.status_code == 200, f"Failed: {res_close.text}"
