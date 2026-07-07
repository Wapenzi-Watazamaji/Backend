import uuid
from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.models.postpartum import MilestoneCategory
from app.schemas.postpartum import (
    BabyProfileCreate, BabyProfileUpdate, BabyProfileRead,
    BabyMilestoneCreate, BabyMilestoneRead,
    VaccinationRecordCreate, VaccinationRecordRead, VaccinationScheduleItem, MarkGivenRequest,
    EpdsSubmitRequest, EpdsScreeningRead, EpdsHistoryItem, EpdsFlagStatus,
    MaternalCheckinCreate, MaternalCheckinRead,
    BabyVitalsCreate, BabyAlertRead, PostnatalVisitRead,
    FormTemplateRead,
)
from app.schemas.pregnancy import VisitRead
from app.services import postpartum_service, consent_service
from app.utils.exceptions import create_success_response, APIResponse, ForbiddenError

router = APIRouter()

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    404: {"model": APIResponse[None], "description": "Not Found"},
    422: {"model": APIResponse[None], "description": "Validation Error"},
}


# ================================================================== #
# Maternal Check-ins                                                  #
# ================================================================== #

@router.get(
    "/maternal-checkins/form-template",
    response_model=APIResponse[FormTemplateRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get maternal check-in form template",
)
async def get_maternal_checkin_template(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    template = await postpartum_service.get_maternal_checkin_template(db)
    return create_success_response(data=template)


@router.post(
    "/maternal-checkins",
    response_model=APIResponse[MaternalCheckinRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Submit a maternal check-in",
)
async def create_maternal_checkin(
    data: MaternalCheckinCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    submission = await postpartum_service.create_maternal_checkin(db, current_user.id, data)
    return create_success_response(data=submission)


@router.get(
    "/maternal-checkins",
    response_model=APIResponse[list[MaternalCheckinRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List maternal check-ins",
)
async def list_maternal_checkins(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    checkins = await postpartum_service.list_maternal_checkins(db, current_user.id)
    return create_success_response(data=checkins)


@router.get(
    "/maternal-checkins/{checkin_id}",
    response_model=APIResponse[MaternalCheckinRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get a single maternal check-in",
)
async def get_maternal_checkin(
    checkin_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    checkin = await postpartum_service.get_maternal_checkin(db, checkin_id, current_user.id)
    return create_success_response(data=checkin)


# ================================================================== #
# EPDS Depression Screening                                           #
# ================================================================== #

@router.post(
    "/depression-screening",
    response_model=APIResponse[EpdsScreeningRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Submit an EPDS depression screening",
)
async def submit_epds(
    data: EpdsSubmitRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    result = await postpartum_service.submit_epds(db, current_user.id, data)
    return create_success_response(data=result)


@router.get(
    "/depression-screening/history",
    response_model=APIResponse[list[EpdsHistoryItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get EPDS screening history",
)
async def get_epds_history(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    history = await postpartum_service.list_epds_history(db, current_user.id)
    return create_success_response(data=history)


@router.get(
    "/depression-screening/flag",
    response_model=APIResponse[EpdsFlagStatus],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Check if an active self-harm flag exists",
)
async def get_epds_flag(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    flag = await postpartum_service.get_epds_flag(db, current_user.id)
    return create_success_response(data=flag)


# ================================================================== #
# Baby Profile                                                        #
# ================================================================== #

@router.post(
    "/baby/profile",
    response_model=APIResponse[BabyProfileRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Create baby profile (auto-generates vaccination schedule)",
)
async def create_baby_profile(
    data: BabyProfileCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    profile = await postpartum_service.create_baby_profile(db, current_user.id, data)
    return create_success_response(data=profile)


@router.get(
    "/baby/profiles",
    response_model=APIResponse[list[BabyProfileRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List all baby profiles for the current user",
)
async def list_baby_profiles(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    profiles = await postpartum_service.list_baby_profiles(db, current_user.id)
    return create_success_response(data=profiles)


@router.get(
    "/baby/profiles/{baby_id}",
    response_model=APIResponse[BabyProfileRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get a specific baby profile",
)
async def get_baby_profile(
    baby_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    profile = await postpartum_service.get_baby_profile(db, baby_id, current_user.id)
    return create_success_response(data=profile)


@router.put(
    "/baby/profiles/{baby_id}",
    response_model=APIResponse[BabyProfileRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Update a specific baby profile",
)
async def update_baby_profile(
    baby_id: uuid.UUID,
    data: BabyProfileUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    profile = await postpartum_service.update_baby_profile(db, baby_id, current_user.id, data)
    return create_success_response(data=profile)


# ================================================================== #
# Baby Vitals                                                         #
# ================================================================== #

@router.get(
    "/baby/vitals/form-template",
    response_model=APIResponse[FormTemplateRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get baby vitals form template",
)
async def get_baby_vitals_template(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    template = await postpartum_service.get_baby_vitals_template(db)
    return create_success_response(data=template)


@router.post(
    "/baby/{baby_id}/vitals",
    response_model=APIResponse[MaternalCheckinRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Submit baby vitals",
)
async def create_baby_vitals(
    baby_id: uuid.UUID,
    data: BabyVitalsCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    submission = await postpartum_service.create_baby_vitals(db, baby_id, current_user.id, data)
    return create_success_response(data=submission)


@router.get(
    "/baby/{baby_id}/vitals",
    response_model=APIResponse[list[MaternalCheckinRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List baby vitals submissions",
)
async def list_baby_vitals(
    baby_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    submissions = await postpartum_service.list_baby_vitals(db, baby_id, current_user.id)
    return create_success_response(data=submissions)


@router.get(
    "/baby/{baby_id}/vitals/alerts",
    response_model=APIResponse[list[BabyAlertRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get flagged baby vitals alerts",
)
async def get_baby_vitals_alerts(
    baby_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    alerts = await postpartum_service.get_baby_vitals_alerts(db, baby_id, current_user.id)
    return create_success_response(data=alerts)


# ================================================================== #
# Baby Milestones                                                     #
# ================================================================== #

@router.post(
    "/baby/{baby_id}/milestones",
    response_model=APIResponse[BabyMilestoneRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Record a baby milestone",
)
async def create_milestone(
    baby_id: uuid.UUID,
    data: BabyMilestoneCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    milestone = await postpartum_service.create_milestone(db, baby_id, current_user.id, data)
    return create_success_response(data=milestone)


@router.get(
    "/baby/{baby_id}/milestones",
    response_model=APIResponse[list[BabyMilestoneRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List baby milestones",
)
async def list_milestones(
    baby_id: uuid.UUID,
    category: Optional[MilestoneCategory] = Query(None),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    milestones = await postpartum_service.list_milestones(db, baby_id, current_user.id, category)
    return create_success_response(data=milestones)


# ================================================================== #
# Baby Vaccinations                                                   #
# ================================================================== #

@router.post(
    "/baby/{baby_id}/vaccinations",
    response_model=APIResponse[VaccinationRecordRead],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Record a vaccination as given",
)
async def record_vaccination(
    baby_id: uuid.UUID,
    data: VaccinationRecordCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    record = await postpartum_service.record_vaccination(db, baby_id, current_user.id, data)
    return create_success_response(data=record)


@router.get(
    "/baby/{baby_id}/vaccinations/schedule",
    response_model=APIResponse[list[VaccinationScheduleItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get baby vaccination schedule",
)
async def get_vaccination_schedule(
    baby_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    schedule = await postpartum_service.get_vaccination_schedule(db, baby_id, current_user.id)
    return create_success_response(data=schedule)


@router.put(
    "/baby/{baby_id}/vaccinations/{visit_id}/mark-given",
    response_model=APIResponse[VisitRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Mark a scheduled vaccination as given",
)
async def mark_vaccination_given(
    baby_id: uuid.UUID,
    visit_id: uuid.UUID,
    data: MarkGivenRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    visit = await postpartum_service.mark_vaccination_given(db, baby_id, current_user.id, visit_id, data)
    return create_success_response(data=visit)


# ================================================================== #
# Postnatal Clinic-Visit Schedule                                     #
# ================================================================== #

@router.get(
    "/clinic-visits/schedule",
    response_model=APIResponse[list[PostnatalVisitRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get combined mother+baby postnatal clinic-visit schedule",
)
async def get_postnatal_clinic_schedule(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    schedule = await postpartum_service.get_postnatal_clinic_schedule(db, current_user.id)
    return create_success_response(data=schedule)


# ================================================================== #
# Clinician Endpoints (Require Consent)                               #
# ================================================================== #

async def verify_consent(db: AsyncSession, patient_id: uuid.UUID, facility_id: uuid.UUID):
    has_consent = await consent_service.has_active_consent(db, patient_id, facility_id)
    if not has_consent:
        raise ForbiddenError(message="Patient has not consented to sharing data with this facility")


@router.get(
    "/patients/{patient_id}/babies",
    response_model=APIResponse[list[BabyProfileRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Clinician: Get a patient's baby profiles",
)
async def get_patient_babies(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    await verify_consent(db, patient_id, facility_id)
    # Using existing service method, but passing patient_id
    profiles = await postpartum_service.list_baby_profiles(db, patient_id)
    return create_success_response(data=profiles)


@router.get(
    "/patients/{patient_id}/epds",
    response_model=APIResponse[list[EpdsHistoryItem]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Clinician: Get a patient's EPDS history",
)
async def get_patient_epds(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    await verify_consent(db, patient_id, facility_id)
    history = await postpartum_service.list_epds_history(db, patient_id)
    return create_success_response(data=history)


@router.get(
    "/patients/{patient_id}/maternal-checkins",
    response_model=APIResponse[list[MaternalCheckinRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Clinician: Get a patient's maternal check-ins",
)
async def get_patient_maternal_checkins(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_clinician),
    facility_id: uuid.UUID = Depends(deps.get_facility_context),
):
    await verify_consent(db, patient_id, facility_id)
    checkins = await postpartum_service.list_maternal_checkins(db, patient_id)
    return create_success_response(data=checkins)
