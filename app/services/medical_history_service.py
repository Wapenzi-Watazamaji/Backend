import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.medical_history import MedicalHistoryRecord, MedicalHistoryCustomField
from app.schemas.medical_history import (
    MedicalHistoryRecordCreate, MedicalHistoryRecordUpdate,
    MedicalHistoryCustomFieldCreate
)
from app.utils.exceptions import NotFoundError, DuplicateResourceError

async def get_medical_history(db: AsyncSession, patient_id: uuid.UUID) -> MedicalHistoryRecord | None:
    stmt = select(MedicalHistoryRecord).where(MedicalHistoryRecord.patient_user_id == patient_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def create_medical_history(
    db: AsyncSession, patient_id: uuid.UUID, clinician_id: uuid.UUID, data: MedicalHistoryRecordCreate
) -> MedicalHistoryRecord:
    existing = await get_medical_history(db, patient_id)
    if existing:
        raise DuplicateResourceError(message="Medical history record already exists for this patient")

    record = MedicalHistoryRecord(
        patient_user_id=patient_id,
        created_by=clinician_id,
        last_updated_by=clinician_id,
        **data.model_dump()
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record

async def update_medical_history(
    db: AsyncSession, patient_id: uuid.UUID, clinician_id: uuid.UUID, data: MedicalHistoryRecordUpdate
) -> MedicalHistoryRecord:
    record = await get_medical_history(db, patient_id)
    if not record:
        raise NotFoundError(message="Medical history record not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
    
    record.last_updated_by = clinician_id
    await db.commit()
    await db.refresh(record)
    return record

async def get_custom_fields(db: AsyncSession, facility_id: uuid.UUID) -> list[MedicalHistoryCustomField]:
    stmt = select(MedicalHistoryCustomField).where(MedicalHistoryCustomField.facility_id == facility_id)
    res = await db.execute(stmt)
    return res.scalars().all()

async def create_custom_field(
    db: AsyncSession, facility_id: uuid.UUID, clinician_id: uuid.UUID, data: MedicalHistoryCustomFieldCreate
) -> MedicalHistoryCustomField:
    field = MedicalHistoryCustomField(
        facility_id=facility_id,
        created_by=clinician_id,
        **data.model_dump()
    )
    db.add(field)
    await db.commit()
    await db.refresh(field)
    return field
