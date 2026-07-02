import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.referral import Referral, ReferralStatus
from app.schemas.referral import ReferralCreate, ReferralUpdate
from app.models.user import User
from app.models.profile import Profile, SharingPreference
from app.models.consent import Consent, ConsentType
from app.models.facility import Facility

async def create_referral(db: AsyncSession, sending_facility_id: uuid.UUID, req: ReferralCreate) -> Referral:
    # Ensure patient exists
    patient = await db.get(User, req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    referral = Referral(
        patient_id=req.patient_id,
        sending_facility_id=sending_facility_id,
        receiving_facility_id=req.receiving_facility_id,
        reason=req.reason,
        priority=req.priority,
        clinical_notes=req.clinical_notes,
        status=ReferralStatus.PENDING
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return referral

async def get_facility_inbox(db: AsyncSession, facility_id: uuid.UUID) -> list[Referral]:
    result = await db.execute(
        select(Referral).where(Referral.receiving_facility_id == facility_id).order_by(Referral.created_at.desc())
    )
    return result.scalars().all()

async def get_facility_outbox(db: AsyncSession, facility_id: uuid.UUID) -> list[Referral]:
    result = await db.execute(
        select(Referral).where(Referral.sending_facility_id == facility_id).order_by(Referral.created_at.desc())
    )
    return result.scalars().all()

async def update_referral_status(db: AsyncSession, referral_id: uuid.UUID, facility_id: uuid.UUID, req: ReferralUpdate) -> Referral:
    referral = await db.get(Referral, referral_id)
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
        
    # Security: only the receiving facility can accept/reject/complete
    if referral.receiving_facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Only the receiving facility can update this referral")
        
    referral.status = req.status
    if req.rejection_reason:
        referral.rejection_reason = req.rejection_reason
        
    await db.commit()
    await db.refresh(referral)
    return referral

async def request_records_access(db: AsyncSession, referral_id: uuid.UUID, facility_id: uuid.UUID) -> dict:
    referral = await db.get(Referral, referral_id)
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
        
    if referral.receiving_facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Only the receiving facility can request access")
        
    if referral.status != ReferralStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Referral must be accepted before requesting records access")
        
    # Get Patient Profile
    result = await db.execute(select(Profile).where(Profile.user_id == referral.patient_id))
    profile = result.scalar_one_or_none()
    
    if not profile or not profile.emergency_sharing_preference:
        # Default to ASK_FIRST if not set
        pref = SharingPreference.ASK_FIRST
    else:
        pref = profile.emergency_sharing_preference
        
    if pref == SharingPreference.NEVER_SHARE:
        raise HTTPException(status_code=403, detail="Patient has locked their health records. Access denied.")
        
    if pref == SharingPreference.ALWAYS_SHARE:
        # Create Consent immediately
        facility = await db.get(Facility, facility_id)
        
        # Check if consent already exists
        existing_result = await db.execute(
            select(Consent).where(
                Consent.user_id == referral.patient_id,
                Consent.grantee_id == str(facility_id),
                Consent.active == True
            )
        )
        existing_consent = existing_result.scalar_one_or_none()
        
        if not existing_consent:
            consent = Consent(
                user_id=referral.patient_id,
                consent_type=ConsentType.FACILITY_AUTO_SHARE,
                grantee_id=str(facility_id),
                grantee_name=facility.name,
                active=True
            )
            db.add(consent)
            await db.commit()
            
        return {"status": "access_granted", "message": "Access granted via ALWAYS_SHARE preference"}
        
    # If ASK_FIRST, return pending status (mock sending push notification)
    return {"status": "pending_consent", "message": "Push notification sent to patient asking for consent"}
