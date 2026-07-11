import pytest
import uuid
from httpx import AsyncClient
from datetime import date, datetime, timedelta

@pytest.mark.asyncio
async def test_postpartum_tracking_endpoints(authenticated_client: AsyncClient):
    patient_client = authenticated_client

    # 1. Create Baby Profile
    baby_payload = {
        "name": "Test Baby",
        "dateOfBirth": str(date.today()),
        "timeOfBirth": "14:30",
        "sex": "MALE",
        "birthWeightKg": 3.2,
        "birthLengthCm": 50.0,
        "deliveryType": "VAGINAL"
    }
    res_baby = await patient_client.post("/api/v1/postpartum/baby/profile", json=baby_payload)
    assert res_baby.status_code == 201, f"Failed: {res_baby.text}"
    baby_id = res_baby.json()["data"]["id"]

    # 2. Get Baby Profile
    res_get_baby = await patient_client.get(f"/api/v1/postpartum/baby/profiles/{baby_id}")
    assert res_get_baby.status_code == 200, f"Failed: {res_get_baby.text}"

    # 3. Add Baby Milestone
    milestone_payload = {
        "category": "MOVEMENT",
        "title": "First Step",
        "achievedAt": str(date.today()),
        "note": "Took first step today"
    }
    res_milestone = await patient_client.post(f"/api/v1/postpartum/baby/{baby_id}/milestones", json=milestone_payload)
    assert res_milestone.status_code == 201, f"Failed: {res_milestone.text}"

    # 4. List Milestones
    res_list_milestone = await patient_client.get(f"/api/v1/postpartum/baby/{baby_id}/milestones")
    assert res_list_milestone.status_code == 200, f"Failed: {res_list_milestone.text}"

    # 5. Submit EPDS Screening
    epds_payload = {
        "responses": [
            {"questionId": "q1", "answerValue": 1},
            {"questionId": "q2", "answerValue": 0},
            {"questionId": "q3", "answerValue": 2},
            {"questionId": "q10", "answerValue": 0}  # q10 is usually self-harm, 0 means no concern
        ]
    }
    res_epds = await patient_client.post("/api/v1/postpartum/depression-screening", json=epds_payload)
    assert res_epds.status_code == 201, f"Failed: {res_epds.text}"

    # 6. Get EPDS Flag
    res_flag = await patient_client.get("/api/v1/postpartum/depression-screening/flag")
    assert res_flag.status_code == 200, f"Failed: {res_flag.text}"
