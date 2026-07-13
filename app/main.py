from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.api.router import api_router
from app.services.reminder_service import send_due_reminders, send_vitals_reminders

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    
    # 1. Appointment Reminders: Daily at 8:00 AM
    trigger_app = CronTrigger(hour=8, minute=0)
    scheduler.add_job(send_due_reminders, trigger_app, name="daily_reminders")
    
    # Run once, 5 seconds after startup (for validation)
    run_time_app = datetime.now(timezone.utc) + timedelta(seconds=5)
    scheduler.add_job(send_due_reminders, 'date', run_date=run_time_app, name="startup_reminders")
    
    # 2. Vitals compliance check: Daily at 9:00 AM (morning) and 8:00 PM (evening)
    trigger_vitals_morning = CronTrigger(hour=9, minute=0)
    scheduler.add_job(send_vitals_reminders, trigger_vitals_morning, name="daily_vitals_check_morning", kwargs={"is_morning": True})
    
    trigger_vitals_evening = CronTrigger(hour=20, minute=0)
    scheduler.add_job(send_vitals_reminders, trigger_vitals_evening, name="daily_vitals_check_evening", kwargs={"is_morning": False})
    
    # Run once, 10 seconds after startup (for validation)
    run_time_vitals = datetime.now(timezone.utc) + timedelta(seconds=10)
    scheduler.add_job(send_vitals_reminders, 'date', run_date=run_time_vitals, name="startup_vitals_check", kwargs={"is_morning": True})
    
    scheduler.start()
    print("=== APScheduler started: daily reminders (8 AM) and vitals checks (9 AM & 8 PM) active ===")
    
    yield
    
    scheduler.shutdown()
    print("=== APScheduler shut down ===")

app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.include_router(api_router, prefix="/api/v1")

from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.exceptions import BaseAppException

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response_dict()
    )

from sqlalchemy.exc import IntegrityError
from fastapi import status

@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "data": None,
            "meta": None,
            "error": {
                "code": "CONFLICT",
                "message": "A record with these unique constraints already exists."
            }
        }
    )

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "project": settings.PROJECT_NAME}

