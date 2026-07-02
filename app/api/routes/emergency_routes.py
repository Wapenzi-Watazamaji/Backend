import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_current_user, require_roles, get_facility_context
from app.models.user import User, UserRole
from app.schemas.emergency import EmergencyRequestCreate, EmergencyRequestUpdate, EmergencyRequestRead
from app.services import emergency_service
from app.utils.exceptions import APIResponse, create_success_response

router = APIRouter(prefix="/emergencies", tags=["Emergencies"])

@router.post("", response_model=APIResponse[EmergencyRequestRead])
async def create_emergency(
    req: EmergencyRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    emergency = await emergency_service.create_emergency_request(db, current_user.id, req)
    return create_success_response(message="Emergency request created successfully", data=emergency)

@router.get("/my-requests", response_model=APIResponse[list[EmergencyRequestRead]])
async def get_patient_emergencies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    emergencies = await emergency_service.get_patient_emergencies(db, current_user.id)
    return create_success_response(message="Emergency requests fetched successfully", data=emergencies)

@router.get("/inbox", response_model=APIResponse[list[EmergencyRequestRead]])
async def get_facility_emergencies(
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_roles(UserRole.CLINICIAN, UserRole.FACILITY_ADMIN)),
    db: AsyncSession = Depends(get_session)
):
    emergencies = await emergency_service.get_facility_emergencies(db, requester_facility_id)
    return create_success_response(message="Facility emergencies fetched successfully", data=emergencies)

@router.put("/{emergency_id}", response_model=APIResponse[EmergencyRequestRead])
async def update_emergency_status(
    emergency_id: uuid.UUID,
    req: EmergencyRequestUpdate,
    requester_facility_id: uuid.UUID = Depends(get_facility_context),
    current_user: User = Depends(require_roles(UserRole.CLINICIAN, UserRole.FACILITY_ADMIN)),
    db: AsyncSession = Depends(get_session)
):
    emergency = await emergency_service.update_emergency_status(db, emergency_id, requester_facility_id, req)
    return create_success_response(message="Emergency status updated successfully", data=emergency)
