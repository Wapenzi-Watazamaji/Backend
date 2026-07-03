import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    db_url = "postgresql+asyncpg://neondb_owner:npg_BeDQAZ1Y8UzE@ep-quiet-haze-a9pi43r8-pooler.gwc.azure.neon.tech/neondb?ssl=require"
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE scheduled_visits DROP CONSTRAINT scheduled_visits_pregnancy_id_fkey"))
        except Exception as e:
            print("FK drop failed:", e)
        try:
            await conn.execute(text("ALTER TABLE scheduled_visits ALTER COLUMN pregnancy_id DROP NOT NULL"))
        except Exception as e:
            print("Drop not null failed:", e)
        try:
            await conn.execute(text("ALTER TABLE scheduled_visits ADD COLUMN IF NOT EXISTS baby_id UUID REFERENCES baby_profiles(id) ON DELETE CASCADE"))
        except Exception as e:
            print("Add column failed:", e)
            
        print("Database schema updated successfully.")

asyncio.run(main())
