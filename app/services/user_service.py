from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.utils.exceptions import PhoneAlreadyRegisteredError, InvalidCredentialsError
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
    
    return await user_repository.create(db, user_data)

async def login_user(db: AsyncSession, login_in: UserLogin) -> Token:
    user = await user_repository.get_by_phone_number(db, login_in.phone_number)
    if not user or not verify_password(login_in.password, user.password_hash):
        raise InvalidCredentialsError(
            message="Incorrect phone number or password"
        )
    
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


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
    return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")

async def logout_user(db: AsyncSession) -> dict:
    # For now, we will just return a success response Since we are using stateless JWTs, and the client will discard the tokens. 
    return {"message": "Successfully logged out"}

