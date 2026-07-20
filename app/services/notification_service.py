from app.models.user import User
import uuid
import logging
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import notification_repository, device_token_repository, user_repository, cycle_repository, profile_repository
from app.models.notification import Notification
from app.models.device_token import DeviceToken
from app.models.profile import NotificationPreference
from app.models.cycle import FormContext, FormTemplate
from app.models.reminder import Reminder
from app.schemas.notification import DeviceRegisterRequest, SmsSendRequest, SmsInboundWebhook
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.sms import send_sms, render_template

logger = logging.getLogger(__name__)

async def list_notifications(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    unread_only: bool = False, 
    page: int = 1, 
    page_size: int = 20
) -> Tuple[List[Notification], int]:
    limit = page_size
    offset = (page - 1) * page_size
    return await notification_repository.get_by_user_id(db, user_id, unread_only, limit, offset)

async def mark_notification_read(db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
    notification = await notification_repository.get_by_id(db, notification_id)
    if not notification or notification.user_id != user_id:
        raise NotFoundError(message="Notification not found")
    return await notification_repository.update(db, notification, {"is_read": True})

async def register_device_token(db: AsyncSession, user_id: uuid.UUID, device_in: DeviceRegisterRequest) -> DeviceToken:
    # Check if this token is already registered
    existing_token = await device_token_repository.get_by_token(db, device_in.device_token)
    if existing_token:
        if existing_token.user_id == user_id:
            return existing_token
        else:
            await device_token_repository.delete(db, existing_token)
            
    token_data = device_in.model_dump()
    token_data["user_id"] = user_id
    return await device_token_repository.create(db, token_data)

async def unregister_device_token(db: AsyncSession, token_id: uuid.UUID, user_id: uuid.UUID) -> None:
    token = await device_token_repository.get_by_id(db, token_id)
    if not token or token.user_id != user_id:
        raise NotFoundError(message="Device token not found")
    await device_token_repository.delete(db, token)

async def send_templated_sms(db: AsyncSession, req: SmsSendRequest) -> dict:
    message = render_template(req.template_id, req.variables)
    res = await send_sms(req.to_phone_number, message)
    return res

async def inbound_sms_reply(db: AsyncSession, webhook: SmsInboundWebhook) -> None:
    # 1. Find user by phone number
    user = await user_repository.get_by_phone_number(db, webhook.from_number)
    if not user:
        raise NotFoundError(message="User not found for this phone number")
        
    # 2. Check if the message is a vitals submission (e.g. starts with "vitals")
    text_clean = webhook.text.strip().lower()
    if text_clean.startswith("vitals"):
        import re
        from app.utils.sms import send_sms
        
        # Parse BP (systolic/diastolic) and Weight
        bp_match = re.search(r'(\d{2,3})/(\d{2,3})', text_clean)
        systolic, diastolic, weight = None, None, None
        
        cleaned_text = text_clean
        if bp_match:
            systolic = int(bp_match.group(1))
            diastolic = int(bp_match.group(2))
            cleaned_text = text_clean.replace(bp_match.group(0), "")
            
        weight_match = re.search(r'(?:wt|weight)?\s*(\d{2,3}(?:\.\d+)?)', cleaned_text)
        if weight_match:
            weight = float(weight_match.group(1))
            
        if systolic is None or diastolic is None or weight is None:
            reply_msg = "BintiCare: Invalid format. Please reply in this format: vitals <blood_pressure> <weight>. Example: vitals 120/80 65"
            await send_sms(webhook.from_number, reply_msg)
            return
        
        # Acknowledge immediately before heavy processing
        await send_sms(webhook.from_number, "BintiCare: Recording your vitals, please wait...")
            
        # Create vitals entry using the pregnancy service
        from app.services import pregnancy_service
        from app.utils.exceptions import NoActivePregnancyError
        
        class SmsVitalsPayload:
            def __init__(self, sys, dia, wt):
                self.templateSlug = "tmpl_preg_vitals_v1"
                self.answers = {
                    "systolicBp": sys,
                    "diastolicBp": dia,
                    "weightKg": wt,
                    "symptoms": []
                }
                self.clientGeneratedId = None
                self.clientCreatedAt = None
                
        try:
            await pregnancy_service.create_vitals(db, user.id, SmsVitalsPayload(systolic, diastolic, weight))
            confirm_msg = f"BintiCare: Thank you {user.full_name}! We have recorded your vitals: Blood Pressure {systolic}/{diastolic} mmHg, Weight {weight} kg."
            await send_sms(webhook.from_number, confirm_msg)
            return
        except NoActivePregnancyError:
            reply_msg = "BintiCare: No active pregnancy record found for your account. If you are postpartum, please log baby vitals in the mobile app."
            await send_sms(webhook.from_number, reply_msg)
            return
        except Exception as e:
            logger.error(f"Error saving vitals via SMS: {e}")
            reply_msg = "BintiCare: An error occurred while saving your vitals. Please try again later."
            await send_sms(webhook.from_number, reply_msg)
            return

    # 3a. GET FACILITIES intent (Listing)
    if text_clean.startswith("get facilities"):
        from app.models.facility import Facility
        from sqlalchemy import select
        from app.utils.sms import send_sms
        
        parts = webhook.text.strip().split(None, 2)
        county = parts[2] if len(parts) > 2 else None
        
        if county:
            stmt = select(Facility).where(Facility.county.ilike(f"%{county}%"), Facility.is_active == True)
        else:
            stmt = select(Facility).where(Facility.is_active == True).limit(5)
            
        res = await db.execute(stmt)
        facilities = res.scalars().all()
        
        if not facilities:
            msg = "BintiCare: No active facilities found. Try listing without specifying county."
        else:
            fac_list = []
            for f in facilities:
                fac_list.append(f"{f.name} in {f.county} (ID: {str(f.id)[:8]})")
            msg = "BintiCare Available Facilities:\n" + "\n".join(fac_list) + "\nReply with GET FACILITY <name> for details, or REGISTER FACILITY <name>."
            
        await send_sms(webhook.from_number, msg)
        return

    # 3b. GET FACILITY intent (Specific Details)
    if text_clean.startswith("get facility"):
        from app.models.facility import Facility
        from sqlalchemy import select, cast, String
        from app.utils.sms import send_sms
        
        parts = webhook.text.strip().split(None, 2)
        if len(parts) < 3:
            await send_sms(webhook.from_number, "BintiCare: Please specify the facility name or ID. Example: GET FACILITY Pumwani")
            return
            
        target = parts[2]
        stmt = select(Facility).where(
            (Facility.name.ilike(f"%{target}%")) | 
            (cast(Facility.id, String).like(f"{target}%"))
        )
        res = await db.execute(stmt)
        facility = res.scalar_one_or_none()
        
        if not facility:
            await send_sms(webhook.from_number, f"BintiCare: Facility '{target}' not found. Reply with GET FACILITIES to search.")
        else:
            services = ", ".join(facility.services_offered) if facility.services_offered else "General Care"
            phone = facility.phone_number or "N/A"
            msg = f"BintiCare Facility Profile:\n{facility.name}\nCounty: {facility.county}\nPhone: {phone}\nServices: {services}\n\nTo register here, reply: REGISTER FACILITY {facility.name}"
            await send_sms(webhook.from_number, msg)
        return

    # 4. REGISTER FACILITY intent
    if text_clean.startswith("register facility"):
        from app.models.facility import Facility
        from app.models.profile import Profile
        from sqlalchemy import select, cast, String
        from app.utils.sms import send_sms
        
        parts = webhook.text.strip().split(None, 2)
        if len(parts) < 3:
            await send_sms(webhook.from_number, "BintiCare: Please specify the facility name or ID. Example: REGISTER FACILITY Karen Health Center")
            return
            
        target = parts[2]
        stmt = select(Facility).where(
            (Facility.name.ilike(f"%{target}%")) | 
            (cast(Facility.id, String).like(f"{target}%"))
        )
        res = await db.execute(stmt)
        facility = res.scalar_one_or_none()
        
        if not facility:
            await send_sms(webhook.from_number, f"BintiCare: Facility '{target}' not found. Reply with GET FACILITIES to search.")
            return
            
        profile = await profile_repository.get_by_user_id(db, user.id)
        if not profile:
            profile = await profile_repository.create(db, user.id)
            
        await profile_repository.update(db, profile, {"preferred_facility_id": facility.id})
        await db.commit()
        
        msg = f"BintiCare: You are now registered with {facility.name}! Reply with REQUEST DOCTOR to get a personal doctor assigned from this facility."
        await send_sms(webhook.from_number, msg)
        return

    # 5. REQUEST DOCTOR intent
    if text_clean.startswith("request doctor"):
        from app.models.profile import Profile, DoctorRequestStatus
        from app.models.staff import StaffMember, StaffStatus
        from app.models.user import UserRole
        from app.models.facility import Facility
        from sqlalchemy import select
        from app.utils.sms import send_sms
        
        # Acknowledge immediately before heavy processing
        await send_sms(webhook.from_number, "BintiCare: Processing your doctor request, please wait...")
        
        profile = await profile_repository.get_by_user_id(db, user.id)
        if not profile or not profile.preferred_facility_id:
            await send_sms(webhook.from_number, "BintiCare: Please register with a facility first by replying: REGISTER FACILITY <name>")
            return
            
        facility = await db.get(Facility, profile.preferred_facility_id)
        fac_name = facility.name if facility else "your registered clinic"
        
        if profile.personal_doctor_id:
            doc = await db.get(User, profile.personal_doctor_id)
            doc_name = doc.full_name if doc else "your assigned doctor"
            await send_sms(webhook.from_number, f"BintiCare: Dr. {doc_name} is already assigned to you.")
            return
            
        # Look for an active clinician at this facility
        stmt = (
            select(User)
            .join(StaffMember, StaffMember.user_id == User.id)
            .where(
                StaffMember.facility_id == profile.preferred_facility_id,
                User.role == UserRole.CLINICIAN
            )
            .limit(1)
        )
        res = await db.execute(stmt)
        clinician = res.scalar_one_or_none()
            
        if clinician:
            await profile_repository.update(db, profile, {
                "personal_doctor_id": clinician.id,
                "personal_doctor_request_status": DoctorRequestStatus.ASSIGNED
            })
            await db.commit()
            
            # Send SMS to patient
            msg = f"BintiCare: Dr. {clinician.full_name} has been assigned to you. They will monitor your vitals and checks."
            await send_sms(webhook.from_number, msg)
            
            # Trigger SMS and in-app alert to the assigned clinician
            try:
                from app.repositories import notification_repository
                
                doc_msg = f"BintiCare Clinician Alert: A new patient {user.full_name} has been assigned to you from {fac_name}."
                await notification_repository.create(db, {
                    "user_id": clinician.id,
                    "category": "PATIENT_ASSIGNED",
                    "title": "New Patient Assigned",
                    "body": doc_msg,
                    "is_read": False,
                    "related_entity_type": "USER",
                    "related_entity_id": str(user.id)
                })
                await send_sms(clinician.phone_number, doc_msg)
            except Exception as e:
                logger.warning(f"Failed to alert clinician of patient assignment: {e}")
        else:
            await profile_repository.update(db, profile, {
                "personal_doctor_request_status": DoctorRequestStatus.PENDING
            })
            await db.commit()
            msg = f"BintiCare: Your request for a personal doctor at {fac_name} is pending clinician assignment. We will alert you once assigned."
            await send_sms(webhook.from_number, msg)
            
        return

    # 5a. HELP/EMERGENCY intent
    if text_clean in ["help", "emergency", "danger", "sos"]:
        from app.models.profile import Profile
        from app.models.emergency import EmergencyRequest, EmergencyStatus
        from app.models.facility import Facility
        from app.utils.sms import send_sms
        from app.repositories import notification_repository
        
        # Acknowledge immediately — emergencies need instant feedback
        await send_sms(webhook.from_number, "BintiCare: Your emergency request is being processed. Stay calm, help is on the way.")
        
        profile = await profile_repository.get_by_user_id(db, user.id)
        if profile and profile.preferred_facility_id:
            em_req = EmergencyRequest(
                patient_id=user.id,
                facility_id=profile.preferred_facility_id,
                status=EmergencyStatus.PENDING,
                notes="Triggered via SMS Panic Button"
            )
            db.add(em_req)
            await db.commit()
            
            facility = await db.get(Facility, profile.preferred_facility_id)
            fac_name = facility.name if facility else "your facility"
            
            msg = f"BintiCare EMERGENCY: We have notified {fac_name}. Please head to the hospital immediately or call their emergency line."
            await send_sms(webhook.from_number, msg)
            
            try:
                alert_msg = f"EMERGENCY ALERT: Patient {user.full_name} ({user.phone_number}) triggered an SOS via SMS."
                if profile.personal_doctor_id:
                    await notification_repository.create(db, {
                        "user_id": profile.personal_doctor_id,
                        "category": "EMERGENCY",
                        "title": "EMERGENCY ALERT",
                        "body": alert_msg,
                        "is_read": False,
                        "related_entity_type": "EMERGENCY",
                        "related_entity_id": str(em_req.id)
                    })
            except Exception as e:
                logger.warning(f"Failed to send emergency alert to doctor: {e}")
        else:
            msg = "BintiCare EMERGENCY: You are not registered to a facility. Please go to the nearest hospital immediately or call 999."
            await send_sms(webhook.from_number, msg)
            
        return

    # 5b. MENU/TIPS intent
    if text_clean in ["menu", "tips", "info"]:
        from app.utils.sms import send_sms
        
        if text_clean == "tips":
            msg = "BintiCare Tips: Eat iron-rich foods like spinach and beans. Drink plenty of water. Rest when tired. Reply MENU for more options."
        else:
            msg = (
                "BintiCare Menu:\n"
                "1. VITALS <bp> <weight> - log vitals\n"
                "2. STATUS - pregnancy summary\n"
                "3. NEXT VISIT - upcoming appointment\n"
                "4. MY DOCTOR - your doctor's info\n"
                "5. EVENTS - facility events\n"
                "6. GET FACILITIES - search hospitals\n"
                "7. REQUEST DOCTOR - get assigned\n"
                "8. HELP - emergencies\n"
                "9. TIPS - pregnancy advice"
            )
            
        await send_sms(webhook.from_number, msg)
        return

    # 6. STATUS intent — pregnancy snapshot
    if text_clean == "status":
        from app.utils.sms import send_sms
        from app.repositories import pregnancy_repository
        from datetime import date as date_type
        
        await send_sms(webhook.from_number, "BintiCare: Fetching your status...")
        
        profile = await profile_repository.get_by_user_id(db, user.id)
        pregnancy = await pregnancy_repository.get_active_pregnancy(db, user.id)
        
        if not pregnancy:
            await send_sms(webhook.from_number, "BintiCare: No active pregnancy on record. If you are pregnant, please register through the app or contact your facility.")
            return
        
        # Calculate week and trimester
        today = date_type.today()
        days_since_lmp = (today - pregnancy.last_menstrual_period).days
        week_number = days_since_lmp // 7
        trimester = 1 if week_number <= 12 else (2 if week_number <= 27 else 3)
        days_to_due = (pregnancy.due_date - today).days
        
        # Get risk level
        risk_text = ""
        try:
            risk_score = await pregnancy_repository.get_latest_risk_score(db, pregnancy.id)
            if risk_score:
                risk_text = f"\nRisk Level: {risk_score.level.value}"
        except Exception:
            pass
        
        # Get assigned doctor
        doc_text = ""
        if profile and profile.personal_doctor_id:
            doc = await db.get(User, profile.personal_doctor_id)
            if doc:
                doc_text = f"\nDoctor: Dr. {doc.full_name}"
        
        msg = (
            f"BintiCare Status:\n"
            f"Week {week_number} - Trimester {trimester}\n"
            f"Due Date: {pregnancy.due_date.strftime('%d %b %Y')}\n"
            f"Days to go: {days_to_due}"
            f"{risk_text}"
            f"{doc_text}"
        )
        await send_sms(webhook.from_number, msg)
        return

    # 7. NEXT VISIT intent — upcoming ANC appointment
    if text_clean == "next visit":
        from app.utils.sms import send_sms
        from app.repositories import pregnancy_repository
        from app.models.pregnancy import VisitStatus
        from sqlalchemy import select
        from datetime import datetime as dt
        
        pregnancy = await pregnancy_repository.get_active_pregnancy(db, user.id)
        if not pregnancy:
            await send_sms(webhook.from_number, "BintiCare: No active pregnancy on record. Please register through the app first.")
            return
        
        # Find the next upcoming scheduled visit
        from app.models.pregnancy import ScheduledVisit
        stmt = (
            select(ScheduledVisit)
            .where(
                ScheduledVisit.pregnancy_id == pregnancy.id,
                ScheduledVisit.status == VisitStatus.SCHEDULED,
                ScheduledVisit.scheduled_at >= dt.now()
            )
            .order_by(ScheduledVisit.scheduled_at)
            .limit(1)
        )
        res = await db.execute(stmt)
        visit = res.scalar_one_or_none()
        
        if visit:
            visit_date = visit.scheduled_at.strftime("%A, %d %b %Y")
            purpose = visit.purpose or visit.label or "Routine check-up"
            
            # Try to get facility name
            fac_text = ""
            if visit.facility_id:
                from app.models.facility import Facility
                fac = await db.get(Facility, visit.facility_id)
                if fac:
                    fac_text = f"\nFacility: {fac.name}"
            
            msg = (
                f"BintiCare Next Visit:\n"
                f"Date: {visit_date}\n"
                f"Purpose: {purpose}"
                f"{fac_text}"
            )
        else:
            msg = "BintiCare: No upcoming visits scheduled. Contact your facility or doctor to schedule your next ANC visit."
        
        await send_sms(webhook.from_number, msg)
        return

    # 8. MY DOCTOR intent — assigned doctor info
    if text_clean == "my doctor":
        from app.utils.sms import send_sms
        
        profile = await profile_repository.get_by_user_id(db, user.id)
        
        if not profile or not profile.personal_doctor_id:
            await send_sms(webhook.from_number, "BintiCare: You don't have a doctor assigned yet. Reply REQUEST DOCTOR to get one assigned from your facility.")
            return
        
        doc = await db.get(User, profile.personal_doctor_id)
        if not doc:
            await send_sms(webhook.from_number, "BintiCare: Your assigned doctor record could not be found. Please contact your facility.")
            return
        
        # Get facility name
        fac_text = ""
        if profile.preferred_facility_id:
            from app.models.facility import Facility
            fac = await db.get(Facility, profile.preferred_facility_id)
            if fac:
                fac_text = f"\nFacility: {fac.name}"
        
        phone_text = f"\nPhone: {doc.phone_number}" if doc.phone_number else ""
        
        msg = (
            f"BintiCare Your Doctor:\n"
            f"Dr. {doc.full_name}"
            f"{phone_text}"
            f"{fac_text}\n"
            f"For emergencies, reply HELP."
        )
        await send_sms(webhook.from_number, msg)
        return

    # 9. EVENTS intent — upcoming facility events
    if text_clean == "events":
        from app.utils.sms import send_sms
        from app.models.education import EducationEvent
        from sqlalchemy import select
        from datetime import datetime as dt
        
        profile = await profile_repository.get_by_user_id(db, user.id)
        
        if not profile or not profile.preferred_facility_id:
            await send_sms(webhook.from_number, "BintiCare: Please register with a facility first. Reply GET FACILITIES to search.")
            return
        
        # Fetch upcoming events at the user's facility
        stmt = (
            select(EducationEvent)
            .where(
                EducationEvent.facility_id == profile.preferred_facility_id,
                EducationEvent.event_date >= dt.now()
            )
            .order_by(EducationEvent.event_date)
            .limit(3)
        )
        res = await db.execute(stmt)
        events = res.scalars().all()
        
        if not events:
            await send_sms(webhook.from_number, "BintiCare: No upcoming events at your facility right now. Check back later or reply TIPS for health advice.")
            return
        
        event_lines = []
        for e in events:
            event_date = e.event_date.strftime("%d %b, %I:%M %p")
            event_lines.append(f"- {e.title} ({event_date})")
        
        msg = "BintiCare Upcoming Events:\n" + "\n".join(event_lines)
        await send_sms(webhook.from_number, msg)
        return

    # 10. Unrecognized intent — notify user (unless it's a reminder-linked reply)
    if not webhook.linked_reminder_id:
        from app.utils.sms import send_sms
        
        logger.info(f"Unrecognized SMS intent from {webhook.from_number}: '{webhook.text}'")
        
        msg = (
            "BintiCare: Sorry, we didn't recognise that command.\n"
            "Reply MENU to see available options, or try:\n"
            "- VITALS <bp> <weight>\n"
            "- STATUS\n"
            "- NEXT VISIT\n"
            "- MY DOCTOR\n"
            "- HELP (for emergencies)"
        )
        await send_sms(webhook.from_number, msg)
        return

    # 6. Determine context & linked reminder
    context = FormContext.MATERNAL_CHECKIN
    reminder_id = None
    if webhook.linked_reminder_id:
        try:
            reminder_uuid = uuid.UUID(webhook.linked_reminder_id)
            from app.repositories import reminder_repository
            reminder = await reminder_repository.get_by_id(db, reminder_uuid)
            if reminder and reminder.user_id == user.id:
                reminder_id = reminder.id
                if reminder.type == "CYCLE":
                    context = FormContext.CYCLE_ENTRY
                # Mark as done
                await reminder_repository.update(db, reminder, {"is_done": True})
        except Exception as e:
            logger.error(f"Error checking linked reminder: {e}")
            
    # 3. Find active FormTemplate
    template = await cycle_repository.get_active_form_template(db, context)
    if not template:
        # Create a default template if none exists to avoid blocking
        template_data = {
            "slug": f"{context.lower().replace('_', '-')}-sms-default",
            "context": context,
            "fields": {"response": {"type": "string"}},
            "is_active": True
        }
        template = await cycle_repository.create_form_template(db, template_data)
        
    # 4. Create FormSubmission
    submission_data = {
        "template_id": template.id,
        "user_id": user.id,
        "context": context,
        "answers": {
            "response": webhook.text,
            "enteredBy": "PATIENT",
            "linkedReminderId": str(reminder_id) if reminder_id else None
        }
    }
    await cycle_repository.create_submission(db, submission_data)

async def get_sms_preference(db: AsyncSession, user_id: uuid.UUID) -> str:
    profile = await profile_repository.get_by_user_id(db, user_id)
    if not profile:
        profile = await profile_repository.create(db, user_id)
        
    pref = profile.notification_preference
    if pref == NotificationPreference.NOTIFICATION:
        return "APP_NOTIFICATIONS"
    elif pref == NotificationPreference.SMS:
        return "SMS"
    elif pref == NotificationPreference.BOTH:
        return "BOTH"
    return "BOTH" # default

async def update_sms_preference(db: AsyncSession, user_id: uuid.UUID, contact_preference: str) -> str:
    profile = await profile_repository.get_by_user_id(db, user_id)
    if not profile:
        profile = await profile_repository.create(db, user_id)
        
    if contact_preference == "APP_NOTIFICATIONS":
        pref = NotificationPreference.NOTIFICATION
    elif contact_preference == "SMS":
        pref = NotificationPreference.SMS
    elif contact_preference == "BOTH":
        pref = NotificationPreference.BOTH
    else:
        raise ValidationError(message="Invalid contactPreference value")
        
    await profile_repository.update(db, profile, {"notification_preference": pref})
    return contact_preference

async def send_clinician_assigned_notification(db: AsyncSession, patient_id: uuid.UUID, clinician_id: uuid.UUID, facility_id: uuid.UUID) -> None:
    try:
        from app.models.user import User
        from app.models.facility import Facility
        from app.models.profile import Profile, NotificationPreference
        from app.repositories import notification_repository, device_token_repository
        from app.utils.firebase import send_push_notification
        from app.utils.sms import send_sms
        from sqlalchemy import select

        patient = await db.get(User, patient_id)
        clinician = await db.get(User, clinician_id)
        facility = await db.get(Facility, facility_id)
        
        if not patient or not clinician:
            return
            
        fac_name = facility.name if facility else "your registered facility"
        msg = f"BintiCare: Dr. {clinician.full_name} has been assigned as your personal doctor from {fac_name}."
        
        profile = await db.scalar(select(Profile).where(Profile.user_id == patient_id))
        pref = NotificationPreference.BOTH
        if profile and profile.notification_preference:
            pref = profile.notification_preference
            
        # 1. SMS
        if pref in (NotificationPreference.SMS, NotificationPreference.BOTH):
            await send_sms(patient.phone_number, msg)
            
        # 2. Push/In-App
        if pref in (NotificationPreference.NOTIFICATION, NotificationPreference.BOTH):
            await notification_repository.create(db, {
                "user_id": patient_id,
                "category": "DOCTOR_ASSIGNED",
                "title": "Doctor Assigned",
                "body": msg,
                "is_read": False,
                "related_entity_type": "USER",
                "related_entity_id": str(clinician_id)
            })
            tokens = await device_token_repository.get_by_user_id(db, patient_id)
            if tokens:
                for t in tokens:
                    await send_push_notification(t.device_token, "Doctor Assigned", msg, {"clinicianId": str(clinician_id)})

        # 3. Notify Clinician via SMS and Web Inbox
        doc_msg = f"BintiCare Clinician Alert: Patient {patient.full_name} has been assigned to you."
        await notification_repository.create(db, {
            "user_id": clinician_id,
            "category": "PATIENT_ASSIGNED",
            "title": "New Patient Assigned",
            "body": doc_msg,
            "is_read": False,
            "related_entity_type": "USER",
            "related_entity_id": str(patient_id)
        })
        await send_sms(clinician.phone_number, doc_msg)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to send clinician assignment alert: {e}")

