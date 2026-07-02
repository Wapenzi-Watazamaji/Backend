from fastapi import APIRouter
from app.api.routes import auth_routes, profile_routes, facility_routes, cycle_routes, referral_routes, emergency_routes, education_routes

api_router = APIRouter()
api_router.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile_routes.router, prefix="/profile", tags=["Profile"])
api_router.include_router(facility_routes.router, prefix="/facilities", tags=["Facilities"])
api_router.include_router(cycle_routes.router, prefix="/cycles", tags=["Cycle Tracker"])
api_router.include_router(referral_routes.router, tags=["Referrals"])
api_router.include_router(emergency_routes.router, tags=["Emergencies"])
api_router.include_router(education_routes.router)
