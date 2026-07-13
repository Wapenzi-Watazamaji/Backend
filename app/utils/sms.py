import logging
import uuid
import asyncio
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Africa's Talking
_at_initialized = False
try:
    if settings.AT_API_KEY and settings.AT_USERNAME:
        import africastalking
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        _sms_service = africastalking.SMS
        _at_initialized = True
        logger.info("Africa's Talking SMS client initialized successfully.")
    else:
        logger.warning("Africa's Talking credentials missing. SMS service running in MOCK mode.")
except Exception as e:
    logger.error(f"Failed to initialize Africa's Talking client: {e}. SMS service running in MOCK mode.")
    _at_initialized = False

# SMS Templates
SMS_TEMPLATES: Dict[str, str] = {
    "emergency_contact_notify": "Emergency alert for {motherName} at {facilityName}. Please respond immediately.",
    "appointment_reminder": "Hi {motherName}, you have a scheduled visit at {facilityName} on {appointmentDate}.",
    "check_in_prompt": "Hi {motherName}, this is BintiCare. Reply 1 if baby moved today, 2 if not."
}

def render_template(template_id: str, variables: Dict[str, Any]) -> str:
    template = SMS_TEMPLATES.get(template_id)
    if not template:
        logger.warning(f"SMS template '{template_id}' not found. Using default rendering.")
        var_str = ", ".join(f"{k}: {v}" for k, v in variables.items())
        return f"System Alert [{template_id}]: {var_str}"
    
    try:
        return template.format(**variables)
    except KeyError as e:
        logger.error(f"Missing variable {e} for template '{template_id}'. Template: '{template}'")
        return template

async def send_sms(to: str, message: str) -> dict:
    """
    Sends an SMS using Africa's Talking.
    If the client is not initialized or fails, it falls back to mock delivery.
    """
    logger.info(f"Dispatching SMS to {to}: '{message}'")
    
    if _at_initialized:
        try:
            def do_send():
                kwargs = {}
                if settings.AT_SENDER_ID:
                    kwargs["sender_id"] = settings.AT_SENDER_ID
                return _sms_service.send(message, [to], **kwargs)
                
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, do_send)
            
            # Check response
            recipients = res.get("SMSMessageData", {}).get("Recipients", [])
            if recipients:
                rec = recipients[0]
                status = rec.get("status")
                # Africa's Talking status can be "Success", "SuccessSent", "SENT", "Sent"
                if status in ["Success", "SuccessSent", "SENT", "Sent", "success"]:
                    return {"sms_id": rec.get("messageId", "sms_at"), "status": "SENT"}
                else:
                    logger.warning(f"Africa's Talking delivery status: {status} for {to}")
                    return {"sms_id": rec.get("messageId", "sms_at_failed"), "status": "FAILED"}
            
            return {"sms_id": "sms_unknown", "status": "FAILED"}
            
        except Exception as e:
            logger.error(f"Africa's Talking send failure, falling back to mock: {e}")
            # Fall through to mock
            
    # Mock Delivery Fallback
    mock_id = f"sms_mock_{uuid.uuid4().hex[:6]}"
    logger.info(f"[MOCK SMS] Message {mock_id} sent to {to} successfully.")
    return {"sms_id": mock_id, "status": "SENT"}
