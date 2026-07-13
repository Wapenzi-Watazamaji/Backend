import asyncio
from app.services.reminder_service import send_due_reminders

async def main():
    await send_due_reminders()

if __name__ == "__main__":
    asyncio.run(main())
