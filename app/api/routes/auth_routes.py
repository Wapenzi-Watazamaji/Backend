from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_dep as get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserLogin, Token, RefreshTokenRequest, UserCreateSmsOnly
from app.utils.exceptions import create_success_response, APIResponse
from app.services import user_service

router = APIRouter()


@router.post("/register", response_model=APIResponse[UserRead], status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await user_service.register_user(db, user_in)
    return create_success_response(message="User registered successfully", data=db_user)


@router.post("/register-sms-only", response_model=APIResponse[UserRead], status_code=status.HTTP_201_CREATED)
async def register_sms_only(user_in: UserCreateSmsOnly, db: AsyncSession = Depends(get_db)):
    db_user = await user_service.register_sms_only(db, user_in)
    return create_success_response(message="SMS-only user registered successfully", data=db_user)


@router.post("/login", response_model=APIResponse[Token])
async def login(login_in: UserLogin, db: AsyncSession = Depends(get_db)):
    token_data = await user_service.login_user(db, login_in)
    return create_success_response(message="User logged in successfully", data=token_data)


@router.post("/refresh", response_model=APIResponse[Token])
async def refresh(refresh_in: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    token_data = await user_service.refresh_user_token(db, refresh_in.refresh_token)
    return create_success_response(message="Token refreshed successfully", data=token_data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_in: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
):
    return None


@router.get("/me", response_model=APIResponse[UserRead])
async def get_me(current_user: User = Depends(get_current_user)):
    return create_success_response(data=current_user)
