import pytest
import uuid
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.profile import Profile, CurrentStage, NotificationPreference
from app.models.cycle import CycleEntry, FormSubmission, FormContext, FormTemplate
from app.models.notification import Notification
from app.services.reminder_service import send_vitals_reminders


@pytest.mark.asyncio
async def test_send_vitals_reminders_not_pregnant(db_session: AsyncSession):
    # 1. Setup template
    template = FormTemplate(
        id=uuid.uuid4(),
        slug="cycle-entry-test",
        context=FormContext.CYCLE_ENTRY,
        fields={},
        version="v1",
        is_active=True
    )
    db_session.add(template)
    await db_session.flush()

    # 2. Setup user and profile (NOT_PREGNANT)
    user = User(
        id=uuid.uuid4(),
        phone_number=f"+2547{str(uuid.uuid4().int)[:8]}",
        full_name="Cycle Test Patient",
        password_hash="hashed",
        role="USER"
    )
    db_session.add(user)
    await db_session.flush()

    profile = Profile(
        id=uuid.uuid4(),
        user_id=user.id,
        current_stage=CurrentStage.NOT_PREGNANT,
        notification_preference=NotificationPreference.NOTIFICATION,
        typical_cycle_length_days=28
    )
    db_session.add(profile)
    await db_session.flush()

    # Define common helper to check if notification exists
    async def get_notifications():
        await db_session.flush()
        stmt = select(Notification).where(Notification.user_id == user.id)
        res = await db_session.execute(stmt)
        return res.scalars().all()

    # Define helper to clear notifications between sub-test stages
    async def clear_notifications():
        stmt = select(Notification).where(Notification.user_id == user.id)
        res = await db_session.execute(stmt)
        for n in res.scalars().all():
            await db_session.delete(n)
        await db_session.flush()

    # Scenario A: Outside period, no cycle entries logged -> Morning run triggers monthly fallback reminder
    await send_vitals_reminders(db=db_session, is_morning=True)
    notifs = await get_notifications()
    assert len(notifs) == 1
    assert "Cycle Log Reminder" in notifs[0].title
    assert "update your menstrual cycle records" in notifs[0].body

    # Scenario B: Outside period, no cycle entries logged -> Evening run suppresses monthly fallback reminder
    await clear_notifications()
    await send_vitals_reminders(db=db_session, is_morning=False)
    notifs = await get_notifications()
    assert len(notifs) == 0

    # Scenario C: Active period (logged today, within 4 days assumption), but no log today yet -> Daily reminder is sent
    # Log period start as of yesterday (so it's day 2 of period)
    yesterday = date.today() - timedelta(days=1)
    sub = FormSubmission(
        id=uuid.uuid4(),
        template_id=template.id,
        user_id=user.id,
        context=FormContext.CYCLE_ENTRY,
        answers={},
        created_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db_session.add(sub)
    await db_session.flush()

    cycle_entry = CycleEntry(
        id=uuid.uuid4(),
        user_id=user.id,
        submission_id=sub.id,
        start_date=yesterday,
        end_date=None
    )
    db_session.add(cycle_entry)
    await db_session.flush()

    # Run reminders (either morning or evening) -> Daily reminder is sent
    await clear_notifications()
    await send_vitals_reminders(db=db_session, is_morning=False)
    notifs = await get_notifications()
    assert len(notifs) == 1
    assert "Daily Cycle Log Reminder" in notifs[0].title
    assert "log your flow levels and symptoms" in notifs[0].body

    # Scenario D: Active period, but user already logged today -> Daily reminder is NOT sent
    # Create submission today
    sub_today = FormSubmission(
        id=uuid.uuid4(),
        template_id=template.id,
        user_id=user.id,
        context=FormContext.CYCLE_SYMPTOM,
        answers={},
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(sub_today)
    await db_session.flush()

    await clear_notifications()
    await send_vitals_reminders(db=db_session, is_morning=False)
    notifs = await get_notifications()
    assert len(notifs) == 0

    # Scenario E: Outside period duration (>4 days default limit) -> fallback logic applies (not triggered because log is fresh)
    # Move start_date to 10 days ago (so period is long completed, end_date remains null)
    cycle_entry.start_date = date.today() - timedelta(days=10)
    db_session.add(cycle_entry)
    await db_session.flush()

    await clear_notifications()
    await send_vitals_reminders(db=db_session, is_morning=True)
    notifs = await get_notifications()
    assert len(notifs) == 0  # No reminder because last cycle entry is fresh (<30 days)
