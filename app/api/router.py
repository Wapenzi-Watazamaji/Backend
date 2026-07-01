from fastapi import APIRouter
from app.api.routes import auth_routes, profile_routes, facility_routes

api_router = APIRouter()
api_router.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile_routes.router, prefix="/profile", tags=["Profile"])
api_router.include_router(facility_routes.router, prefix="/facilities", tags=["Facilities"])
