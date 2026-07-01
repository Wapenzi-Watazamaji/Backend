import uuid
from typing import AsyncGenerator

import jwt
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories import user_repository
from app.repositories import staff_repository
from app.utils.exceptions import UnauthorizedError, ForbiddenError

_bearer_scheme = HTTPBearer(auto_error=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session

get_db_dep = get_session


def _extract_user_id(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        raise UnauthorizedError(message="Not authenticated — missing Bearer token")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError(message="Access token has expired")
    except jwt.PyJWTError:
        raise UnauthorizedError(message="Could not validate credentials")

    if payload.get("type") == "refresh":
        raise UnauthorizedError(message="Cannot use a refresh token as an access token")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(message="Invalid token payload")

    return user_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = _extract_user_id(credentials)

    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise UnauthorizedError(message="User not found")
    if not user.is_active:
        raise UnauthorizedError(message="Account is disabled")

    return user


def require_roles(*roles: UserRole):
    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(
                message=f"Access denied — required role(s): {[r.value for r in roles]}"
            )
        return current_user
    return _check_role


require_clinician = require_roles(UserRole.CLINICIAN, UserRole.FACILITY_ADMIN)
require_facility_admin = require_roles(UserRole.FACILITY_ADMIN)


async def get_facility_context(
    x_facility_context: str | None = Header(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    if not x_facility_context:
        raise ForbiddenError(message="X-Facility-Context header is required for this endpoint")

    try:
        facility_id = uuid.UUID(x_facility_context)
    except ValueError:
        raise ForbiddenError(message=f"X-Facility-Context '{x_facility_context}' is not a valid UUID")

    is_member = await staff_repository.is_active_staff_at_facility(
        db, user_id=current_user.id, facility_id=facility_id
    )
    if not is_member:
        raise ForbiddenError(message="You are not an active staff member at the requested facility")

    return facility_id
