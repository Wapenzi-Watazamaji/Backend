import uuid
from app.utils.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.consent import Consent
from app.schemas.consent import ConsentRead

async def revoke_consent(db: AsyncSession, user_id: uuid.UUID, grantee_id: str) -> Consent:
    # Find active consent for this user and grantee
    result = await db.execute(
        select(Consent).where(
            Consent.user_id == user_id,
            Consent.grantee_id == grantee_id,
            Consent.active == True
        )
    )
    consent = result.scalar_one_or_none()
    
    if not consent:
        raise NotFoundError(message="Active consent not found for this facility")
        
    consent.active = False
    consent.revoked_at = func.now()
    
    await db.commit()
    await db.refresh(consent)
    return consent

async def get_my_consents(db: AsyncSession, user_id: uuid.UUID) -> list[Consent]:
    result = await db.execute(
        select(Consent)
        .where(Consent.user_id == user_id)
        .order_by(Consent.granted_at.desc())
    )
    return result.scalars().all()


async def has_active_consent(db: AsyncSession, user_id: uuid.UUID, facility_id: uuid.UUID) -> bool:
    """Check if the user has active consent for the given facility."""
    stmt = select(Consent).where(
        Consent.user_id == user_id,
        Consent.grantee_id == str(facility_id),
        Consent.active == True
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
