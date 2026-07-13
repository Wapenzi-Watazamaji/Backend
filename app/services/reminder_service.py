import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import reminder_repository
from app.models.reminder import Reminder, ReminderType
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.utils.exceptions import NotFoundError

async def create_reminder(db: AsyncSession, user_id: uuid.UUID, reminder_in: ReminderCreate) -> Reminder:
    reminder_data = reminder_in.model_dump()
    reminder_data["user_id"] = user_id
    reminder_data["is_done"] = False
    return await reminder_repository.create(db, reminder_data)

async def get_reminder_by_id(db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder:
    reminder = await reminder_repository.get_by_id(db, reminder_id)
    if not reminder or reminder.user_id != user_id:
        raise NotFoundError(message="Reminder not found")
    return reminder

async def list_reminders(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    upcoming_only: bool = False, 
    reminder_type: Optional[ReminderType] = None
) -> List[Reminder]:
    return await reminder_repository.get_by_user_id(db, user_id, upcoming_only, reminder_type)

async def update_reminder(db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID, reminder_in: ReminderUpdate) -> Reminder:
    reminder = await get_reminder_by_id(db, reminder_id, user_id)
    update_data = reminder_in.model_dump(exclude_unset=True)
    return await reminder_repository.update(db, reminder, update_data)

async def mark_reminder_done(db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder:
    reminder = await get_reminder_by_id(db, reminder_id, user_id)
    return await reminder_repository.update(db, reminder, {"is_done": True})

async def delete_reminder(db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID) -> None:
    reminder = await get_reminder_by_id(db, reminder_id, user_id)
    await reminder_repository.delete(db, reminder)

async def send_due_reminders(db: Optional[AsyncSession] = None) -> None:
    from app.db.base import AsyncSessionLocal
    from app.models.pregnancy import ScheduledVisit, PregnancyRecord, VisitStatus
    from app.models.postpartum import BabyProfile
    from app.models.user import User
    from app.models.facility import Facility
    from app.models.profile import Profile, NotificationPreference
    from app.models.notification import Notification
    from app.repositories import notification_repository, device_token_repository
    from app.utils.sms import send_sms, render_template
    from sqlalchemy import select
    from datetime import datetime, timedelta, time, timezone

    async def _process(session: AsyncSession):
        print("=== Checking upcoming Scheduled Visits for Tomorrow ===")
        today = datetime.now(timezone.utc).date()
        tomorrow = today + timedelta(days=1)
        tomorrow_start = datetime.combine(tomorrow, time.min, tzinfo=timezone.utc)
        tomorrow_end = datetime.combine(tomorrow, time.max, tzinfo=timezone.utc)
        
        # 1. Pregnancy scheduled visits
        pregnancy_stmt = (
            select(ScheduledVisit, User, Facility, Profile)
            .join(PregnancyRecord, ScheduledVisit.pregnancy_id == PregnancyRecord.id)
            .join(User, PregnancyRecord.user_id == User.id)
            .outerjoin(Profile, User.id == Profile.user_id)
            .outerjoin(Facility, ScheduledVisit.facility_id == Facility.id)
            .where(
                ScheduledVisit.status == VisitStatus.SCHEDULED,
                ScheduledVisit.scheduled_at >= tomorrow_start,
                ScheduledVisit.scheduled_at <= tomorrow_end
            )
        )
        
        preg_results = await session.execute(pregnancy_stmt)
        preg_visits = preg_results.all()
        
        # 2. Baby postnatal / vaccination scheduled visits
        baby_stmt = (
            select(ScheduledVisit, User, Facility, Profile)
            .join(BabyProfile, ScheduledVisit.baby_id == BabyProfile.id)
            .join(User, BabyProfile.user_id == User.id)
            .outerjoin(Profile, User.id == Profile.user_id)
            .outerjoin(Facility, ScheduledVisit.facility_id == Facility.id)
            .where(
                ScheduledVisit.status == VisitStatus.SCHEDULED,
                ScheduledVisit.scheduled_at >= tomorrow_start,
                ScheduledVisit.scheduled_at <= tomorrow_end
            )
        )
        
        baby_results = await session.execute(baby_stmt)
        baby_visits = baby_results.all()
        
        all_visits = preg_visits + baby_visits
        processed_count = 0
        sms_sent = 0
        push_sent = 0
        
        for visit, user, facility, profile in all_visits:
            fac_name = facility.name if facility else "the health facility"
            app_date = visit.scheduled_at.strftime('%Y-%m-%d %H:%M')
            
            message = render_template(
                template_id="appointment_reminder",
                variables={
                    "motherName": user.full_name,
                    "facilityName": fac_name,
                    "appointmentDate": app_date
                }
            )
            
            # Determine preference: default to BOTH if no profile/preference set
            pref = NotificationPreference.BOTH
            if profile and profile.notification_preference:
                pref = profile.notification_preference
                
            # A. Process SMS (if preference is SMS or BOTH)
            if pref in (NotificationPreference.SMS, NotificationPreference.BOTH):
                print(f"Sending SMS reminder to {user.full_name} ({user.phone_number})...")
                res = await send_sms(user.phone_number, message)
                if res.get("status") == "SENT":
                    sms_sent += 1
            
            # B. Process In-App & Push Notification (if preference is NOTIFICATION or BOTH)
            if pref in (NotificationPreference.NOTIFICATION, NotificationPreference.BOTH):
                # 1. Create in-app Notification record
                notif_data = {
                    "user_id": user.id,
                    "category": "APPOINTMENT_REMINDER",
                    "title": "Upcoming Visit Reminder",
                    "body": message,
                    "is_read": False,
                    "related_entity_type": "SCHEDULED_VISIT",
                    "related_entity_id": str(visit.id)
                }
                await notification_repository.create(session, notif_data)
                
                # 2. Trigger Push Notification to registered device tokens
                tokens = await device_token_repository.get_by_user_id(session, user.id)
                if tokens:
                    from app.utils.firebase import send_push_notification
                    for t in tokens:
                        await send_push_notification(
                            token=t.device_token,
                            title="Upcoming Visit Reminder",
                            body=message,
                            data={"visitId": str(visit.id)}
                        )
                        push_sent += 1
                else:
                    print(f"In-App Notification saved for {user.full_name}. (No registered FCM device tokens found).")
            
            processed_count += 1
            
        print(f"Processed {processed_count} visits. Sent {sms_sent} SMS reminders, and triggered {push_sent} mock Push Notifications.")

    if db is None:
        async with AsyncSessionLocal() as session:
            await _process(session)
    else:
        await _process(db)

async def send_vitals_reminders(db: Optional[AsyncSession] = None, is_morning: bool = True) -> None:
    from app.db.base import AsyncSessionLocal
    from app.models.profile import Profile, CurrentStage, NotificationPreference
    from app.models.cycle import FormSubmission, FormContext
    from app.models.user import User
    from app.models.postpartum import BabyProfile
    from app.repositories import notification_repository, device_token_repository
    from app.utils.firebase import send_push_notification
    from app.utils.sms import send_sms
    from sqlalchemy import select, desc
    from datetime import datetime, timezone, timedelta

    async def _process(session: AsyncSession):
        print("=== Checking Vitals Tracking Compliance ===")
        now = datetime.now(timezone.utc)
        
        # Query all active user profiles
        stmt = select(Profile, User).join(User, Profile.user_id == User.id)
        results = await session.execute(stmt)
        profiles = results.all()
        
        for profile, user in profiles:
            pref = profile.notification_preference or NotificationPreference.BOTH
            
            # Helper to dispatch notification/SMS
            async def notify_user(title: str, body: str):
                if pref in (NotificationPreference.SMS, NotificationPreference.BOTH):
                    print(f"Sending vitals reminder SMS to {user.full_name} ({user.phone_number})...")
                    await send_sms(user.phone_number, body)
                if pref in (NotificationPreference.NOTIFICATION, NotificationPreference.BOTH):
                    notif_data = {
                        "user_id": user.id,
                        "category": "VITALS_REMINDER",
                        "title": title,
                        "body": body,
                        "is_read": False,
                        "related_entity_type": "USER_PROFILE",
                        "related_entity_id": str(profile.id)
                    }
                    await notification_repository.create(session, notif_data)
                    
                    tokens = await device_token_repository.get_by_user_id(session, user.id)
                    if tokens:
                        for t in tokens:
                            await send_push_notification(
                                token=t.device_token,
                                title=title,
                                body=body,
                                data={"category": "VITALS_REMINDER"}
                            )
            
            # 1. Pregnancy Vitals Check (7 days)
            if profile.current_stage == CurrentStage.PREGNANT:
                sub_stmt = (
                    select(FormSubmission)
                    .where(
                        FormSubmission.user_id == user.id,
                        FormSubmission.context == FormContext.PREGNANCY_VITALS
                    )
                    .order_by(desc(FormSubmission.created_at))
                    .limit(1)
                )
                sub_res = await session.execute(sub_stmt)
                last_sub = sub_res.scalar_one_or_none()
                
                if not last_sub or (now - last_sub.created_at) > timedelta(days=7):
                    title = "Pregnancy Vitals Reminder"
                    body = f"Hi {user.full_name}, it has been a week since your last vitals check-in. Please log your current blood pressure and weight in the app."
                    await notify_user(title, body)
            
            # 2. Menstrual Cycle Check (Daily during period, Monthly fallback outside period)
            elif profile.current_stage == CurrentStage.NOT_PREGNANT:
                from app.models.cycle import CycleEntry
                cycle_stmt = (
                    select(CycleEntry)
                    .where(CycleEntry.user_id == user.id)
                    .order_by(desc(CycleEntry.start_date))
                    .limit(1)
                )
                cycle_res = await session.execute(cycle_stmt)
                last_cycle = cycle_res.scalar_one_or_none()
                
                is_active_period = False
                today_val = now.date()
                
                if last_cycle:
                    if last_cycle.end_date:
                        is_active_period = last_cycle.start_date <= today_val <= last_cycle.end_date
                    else:
                        # If end_date is not set yet, default to assuming a 4-day period duration
                        is_active_period = last_cycle.start_date <= today_val <= (last_cycle.start_date + timedelta(days=3))
                
                if is_active_period:
                    # Check if they have already submitted a log today
                    today_start = datetime.combine(today_val, datetime.min.time()).replace(tzinfo=timezone.utc)
                    sub_today_stmt = (
                        select(FormSubmission)
                        .where(
                            FormSubmission.user_id == user.id,
                            FormSubmission.context.in_([FormContext.CYCLE_ENTRY, FormContext.CYCLE_SYMPTOM]),
                            FormSubmission.created_at >= today_start
                        )
                        .limit(1)
                    )
                    sub_today_res = await session.execute(sub_today_stmt)
                    has_submitted_today = sub_today_res.scalar_one_or_none() is not None
                    
                    if not has_submitted_today:
                        title = "Daily Cycle Log Reminder"
                        body = f"Hi {user.full_name}, don't forget to log your flow levels and symptoms for today's period check-in."
                        await notify_user(title, body)
                else:
                    # Outside period: Send monthly fallback reminder only during the morning run (9 AM)
                    if is_morning:
                        sub_stmt = (
                            select(FormSubmission)
                            .where(
                                FormSubmission.user_id == user.id,
                                FormSubmission.context == FormContext.CYCLE_ENTRY
                            )
                            .order_by(desc(FormSubmission.created_at))
                            .limit(1)
                        )
                        sub_res = await session.execute(sub_stmt)
                        last_sub = sub_res.scalar_one_or_none()
                        
                        if not last_sub or (now - last_sub.created_at) > timedelta(days=30):
                            title = "Cycle Log Reminder"
                            body = f"Hi {user.full_name}, keep your period tracking accurate! Please update your menstrual cycle records in the app."
                            await notify_user(title, body)
                    
            # 3. Baby Vitals Check (14 days)
            elif profile.current_stage == CurrentStage.POSTPARTUM:
                baby_stmt = select(BabyProfile).where(BabyProfile.user_id == user.id)
                baby_res = await session.execute(baby_stmt)
                babies = baby_res.scalars().all()
                
                for baby in babies:
                    sub_stmt = (
                        select(FormSubmission)
                        .where(
                            FormSubmission.user_id == user.id,
                            FormSubmission.context == FormContext.BABY_VITALS
                        )
                        .order_by(desc(FormSubmission.created_at))
                        .limit(1)
                    )
                    sub_res = await session.execute(sub_stmt)
                    last_sub = sub_res.scalar_one_or_none()
                    
                    if not last_sub or (now - last_sub.created_at) > timedelta(days=14):
                        title = "Baby Vitals Reminder"
                        body = f"Hi {user.full_name}, please log current weight and growth vitals for {baby.name} to keep track of their healthy progress."
                        await notify_user(title, body)

    if db is None:
        async with AsyncSessionLocal() as session:
            await _process(session)
    else:
        await _process(db)


