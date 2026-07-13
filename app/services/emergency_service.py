import uuid
from app.utils.exceptions import NotFoundError, ForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.emergency import EmergencyRequest, EmergencyStatus
from app.schemas.emergency import EmergencyRequestCreate, EmergencyRequestUpdate
from app.models.facility import Facility

async def create_emergency_request(db: AsyncSession, patient_id: uuid.UUID, req: EmergencyRequestCreate) -> EmergencyRequest:
    # Ensure facility exists
    facility = await db.get(Facility, req.facility_id)
    if not facility:
        raise NotFoundError(message="Facility not found")
        
    emergency = EmergencyRequest(
        patient_id=patient_id,
        facility_id=req.facility_id,
        location_lat=req.location_lat,
        location_lng=req.location_lng,
        notes=req.notes,
        status=EmergencyStatus.PENDING
    )
    db.add(emergency)
    await db.commit()
    await db.refresh(emergency)
    
    # Send emergency SMS and web alerts to on-duty facility clinicians and admins
    try:
        from app.models.user import User, UserRole
        from app.models.staff import StaffMember, StaffStatus
        from app.utils.sms import send_sms
        from app.repositories import notification_repository
        
        patient = await db.get(User, patient_id)
        pat_name = patient.full_name if patient else "A BintiCare Patient"
        pat_phone = patient.phone_number if patient else "N/A"
        
        stmt = (
            select(User)
            .join(StaffMember, StaffMember.user_id == User.id)
            .where(
                StaffMember.facility_id == req.facility_id,
                User.role.in_((UserRole.CLINICIAN, UserRole.FACILITY_ADMIN))
            )
        )
        res = await db.execute(stmt)
        staff_members = res.scalars().all()
        
        alert_msg = f"CRITICAL EMERGENCY: Patient {pat_name} has requested emergency assistance at {facility.name}. Notes: {req.notes or 'None'}. Phone: {pat_phone}."
        
        for staff in staff_members:
            # 1. Log in web app dashboard inbox
            await notification_repository.create(db, {
                "user_id": staff.id,
                "category": "EMERGENCY_ALERT",
                "title": "Emergency Assistance Requested",
                "body": alert_msg,
                "is_read": False,
                "related_entity_type": "EMERGENCY_REQUEST",
                "related_entity_id": str(emergency.id)
            })
            # 2. Send SMS Alert
            await send_sms(staff.phone_number, alert_msg)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to alert clinicians/admins of emergency: {e}")
        
    return emergency

async def get_facility_emergencies(db: AsyncSession, facility_id: uuid.UUID) -> list[EmergencyRequest]:
    result = await db.execute(
        select(EmergencyRequest).where(EmergencyRequest.facility_id == facility_id).order_by(EmergencyRequest.created_at.desc())
    )
    return result.scalars().all()

async def get_patient_emergencies(db: AsyncSession, patient_id: uuid.UUID) -> list[EmergencyRequest]:
    result = await db.execute(
        select(EmergencyRequest).where(EmergencyRequest.patient_id == patient_id).order_by(EmergencyRequest.created_at.desc())
    )
    return result.scalars().all()

async def update_emergency_status(db: AsyncSession, emergency_id: uuid.UUID, facility_id: uuid.UUID, req: EmergencyRequestUpdate) -> EmergencyRequest:
    emergency = await db.get(EmergencyRequest, emergency_id)
    if not emergency:
        raise NotFoundError(message="Emergency request not found")
        
    # Security: only the receiving facility can update status
    if emergency.facility_id != facility_id:
        raise ForbiddenError(message="Only the destination facility can update this emergency")
        
    old_status = emergency.status
    new_status = req.status
    
    if old_status != new_status:
        emergency.status = new_status
        await db.commit()
        await db.refresh(emergency)
        
        # Resolve destination facility name
        facility = await db.get(Facility, emergency.facility_id)
        facility_name = facility.name if facility else "the destination facility"
        
        # Construct message content
        if new_status == EmergencyStatus.DISPATCHED:
            body = f"Your emergency request has been acknowledged by {facility_name}. Assistance is on the way."
        elif new_status == EmergencyStatus.RESOLVED:
            body = f"Your emergency request has been marked as resolved by {facility_name}."
        elif new_status == EmergencyStatus.FALSE_ALARM:
            body = f"Your emergency request was marked as a false alarm by {facility_name}."
        else:
            body = f"Your emergency request status has been updated to {new_status} by {facility_name}."
            
        # Create In-App Notification
        from app.repositories import notification_repository, device_token_repository
        from app.utils.firebase import send_push_notification
        from app.utils.sms import send_sms
        from app.models.profile import Profile, NotificationPreference
        from app.models.user import User
        
        # Load patient and their profile preferences
        patient = await db.get(User, emergency.patient_id)
        profile = await db.scalar(select(Profile).where(Profile.user_id == emergency.patient_id))
        
        pref = NotificationPreference.BOTH
        if profile and profile.notification_preference:
            pref = profile.notification_preference
            
        # 1. Process SMS (if preference is SMS or BOTH)
        if pref in (NotificationPreference.SMS, NotificationPreference.BOTH) and patient:
            print(f"Sending emergency update SMS to patient {patient.full_name} ({patient.phone_number})...")
            await send_sms(patient.phone_number, body)
            
        # 2. Process In-App & Push Notification (if preference is NOTIFICATION or BOTH)
        if pref in (NotificationPreference.NOTIFICATION, NotificationPreference.BOTH):
            notif_data = {
                "user_id": emergency.patient_id,
                "category": "EMERGENCY_UPDATE",
                "title": "Emergency Request Updated",
                "body": body,
                "is_read": False,
                "related_entity_type": "EMERGENCY_REQUEST",
                "related_entity_id": str(emergency.id)
            }
            await notification_repository.create(db, notif_data)
            
            # Trigger Firebase Push Notification
            tokens = await device_token_repository.get_by_user_id(db, emergency.patient_id)
            if tokens:
                for t in tokens:
                    await send_push_notification(
                        token=t.device_token,
                        title="Emergency Request Updated",
                        body=body,
                        data={"emergencyId": str(emergency.id), "status": new_status}
                    )
    else:
        await db.commit()
        await db.refresh(emergency)
        
    return emergency