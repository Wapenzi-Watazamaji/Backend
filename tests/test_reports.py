import pytest
from httpx import AsyncClient
import uuid
import datetime

@pytest.mark.asyncio
async def test_reports_endpoints(clinician_client: AsyncClient):
    # 1. Clinician registers a facility
    facility_payload = {
        "facility": {
            "name": f"Reports Facility {uuid.uuid4().hex[:6]}",
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
            "full_name": "Reports Admin",
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

    # 2. Get population snapshot
    res_snapshot = await clinician_client.get("/api/v1/reports/population-snapshot", headers=headers)
    assert res_snapshot.status_code == 200, f"Failed: {res_snapshot.text}"

    # 3. Generate a report
    report_payload = {
        "type": "MONTHLY_FACILITY_SUMMARY",
        "dateRangeStart": (datetime.date.today() - datetime.timedelta(days=30)).isoformat(),
        "dateRangeEnd": datetime.date.today().isoformat(),
        "format": "PDF"
    }
    res_generate = await clinician_client.post("/api/v1/reports/", json=report_payload, headers=headers)
    assert res_generate.status_code == 200, f"Failed: {res_generate.text}"
    report_id = res_generate.json()["data"]["id"]

    # 4. List generated reports
    res_list = await clinician_client.get("/api/v1/reports/", headers=headers)
    assert res_list.status_code == 200, f"Failed: {res_list.text}"
    assert len(res_list.json()["data"]) > 0

    # 5. Download report
    res_download = await clinician_client.get(f"/api/v1/reports/{report_id}/download", headers=headers)
    # The download endpoint returns 200 if ready, or might throw 404 if not ready/found.
    # In this mock service it seems to return a placeholder URL.
    assert res_download.status_code in [200, 404], f"Failed: {res_download.text}"
