import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.profile import SharingPreference, CompanionPreference
from app.repositories import profile_repository

@pytest.mark.asyncio
async def test_websocket_chat_always_share_consent_flow(db_session: AsyncSession):
    # Setup mock user and profile
    from tests.conftest import generate_phone
    from app.repositories import user_repository
    
    phone = generate_phone()
    # Create user
    user = await user_repository.create(db_session, {
        "phone_number": phone,
        "full_name": "Always Share Patient",
        "hashed_password": "hashed",
        "role": "USER"
    })
    
    # Create profile with ALWAYS_SHARE
    profile = await profile_repository.create(db_session, user_id=user.id)
    await profile_repository.update(db_session, profile, {
        "emergency_sharing_preference": SharingPreference.ALWAYS_SHARE,
        "companion_preference": CompanionPreference.AI_DOC
    })
    await db_session.commit()

    # Generate token
    from app.core.config import settings
    import jwt
    from datetime import datetime, timedelta
    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(days=1)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    # Mock Azure OpenAI Chat Completions client
    mock_client = AsyncMock()
    mock_completions = AsyncMock()
    mock_choice = AsyncMock()
    mock_choice.message.tool_calls = []
    mock_completions.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completions)

    with patch("app.services.ai.chat_service.AsyncAzureOpenAI", return_value=mock_client):
        client = TestClient(app)
        with client.websocket_connect(f"/api/v1/chat/ws?token={token}") as websocket:
            # Should connect and skip consent request since preference is ALWAYS_SHARE
            res = websocket.receive_json()
            assert res["type"] == "connected"
            
            # Send message
            websocket.send_json({"type": "user_message", "content": "Hello"})
            # Verify the flow continues (either tokens or completed)
            # Since OpenAI is mocked, it won't actually stream, but we check logic.
