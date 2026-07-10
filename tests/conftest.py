import pytest
import pytest_asyncio
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
