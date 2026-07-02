import asyncio
from app.db.base import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        await session.execute(text("UPDATE alembic_version SET version_num = '37f287bc5357'"))
        await session.commit()
        print("Updated alembic_version to 37f287bc5357")

asyncio.run(main())
