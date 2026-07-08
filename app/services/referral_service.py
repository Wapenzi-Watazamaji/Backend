import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.referral import Referral, ReferralStatus
from app.models.pregnancy import PregnancyRecord, PregnancyRiskScore
from app.models.user import User
from app.models.profile import Profile
from app.repositories import referral_repository
from app.utils.exceptions import NotFoundError, ValidationError


async def create_referral(
    db: AsyncSession, patient_id: uuid.UUID, data
) -> Referral:
    if data.offlineQueued and not data.clientCreatedAt:
        raise ValidationError(message="clientCreatedAt is required when offlineQueued is true")

    referral = await referral_repository.create_referral(db, {
        "patient_id": patient_id,
        "to_facility_id": data.toFacilityId,
        "from_facility_id": data.fromFacilityId,
        "reason": data.reason,
        "notes": data.notes,
        "is_emergency": data.isEmergency,
        "offline_queued": data.offlineQueued,
        "client_created_at": data.clientCreatedAt,
        "status": ReferralStatus.PENDING,
    })
    await db.commit()
    await db.refresh(referral)
    return referral


async def get_referral(db: AsyncSession, referral_id: uuid.UUID) -> Referral:
    referral = await referral_repository.get_referral_by_id(db, referral_id)
    if not referral:
        raise NotFoundError(message="Referral not found")
    return referral


async def list_referrals(
    db: AsyncSession,
    facility_id: Optional[uuid.UUID] = None,
    status: Optional[ReferralStatus] = None,
    direction: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> list[Referral]:
    return await referral_repository.list_referrals(
        db,
        facility_id=facility_id,
        status=status,
        direction=direction,
        page=page,
        page_size=page_size,
    )


async def accept_referral(db: AsyncSession, referral_id: uuid.UUID) -> Referral:
    referral = await get_referral(db, referral_id)
    if referral.status != ReferralStatus.PENDING:
        raise ValidationError(message="Only PENDING referrals can be accepted")

    updated = await referral_repository.update_referral(db, referral, {"status": ReferralStatus.ACCEPTED})
    await db.commit()
    await db.refresh(updated)
    return updated


async def reject_referral(db: AsyncSession, referral_id: uuid.UUID, data) -> Referral:
    referral = await get_referral(db, referral_id)
    if referral.status != ReferralStatus.PENDING:
        raise ValidationError(message="Only PENDING referrals can be rejected")

    updated = await referral_repository.update_referral(db, referral, {
        "status": ReferralStatus.REJECTED,
        "rejection_reason": data.reason,
    })
    await db.commit()
    await db.refresh(updated)
    return updated


async def complete_referral(db: AsyncSession, referral_id: uuid.UUID) -> Referral:
    referral = await get_referral(db, referral_id)
    if referral.status != ReferralStatus.ACCEPTED:
        raise ValidationError(message="Only ACCEPTED referrals can be completed")

    updated = await referral_repository.update_referral(db, referral, {
        "status": ReferralStatus.COMPLETED,
        "completed_at": datetime.now(timezone.utc),
    })
    await db.commit()
    await db.refresh(updated)
    return updated


async def get_patient_summary(db: AsyncSession, referral_id: uuid.UUID) -> dict:
    referral = await get_referral(db, referral_id)

    stmt = select(User).where(User.id == referral.patient_id)
    result = await db.execute(stmt)
    patient = result.scalars().first()
    if not patient:
        raise NotFoundError(message="Patient not found")

    stmt = select(Profile).where(Profile.user_id == patient.id)
    result = await db.execute(stmt)
    profile = result.scalars().first()

    stmt = (
        select(PregnancyRecord)
        .where(PregnancyRecord.user_id == patient.id)
        .order_by(PregnancyRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    pregnancy = result.scalars().first()

    gestational_weeks = None
    if pregnancy:
        from datetime import date
        today = date.today()
        gestational_weeks = (today - pregnancy.last_menstrual_period).days // 7

    stmt = (
        select(PregnancyRiskScore)
        .where(PregnancyRiskScore.user_id == patient.id)
        .order_by(PregnancyRiskScore.calculated_at.desc())
    )
    result = await db.execute(stmt)
    risk_score = result.scalars().first()
    active_flags = [f["label"] for f in risk_score.factors] if risk_score and risk_score.factors else []

    from datetime import date
    dob = patient.date_of_birth
    age = None
    if dob:
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    emergency_contact = None
    if profile and hasattr(profile, "emergency_contact_name") and profile.emergency_contact_name:
        emergency_contact = {
            "name": profile.emergency_contact_name,
            "phoneNumber": getattr(profile, "emergency_contact_phone", None),
        }

    return {
        "patient": {
            "fullName": patient.full_name,
            "age": age,
            "bloodType": None,
        },
        "gestationalAgeWeeks": gestational_weeks,
        "activeRiskFlags": active_flags,
        "reasonForVisit": referral.reason.value,
        "recentVitals": None,
        "allergies": [],
        "emergencyContact": emergency_contact,
    }

from app.schemas.referral import ReferralInboxItem
from app.models.facility import Facility
from sqlalchemy import desc

async def get_incoming_referrals_inbox(db: AsyncSession, facility_id: uuid.UUID) -> list[ReferralInboxItem]:
    stmt = (
        select(Referral, User, Profile, Facility)
        .join(User, User.id == Referral.patient_id)
        .outerjoin(Profile, Profile.user_id == User.id)
        .join(Facility, Facility.id == Referral.from_facility_id)
        .where(
            Referral.to_facility_id == facility_id,
            Referral.status == ReferralStatus.PENDING
        )
        .order_by(desc(Referral.created_at))
    )
    res = await db.execute(stmt)
    rows = res.all()
    results = []
    for ref, user, profile, from_fac in rows:
        results.append(ReferralInboxItem(
            id=ref.id,
            fromFacilityName=from_fac.name,
            toFacilityName="Current Facility",
            patientName=getattr(profile, 'full_name', getattr(user, 'phone_number', 'Unknown')),
            patientAge=32, # Mock
            pregnancyWeek=38, # Mock
            reason=ref.notes or ref.reason.value,
            requestedAt=ref.created_at,
            isEmergency=ref.is_emergency,
            status=ref.status.value,
            estimatedArrivalMinutes=25 if ref.is_emergency else None
        ))
    return results

async def get_outgoing_referrals_inbox(db: AsyncSession, facility_id: uuid.UUID) -> list[ReferralInboxItem]:
    stmt = (
        select(Referral, User, Profile, Facility)
        .join(User, User.id == Referral.patient_id)
        .outerjoin(Profile, Profile.user_id == User.id)
        .join(Facility, Facility.id == Referral.to_facility_id)
        .where(
            Referral.from_facility_id == facility_id
        )
        .order_by(desc(Referral.created_at))
    )
    res = await db.execute(stmt)
    rows = res.all()
    results = []
    for ref, user, profile, to_fac in rows:
        results.append(ReferralInboxItem(
            id=ref.id,
            fromFacilityName="Current Facility",
            toFacilityName=to_fac.name,
            patientName=getattr(profile, 'full_name', getattr(user, 'phone_number', 'Unknown')),
            patientAge=26, # Mock
            pregnancyWeek=12, # Mock
            reason=ref.notes or ref.reason.value,
            requestedAt=ref.created_at,
            isEmergency=ref.is_emergency,
            status=ref.status.value,
            estimatedArrivalMinutes=None
        ))
    return results
