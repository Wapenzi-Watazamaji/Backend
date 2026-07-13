import pytest
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_reminders_lifecycle(authenticated_client: AsyncClient):
    client = authenticated_client
    
    # 1. Create a reminder
    due_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_payload = {
        "title": "ANC check-up week 12",
        "type": "ANC_VISIT",
        "dueAt": due_at
    }
    res = await client.post("/api/v1/reminders", json=create_payload)
    assert res.status_code == 201, f"Failed: {res.text}"
    reminder_id = res.json()["data"]["id"]
    
    # 2. List reminders
    res_list = await client.get("/api/v1/reminders")
    assert res_list.status_code == 200
    reminders = res_list.json()["data"]
    assert len(reminders) >= 1
    assert reminders[0]["title"] == "ANC check-up week 12"
    assert reminders[0]["isDone"] is False
    
    # 3. Update reminder due time
    new_due_at = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    update_payload = {"dueAt": new_due_at}
    res_up = await client.put(f"/api/v1/reminders/{reminder_id}", json=update_payload)
    assert res_up.status_code == 200
    assert res_up.json()["data"]["dueAt"].startswith(new_due_at[:19])
    
    # 4. Mark reminder as done
    res_done = await client.put(f"/api/v1/reminders/{reminder_id}/mark-done")
    assert res_done.status_code == 200
    assert res_done.json()["data"]["isDone"] is True
    
    # 5. Delete reminder
    res_del = await client.delete(f"/api/v1/reminders/{reminder_id}")
    assert res_del.status_code == 204
    
    # Verify deletion
    res_get_del = await client.get("/api/v1/reminders")
    assert not any(r["id"] == reminder_id for r in res_get_del.json()["data"])

@pytest.mark.asyncio
async def test_notifications_and_devices(authenticated_client: AsyncClient, async_client: AsyncClient):
    client = authenticated_client
    
    # 1. Register device token
    device_payload = {
        "deviceToken": "fcm_token_12345",
        "platform": "ANDROID"
    }
    res_dev = await client.post("/api/v1/devices/register", json=device_payload)
    assert res_dev.status_code == 201
    token_id = res_dev.json()["data"]["tokenId"]
    assert token_id is not None
    
    # 2. Unregister device token
    res_unreg = await client.delete(f"/api/v1/devices/{token_id}")
    assert res_unreg.status_code == 204

    # 3. Test preferences
    res_pref = await client.get("/api/v1/notifications/sms/preferences")
    assert res_pref.status_code == 200
    assert "contactPreference" in res_pref.json()["data"]
    
    # Update preference to SMS
    update_payload = {"contactPreference": "SMS"}
    res_pref_up = await client.put("/api/v1/notifications/sms/preferences", json=update_payload)
    assert res_pref_up.status_code == 200
    assert res_pref_up.json()["data"]["contactPreference"] == "SMS"
    
    # Check SMS preference updated
    res_pref_check = await client.get("/api/v1/notifications/sms/preferences")
    assert res_pref_check.json()["data"]["contactPreference"] == "SMS"

@pytest.mark.asyncio
async def test_sms_send_and_inbound_webhook(authenticated_client: AsyncClient, async_client: AsyncClient, db_session):
    # Register/fetch phone number from authenticated user
    res_me = await authenticated_client.get("/api/v1/auth/me")
    assert res_me.status_code == 200
    phone_number = res_me.json()["data"]["phone_number"]
    
    # 1. Send template SMS (Internal endpoint)
    sms_payload = {
        "toPhoneNumber": phone_number,
        "templateId": "emergency_contact_notify",
        "variables": {
            "motherName": "Test Mother",
            "facilityName": "Test Hospital"
        }
    }
    res_sms = await async_client.post("/api/v1/notifications/sms/send", json=sms_payload)
    assert res_sms.status_code == 200
    assert res_sms.json()["data"]["status"] == "SENT"
    
    # 2. Create a check-in reminder
    due_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    reminder_payload = {
        "title": "Check-in reminder",
        "type": "CYCLE",
        "dueAt": due_at
    }
    res_rem = await authenticated_client.post("/api/v1/reminders", json=reminder_payload)
    assert res_rem.status_code == 201
    reminder_id = res_rem.json()["data"]["id"]
    
    # 3. Trigger inbound SMS webhook
    webhook_payload = {
        "from": phone_number,
        "text": "1", # Reply "1"
        "linkedReminderId": reminder_id
    }
    res_webhook = await async_client.post("/api/v1/notifications/sms/inbound-webhook", json=webhook_payload)
    assert res_webhook.status_code == 200
    
    # Verify reminder is marked done automatically
    res_rem_get = await authenticated_client.get("/api/v1/reminders")
    updated_rem = next(r for r in res_rem_get.json()["data"] if r["id"] == reminder_id)
    assert updated_rem["isDone"] is True

    # 4. Test SMS-based Vitals Logging
    # Start a pregnancy first
    preg_payload = {
        "dateInputType": "LMP",
        "lastMenstrualPeriod": "2026-05-01",
        "isFirstPregnancy": True
    }
    res_preg = await authenticated_client.post("/api/v1/pregnancy/start", json=preg_payload)
    assert res_preg.status_code == 201

    # Send vitals SMS message
    webhook_vitals_payload = {
        "from": phone_number,
        "text": "vitals bp 130/85 weight 74.5"
    }
    res_vitals_webhook = await async_client.post("/api/v1/notifications/sms/inbound-webhook", json=webhook_vitals_payload)
    assert res_vitals_webhook.status_code == 200

    # Fetch pregnancy vitals to verify it got logged in the database
    res_vitals = await authenticated_client.get("/api/v1/pregnancy/vitals")
    assert res_vitals.status_code == 200
    vitals_list = res_vitals.json()["data"]
    assert len(vitals_list) >= 1
    
    logged_vitals = vitals_list[0]
    # Answers contain systolicBp, diastolicBp, weightKg
    answers = logged_vitals["answers"]
    assert answers["systolicBp"] == 130
    assert answers["diastolicBp"] == 85
    assert answers["weightKg"] == 74.5

    # 5. Test GET FACILITIES, REGISTER FACILITY, and REQUEST DOCTOR SMS flows
    from app.models.facility import Facility
    from app.models.user import User, UserRole
    from app.models.staff import StaffMember, StaffStatus
    
    # Register facility in database
    facility = Facility(
        name="Test Facility West",
        county="Nairobi",
        sub_county="Westlands",
        latitude=-1.26,
        longitude=36.80,
        is_active=True
    )
    db_session.add(facility)
    await db_session.commit()
    await db_session.refresh(facility)
    
    # Register clinician in database
    clinician = User(
        phone_number="+254711223344",
        full_name="Doctor Tester",
        password_hash="fakehash",
        role=UserRole.CLINICIAN,
        account_type="FULL",
        gender="MALE"
    )
    db_session.add(clinician)
    await db_session.commit()
    await db_session.refresh(clinician)
    
    # Assign clinician to facility staff
    staff = StaffMember(
        facility_id=facility.id,
        user_id=clinician.id,
        role="CLINICIAN",
        status=StaffStatus.ACTIVE,
        is_on_duty=True
    )
    db_session.add(staff)
    await db_session.commit()
    
    # Test 5.1: get facilities
    webhook_get_payload = {
        "from": phone_number,
        "text": "get facilities nairobi"
    }
    res_get = await async_client.post("/api/v1/notifications/sms/inbound-webhook", json=webhook_get_payload)
    assert res_get.status_code == 200
    
    # Test 5.2: register facility Test Facility West
    webhook_reg_payload = {
        "from": phone_number,
        "text": "register facility Test Facility West"
    }
    res_reg_fac = await async_client.post("/api/v1/notifications/sms/inbound-webhook", json=webhook_reg_payload)
    assert res_reg_fac.status_code == 200
    
    # Test 5.3: request doctor
    webhook_req_payload = {
        "from": phone_number,
        "text": "request doctor"
    }
    res_req_doc = await async_client.post("/api/v1/notifications/sms/inbound-webhook", json=webhook_req_payload)
    assert res_req_doc.status_code == 200
    
    # Verify preferred facility and personal doctor assignment in profile
    res_profile = await authenticated_client.get("/api/v1/profile/me")
    assert res_profile.status_code == 200
    profile_data = res_profile.json()["data"]
    assert profile_data["preferred_facility_id"] == str(facility.id)
    assert profile_data["personal_doctor_id"] == str(clinician.id)
    assert profile_data["personal_doctor_request_status"] == "ASSIGNED"

def test_websocket_notification_connection():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    user_uuid = uuid.uuid4()
    with client.websocket_connect(f"/api/v1/notifications/ws/{user_uuid}") as websocket:
        # Connection establishes successfully
        pass



