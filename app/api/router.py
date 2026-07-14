from fastapi import APIRouter
from app.api.routes import (
    auth_routes, profile_routes, facility_routes, cycle_routes, 
    referral_routes, emergency_routes, pregnancy_routes, postpartum_routes, 
    education_routes, labour_routes, clinician_dashboard_routes, report_routes, 
    facility_admin_routes, medical_history_routes, template_routes,
    reminder_routes, notification_routes, ai_routes, chat_routes
)


api_router = APIRouter()
api_router.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile_routes.router, prefix="/profile", tags=["Profile"])
api_router.include_router(medical_history_routes.router, prefix="/medical-history", tags=["Medical History"])
api_router.include_router(facility_routes.router, prefix="/facilities", tags=["Facilities"])
api_router.include_router(cycle_routes.router, prefix="/cycles", tags=["Cycle Tracker"])
api_router.include_router(pregnancy_routes.router, prefix="/pregnancy", tags=["Pregnancy"])
api_router.include_router(postpartum_routes.router, prefix="/postpartum", tags=["Postpartum"])
api_router.include_router(labour_routes.router, prefix="/labour", tags=["Labour & Birth Monitor"])
api_router.include_router(referral_routes.router, prefix="/referrals", tags=["Referrals"])
api_router.include_router(emergency_routes.router, tags=["Emergencies"])
api_router.include_router(education_routes.router)
api_router.include_router(reminder_routes.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(notification_routes.router)
api_router.include_router(ai_routes.router, prefix="/ai", tags=["AI Assistant"])
api_router.include_router(chat_routes.router, prefix="/chat", tags=["AI Chat"])

api_router.include_router(clinician_dashboard_routes.router, prefix="/dashboard", tags=["Web Dashboard"])
api_router.include_router(report_routes.router, prefix="/reports", tags=["Reports"])
api_router.include_router(facility_admin_routes.router, prefix="/facility-admin", tags=["Facility Admin"])
api_router.include_router(template_routes.router, prefix="/templates", tags=["System Templates"])
