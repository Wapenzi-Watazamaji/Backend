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
        
    emergency.status = req.status
        
    await db.commit()
    await db.refresh(emergency)
    return emergency
