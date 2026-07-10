import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient

def generate_phone() -> str:
    return f"+2547{str(uuid.uuid4().int)[:8]}"

@pytest_asyncio.fixture(scope="function")
async def authenticated_client(async_client: AsyncClient):
    # Register and login a new user to get an access token
    phone = generate_phone()
    register_payload = {
        "phone_number": phone,
        "full_name": "Test Profile User",
        "password": "SecurePassword123!",
        "role": "USER",
        "date_of_birth": "1990-01-01",
        "gender": "FEMALE"
    }
    await async_client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "phone_number": phone,
        "password": "SecurePassword123!"
    }
    login_res = await async_client.post("/api/v1/auth/login", json=login_payload)
    token = login_res.json()["data"]["access_token"]
    
    # Create a new client with the authorization header
    # We yield the same async_client but with headers updated
    async_client.headers.update({"Authorization": f"Bearer {token}"})
    yield async_client
    async_client.headers.pop("Authorization", None)

@pytest.mark.asyncio
async def test_create_and_get_profile(authenticated_client: AsyncClient):
    profile_payload = {
        "current_stage": "NOT_PREGNANT",
        "emergency_contact": {
            "name": "John Doe",
            "relationship": "Husband",
            "phone": "+254700000000"
        },
        "typical_cycle_length_days": 28
    }
    # Create profile
    res_create = await authenticated_client.post("/api/v1/profile/me", json=profile_payload)
    assert res_create.status_code == 201
    data_create = res_create.json()["data"]
    assert data_create["typical_cycle_length_days"] == 28

    # Get profile
    res_get = await authenticated_client.get("/api/v1/profile/me")
    assert res_get.status_code == 200
    data_get = res_get.json()["data"]
    assert data_get["typical_cycle_length_days"] == 28
    assert data_get["emergency_contact"]["name"] == "John Doe"

@pytest.mark.asyncio
async def test_update_profile(authenticated_client: AsyncClient):
    # Setup initial profile
    profile_payload = {
        "typical_cycle_length_days": 28
    }
    await authenticated_client.post("/api/v1/profile/me", json=profile_payload)

    # Update profile
    update_payload = {
        "typical_cycle_length_days": 30,
        "home_address_name": "Nairobi, Kenya"
    }
    res_update = await authenticated_client.put("/api/v1/profile/me", json=update_payload)
    assert res_update.status_code == 200
    data_update = res_update.json()["data"]
    assert data_update["typical_cycle_length_days"] == 30
    assert data_update["home_address_name"] == "Nairobi, Kenya"

@pytest.mark.asyncio
async def test_qr_token_flow(authenticated_client: AsyncClient):
    # Setup profile first
    await authenticated_client.post("/api/v1/profile/me", json={"typical_cycle_length_days": 28})

    # Get QR token
    res_qr = await authenticated_client.get("/api/v1/profile/me/qr")
    assert res_qr.status_code == 200
    qr_data = res_qr.json()["data"]
    assert "qr_passport_token" in qr_data
    token = qr_data["qr_passport_token"]

    # Refresh QR token
    res_refresh = await authenticated_client.post("/api/v1/profile/me/qr/refresh")
    assert res_refresh.status_code == 200
    new_qr_data = res_refresh.json()["data"]
    assert "qr_passport_token" in new_qr_data
    new_token = new_qr_data["qr_passport_token"]
    assert token != new_token

    # Scan the new token
    res_scan = await authenticated_client.get(f"/api/v1/profile/qr/scan/{new_token}")
    assert res_scan.status_code == 200
    scan_data = res_scan.json()["data"]
    assert scan_data["user"]["full_name"] == "Test Profile User"
    assert scan_data["profile"]["typical_cycle_length_days"] == 28

@pytest.mark.asyncio
async def test_scan_invalid_qr_token(async_client: AsyncClient):
    res_scan = await async_client.get("/api/v1/profile/qr/scan/invalid-token-123")
    # Should probably be 404 or 401/400 depending on implementation
    assert res_scan.status_code in [400, 401, 404, 422]
