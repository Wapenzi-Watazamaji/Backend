from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserLogin, Token, UserCreateSmsOnly
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.utils.exceptions import PhoneAlreadyRegisteredError, InvalidCredentialsError
from app.models.user import UserRole
import jwt
from app.core.config import settings
from app.core.security import ALGORITHM

async def register_user(db: AsyncSession, user_in: UserCreate):
    existing_user = await user_repository.get_by_phone_number(db, user_in.phone_number)
    if existing_user:
        raise PhoneAlreadyRegisteredError(
            message="Phone number is already registered",
            fields={"phoneNumber": "Already in use"}
        )
    
    user_data = user_in.model_dump(exclude={"password"})
    hashed_password = get_password_hash(user_in.password)
    user_data["password_hash"] = hashed_password
    user_data["account_type"] = "FULL"
    
    user = await user_repository.create(db, user_data)
    
    try:
        from app.utils.sms import send_sms
        welcome_msg = (
            f"Welcome to BintiCare, {user.full_name}! To register with a facility "
            "and get a clinician assigned to you, you can do so through the app, "
            "or reply to this SMS with your facility name."
        )
        await send_sms(user.phone_number, welcome_msg)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to send welcome SMS: {e}")
        
    return user

async def register_sms_only(db: AsyncSession, user_in: UserCreateSmsOnly):
    existing_user = await user_repository.get_by_phone_number(db, user_in.phone_number)
    if existing_user:
        raise PhoneAlreadyRegisteredError(
            message="Phone number is already registered",
            fields={"phoneNumber": "Already in use"}
        )
    
    user_data = user_in.model_dump()
    user_data["account_type"] = "SMS_ONLY"
    user_data["password_hash"] = None
    
    user = await user_repository.create(db, user_data)
    
    try:
        from app.utils.sms import send_sms
        welcome_msg = (
            f"Welcome to BintiCare, {user.full_name}! To register with a facility "
            "and get a clinician assigned to you, please reply to this SMS with your facility name."
        )
        await send_sms(user.phone_number, welcome_msg)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to send welcome SMS: {e}")
        
    return user

async def login_user(db: AsyncSession, login_in: UserLogin) -> Token:
    user = await user_repository.get_by_phone_number(db, login_in.phone_number)
    if not user or not verify_password(login_in.password, user.password_hash):
        raise InvalidCredentialsError(
            message="Incorrect phone number or password"
        )

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    staff_memberships = None
    if user.role in (UserRole.CLINICIAN, UserRole.FACILITY_ADMIN):
        from app.services.facility_service import get_staff_memberships
        from app.models.staff import StaffMember as StaffMemberModel, StaffStatus
        from sqlalchemy import select
        
        # Check if they have a pending invite and flip to ACTIVE on first login
        stmt = select(StaffMemberModel).where(
            StaffMemberModel.user_id == user.id,
            StaffMemberModel.status == StaffStatus.INVITE_PENDING
        )
        res = await db.execute(stmt)
        pending_staff = res.scalars().all()
        for staff_row in pending_staff:
            staff_row.status = StaffStatus.ACTIVE
            from datetime import datetime, timezone
            staff_row.joined_at = datetime.now(timezone.utc)
        if pending_staff:
            await db.commit()

        memberships = await get_staff_memberships(db, user.id)
        staff_memberships = [m.model_dump() for m in memberships]

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        staff_memberships=staff_memberships,
    )


async def refresh_user_token(db: AsyncSession, refresh_token: str) -> Token:
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise InvalidCredentialsError(message="Invalid token type")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidCredentialsError(message="Invalid token payload")
    except jwt.PyJWTError:
        raise InvalidCredentialsError(message="Could not validate credentials")
        
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise InvalidCredentialsError(message="User not found")
        
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))
    return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer", user_id=user.id)

async def logout_user(db: AsyncSession) -> dict:
    # For now, we will just return a success response Since we are using stateless JWTs, and the client will discard the tokens. 
    return {"message": "Successfully logged out"}

