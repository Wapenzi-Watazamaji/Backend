from fastapi import APIRouter
from app.api.routes import auth_routes

api_router = APIRouter()
api_router.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
