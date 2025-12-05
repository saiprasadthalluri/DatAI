"""Integration tests for chat endpoint."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_chat_send_message(client: AsyncClient):
    """Test sending a chat message."""
    # Mock Firebase auth
    with patch("app.api.v1.deps.verify_firebase_token") as mock_auth:
        mock_auth.return_value = {
            "uid": "test-user-123",
            "email": "test@example.com"
        }
        
        # Mock services
        with patch("app.services.safety.check") as mock_safety, \
             patch("app.services.router.decide") as mock_router, \
             patch("app.services.llm_client.get_llm_client") as mock_llm:
            
            mock_safety.return_value = {"allowed": True, "labels": {}, "reason": "", "reference_code": "SAFETY_OK"}
            mock_router.return_value = {
                "model": "theory-specialist",
                "confidence": 0.9,
                "reasons": {"model": "theory-specialist", "source": "auto_routing"}
            }
            
            # Mock LLM client
            mock_client = AsyncMock()
            mock_client.chat_completion.return_value = {"response": "This is a test response"}
            mock_llm.return_value = mock_client
            
            response = await client.post(
                "/api/v1/chat/send",
                json={
                    "message": "Hello",
                    "meta": {"mode": "chat", "temperature": 0.2}
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "assistant_message" in data
            assert "conversation_id" in data
            assert "message_id" in data


@pytest.mark.asyncio
async def test_chat_safety_block(client: AsyncClient):
    """Test chat endpoint blocks unsafe content."""
    with patch("app.api.v1.deps.verify_firebase_token") as mock_auth:
        mock_auth.return_value = {
            "uid": "test-user-123",
            "email": "test@example.com"
        }
        
        with patch("app.services.safety.check") as mock_safety:
            mock_safety.return_value = {
                "allowed": False,
                "labels": {"unsafe": True},
                "reason": "Unsafe content detected",
                "reference_code": "SAFETY_002"
            }
            
            response = await client.post(
                "/api/v1/chat/send",
                json={
                    "message": "Unsafe content",
                    "meta": {"mode": "chat"}
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "safety" in data


@pytest.mark.asyncio
async def test_chat_rate_limit(client: AsyncClient):
    """Test rate limiting on chat endpoint."""
    with patch("app.api.v1.deps.verify_firebase_token") as mock_auth:
        mock_auth.return_value = {
            "uid": "test-user-123",
            "email": "test@example.com"
        }
        
        # Mock rate limit to fail
        with patch("app.core.rate_limit.check_rate_limit") as mock_rate_limit:
            mock_rate_limit.return_value = False
            
            response = await client.post(
                "/api/v1/chat/send",
                json={
                    "message": "Hello",
                    "meta": {"mode": "chat"}
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 429



