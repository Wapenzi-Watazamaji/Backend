import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.session import get_db
from app.core.config import settings

from sqlalchemy.pool import NullPool

from sqlalchemy.pool import NullPool

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={
            "ssl": "require",
            "server_settings": {"application_name": "binticare_test"},
        }
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    async with db_engine.connect() as conn:
        transaction = await conn.begin()
        
        async_session = AsyncSession(
            bind=conn, 
            join_transaction_mode="create_savepoint", 
            expire_on_commit=False
        )
        
        try:
            yield async_session
        finally:
            await async_session.close()
            await transaction.rollback()

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

def generate_phone() -> str:
    return f"+2547{str(uuid.uuid4().int)[:8]}"

@pytest_asyncio.fixture(scope="function")
async def authenticated_client(async_client: AsyncClient):
    phone = generate_phone()
    register_payload = {
        "phone_number": phone,
        "full_name": "Test Patient",
        "password": "SecurePassword123!",
        "role": "USER",
        "date_of_birth": "1990-01-01",
        "gender": "FEMALE"
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=register_payload)
    user_id = reg_res.json()["data"]["id"]

    login_res = await async_client.post("/api/v1/auth/login", json={"phone_number": phone, "password": "SecurePassword123!"})
    token = login_res.json()["data"]["access_token"]
    
    async_client.headers.update({"Authorization": f"Bearer {token}"})
    # Attach user info for convenience in tests
    async_client.user_id = user_id
    yield async_client
    async_client.headers.pop("Authorization", None)

@pytest_asyncio.fixture(scope="function")
async def clinician_client(async_client: AsyncClient):
    phone = generate_phone()
    register_payload = {
        "phone_number": phone,
        "full_name": "Test Clinician",
        "password": "SecurePassword123!",
        "role": "CLINICIAN",
        "date_of_birth": "1985-01-01",
        "gender": "MALE"
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=register_payload)
    user_id = reg_res.json()["data"]["id"]

    login_res = await async_client.post("/api/v1/auth/login", json={"phone_number": phone, "password": "SecurePassword123!"})
    token = login_res.json()["data"]["access_token"]
    
    # Let's create a new AsyncClient instance for the clinician so it doesn't conflict
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers.update({"Authorization": f"Bearer {token}"})
        client.user_id = user_id
        yield client
