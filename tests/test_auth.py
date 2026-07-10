import pytest
import uuid
from httpx import AsyncClient

def generate_phone() -> str:
    # generate a dummy phone number e.g. +254700... + 4 random digits
    return f"+2547{str(uuid.uuid4().int)[:8]}"

@pytest.mark.asyncio
async def test_register_full_account(async_client: AsyncClient):
    payload = {
        "phone_number": generate_phone(),
        "full_name": "Test User",
        "password": "SecurePassword123!",
        "role": "USER",
        "date_of_birth": "1990-01-01",
        "gender": "FEMALE",
        "preferred_language": "en"
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]
    assert data["data"]["phone_number"] == payload["phone_number"]

@pytest.mark.asyncio
async def test_register_sms_only_account(async_client: AsyncClient):
    payload = {
        "phone_number": generate_phone(),
        "full_name": "SMS User",
        "role": "USER",
        "preferred_language": "en"
    }
    response = await async_client.post("/api/v1/auth/register-sms-only", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    phone = generate_phone()
    register_payload = {
        "phone_number": phone,
        "full_name": "Test Login User",
        "password": "SecurePassword123!",
        "role": "USER",
        "date_of_birth": "1995-05-05",
        "gender": "FEMALE"
    }
    await async_client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "phone_number": phone,
        "password": "SecurePassword123!"
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]

@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient):
    login_payload = {
        "phone_number": generate_phone(),
        "password": "WrongPassword!"
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False

@pytest.mark.asyncio
async def test_token_refresh(async_client: AsyncClient):
    phone = generate_phone()
    register_payload = {
        "phone_number": phone,
        "full_name": "Refresh User",
        "password": "SecurePassword123!",
        "role": "USER"
    }
    await async_client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "phone_number": phone,
        "password": "SecurePassword123!"
    }
    login_res = await async_client.post("/api/v1/auth/login", json=login_payload)
    refresh_token = login_res.json()["data"]["refresh_token"]

    refresh_payload = {"refresh_token": refresh_token}
    refresh_res = await async_client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data["data"]