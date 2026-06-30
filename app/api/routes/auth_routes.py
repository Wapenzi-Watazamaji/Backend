from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.user import UserCreate, UserRead, UserLogin, Token, RefreshTokenRequest
from app.utils.exceptions import create_success_response, APIResponse
from app.services import user_service

router = APIRouter()

@router.post("/register", response_model=APIResponse[UserRead], status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(deps.get_db)):
    db_user = await user_service.register_user(db, user_in)
    return create_success_response(message="User registered successfully", data=db_user)

@router.post("/login", response_model=APIResponse[Token])
async def login(login_in: UserLogin, db: AsyncSession = Depends(deps.get_db)):
    token_data = await user_service.login_user(db, login_in)
    return create_success_response(message="User logged in successfully", data=token_data)


@router.post("/refresh", response_model=APIResponse[Token])
async def refresh(refresh_in: RefreshTokenRequest, db: AsyncSession = Depends(deps.get_db)):
    token_data = await user_service.refresh_user_token(db, refresh_in.refresh_token)
    return create_success_response(message="Token refreshed successfully", data=token_data)

@router.post("/logout", response_model=APIResponse[dict])
async def logout(db: AsyncSession = Depends(deps.get_db)):
    # Note: We can inject Depends(deps.get_current_user) here once we build the auth middleware!
    logout_data = await user_service.logout_user(db)
    return create_success_response(data=logout_data)
