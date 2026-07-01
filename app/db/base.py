from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Create the asynchronous engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={
        "ssl": "require",
        "statement_cache_size": 0,
    }
)

# Create the async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass
