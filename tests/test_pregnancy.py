import pytest
import uuid
from httpx import AsyncClient
from datetime import date, datetime, timedelta

@pytest.mark.asyncio
async def test_pregnancy_tracking_endpoints(authenticated_client: AsyncClient, clinician_client: AsyncClient, async_client: AsyncClient):
    patient_client = authenticated_client
    
    # 1. Start Pregnancy
    start_payload = {
        "dateInputType": "LMP",
        "lastMenstrualPeriod": str(date.today() - timedelta(days=60)),
        "dueDate": str(date.today() + timedelta(days=220)),
        "isFirstPregnancy": False
    }
    
    res_start = await patient_client.post("/api/v1/pregnancy/start", json=start_payload)
    assert res_start.status_code == 201, f"Failed: {res_start.text}"
    pregnancy_id = res_start.json()["data"]["id"]
    
    # 2. Get Current Pregnancy
    res_current = await patient_client.get("/api/v1/pregnancy/current")
    assert res_current.status_code == 200, f"Failed: {res_current.text}"
    assert res_current.json()["data"]["id"] == pregnancy_id
    
    # 3. Update Pregnancy
    update_payload = {
        "dueDate": str(date.today() + timedelta(days=210))
    }
    res_update = await patient_client.put("/api/v1/pregnancy/current", json=update_payload)
    assert res_update.status_code == 200, f"Failed: {res_update.text}"
    
    # 4. Get Week Info
    res_week = await patient_client.get("/api/v1/pregnancy/week-info")
    assert res_week.status_code == 200, f"Failed: {res_week.text}"
    
    # 5. Get Risk Score
    res_risk = await patient_client.get("/api/v1/pregnancy/risk-score")
    assert res_risk.status_code == 200, f"Failed: {res_risk.text}"
    
    # 6. Get Nutrition Guidance
    res_nutrition = await patient_client.get("/api/v1/pregnancy/nutrition-guidance")
    assert res_nutrition.status_code == 200, f"Failed: {res_nutrition.text}"
    
    # 7. End Pregnancy
    end_payload = {
        "endedAt": datetime.now().isoformat(),
        "outcome": "LIVE_BIRTH"
    }
    res_end = await patient_client.post("/api/v1/pregnancy/end", json=end_payload)
    assert res_end.status_code == 200, f"Failed: {res_end.text}"

