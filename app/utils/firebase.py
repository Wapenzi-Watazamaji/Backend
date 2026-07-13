import logging
import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_initialized = False

def init_firebase() -> bool:
    global _firebase_initialized
    if _firebase_initialized:
        return True
        
    path = settings.FIREBASE_CREDENTIALS_PATH
    if not path:
        logger.info("FIREBASE_CREDENTIALS_PATH not set. Firebase Admin SDK running in MOCK mode.")
        return False
        
    try:
        cred = credentials.Certificate(path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK successfully initialized.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}. Running in MOCK mode.")
        return False

async def send_push_notification(token: str, title: str, body: str, data: dict = None) -> bool:
    """
    Sends a push notification to a specific device token.
    Falls back to logging in mock mode if Firebase is not initialized or fails.
    """
    is_ready = init_firebase()
    
    if not is_ready:
        logger.info(f"[MOCK PUSH] Sent to token '{token}': Title='{title}', Body='{body}', Data={data}")
        return True
        
    try:
        # Construct message
        msg_data = {k: str(v) for k, v in (data or {}).items()}
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=msg_data,
            token=token,
        )
        
        import asyncio
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: messaging.send(message))
        logger.info(f"Firebase Push Notification sent successfully to token '{token}'")
        return True
    except Exception as e:
        logger.error(f"Firebase send failure: {e}. Falling back to MOCK mode log.")
        logger.info(f"[MOCK PUSH] Sent to token '{token}': Title='{title}', Body='{body}', Data={data}")
        return False
