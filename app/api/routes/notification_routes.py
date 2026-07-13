import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.notification import (
    NotificationRead, DeviceRegisterRequest, DeviceRegisterResponse,
    SmsSendRequest, SmsSendResponse, SmsInboundWebhook,
    SmsPreferenceResponse, SmsPreferenceUpdate
)
from app.services import notification_service
from app.utils.exceptions import create_success_response, APIResponse

router = APIRouter(tags=["Notifications & SMS"])

STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    404: {"model": APIResponse[None], "description": "Not Found"},
}

@router.get(
    "/notifications",
    response_model=APIResponse[List[NotificationRead]],
    responses=STANDARD_ERROR_RESPONSES,
    summary="List notifications for current user"
)
async def list_notifications(
    unread_only: Optional[bool] = Query(False, alias="unreadOnly"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    notifications, total = await notification_service.list_notifications(
        db, current_user.id, unread_only=unread_only, page=page, page_size=page_size
    )
    meta = {
        "page": page,
        "pageSize": page_size,
        "totalItems": total,
        "totalPages": -(-total // page_size)
    }
    return create_success_response(data=notifications, meta=meta)

@router.put(
    "/notifications/{id}/read",
    response_model=APIResponse[NotificationRead],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Mark notification as read"
)
async def mark_notification_read(
    id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    notification = await notification_service.mark_notification_read(db, id, current_user.id)
    return create_success_response(data=notification)

@router.post(
    "/devices/register",
    response_model=APIResponse[DeviceRegisterResponse],
    status_code=status.HTTP_201_CREATED,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Register a push notification device token"
)
async def register_device(
    device_in: DeviceRegisterRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    token = await notification_service.register_device_token(db, current_user.id, device_in)
    return create_success_response(data=DeviceRegisterResponse(tokenId=token.id))

@router.delete(
    "/devices/{tokenId}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=STANDARD_ERROR_RESPONSES,
    summary="Unregister a push notification device token"
)
async def unregister_device(
    tokenId: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    await notification_service.unregister_device_token(db, tokenId, current_user.id)
    return None

@router.post(
    "/notifications/sms/send",
    response_model=APIResponse[SmsSendResponse],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Send a template-based SMS (internal)"
)
async def send_templated_sms(
    req: SmsSendRequest,
    db: AsyncSession = Depends(deps.get_db),
):
    res = await notification_service.send_templated_sms(db, req)
    return create_success_response(data=SmsSendResponse(smsId=res["sms_id"], status=res["status"]))

@router.post(
    "/notifications/sms/inbound-webhook",
    response_model=APIResponse[dict],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Receive inbound SMS check-ins (webhook)"
)
async def inbound_sms_webhook(
    webhook: SmsInboundWebhook,
    db: AsyncSession = Depends(deps.get_db),
):
    await notification_service.inbound_sms_reply(db, webhook)
    return create_success_response(data=None)

@router.get(
    "/notifications/sms/preferences",
    response_model=APIResponse[SmsPreferenceResponse],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Get SMS preference for current user"
)
async def get_sms_preference(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    pref = await notification_service.get_sms_preference(db, current_user.id)
    return create_success_response(data=SmsPreferenceResponse(contactPreference=pref))

@router.put(
    "/notifications/sms/preferences",
    response_model=APIResponse[SmsPreferenceResponse],
    responses=STANDARD_ERROR_RESPONSES,
    summary="Update SMS preference for current user"
)
async def update_sms_preference(
    req: SmsPreferenceUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    pref = await notification_service.update_sms_preference(db, current_user.id, req.contact_preference)
    return create_success_response(data=SmsPreferenceResponse(contactPreference=pref))

from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/notifications/ws/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: uuid.UUID):
    from app.core.websocket import manager
    user_str = str(user_id)
    await manager.connect(user_str, websocket)
    try:
        while True:
            # Keep connection alive; discard incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_str, websocket)
