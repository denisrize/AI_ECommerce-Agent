"""
Chat endpoint tests.

Two categories:

1. STRUCTURAL TESTS (always run, no API key needed)
   - Validates request/response format
   - Tests error handling

2. INTEGRATION TESTS (need OPENAI_API_KEY, skipped otherwise)
   - Tests actual LLM responses
   - Marked with @pytest.mark.skipif

Run: cd backend && pytest tests/test_chat.py -v
"""
import pytest
from httpx import AsyncClient
from app.config import settings

# Flag: skip LLM tests if no API key is configured
has_api_key = bool(settings.openai_api_key and settings.openai_api_key != "sk-your-key-here")


# ══════════════════════════════════════════════════════════════
# Structural tests (always run)
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_chat_empty_messages_returns_400(client: AsyncClient):
    """Sending empty messages should return a clear error."""
    response = await client.post(
        "/api/v1/chat",
        json={"messages": [], "stream": False},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_chat_missing_messages_field(client: AsyncClient):
    """Omitting the messages field entirely should fail validation."""
    response = await client.post(
        "/api/v1/chat",
        json={"stream": False},
    )
    # FastAPI returns 422 for validation errors
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_invalid_message_format(client: AsyncClient):
    """Messages with missing required fields should fail validation."""
    response = await client.post(
        "/api/v1/chat",
        json={
            "messages": [{"content": "Hello"}],  # Missing "role"
            "stream": False,
        },
    )
    assert response.status_code == 422


# ══════════════════════════════════════════════════════════════
# Integration tests (require API key)
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@pytest.mark.skipif(not has_api_key, reason="No OpenAI API key configured")
async def test_chat_non_streaming_returns_response(client: AsyncClient):
    """Non-streaming chat should return a complete response."""
    response = await client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Say hello in one word."}],
            "stream": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0


@pytest.mark.asyncio
@pytest.mark.skipif(not has_api_key, reason="No OpenAI API key configured")
async def test_chat_streaming_returns_sse(client: AsyncClient):
    """
    Streaming chat should return SSE events.

    Note: httpx doesn't natively parse SSE, so we check the
    response headers and raw body format.
    """
    response = await client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Say hi."}],
            "stream": True,
        },
    )
    assert response.status_code == 200
    # SSE responses have this content type
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
@pytest.mark.skipif(not has_api_key, reason="No OpenAI API key configured")
async def test_chat_hebrew_response(client: AsyncClient):
    """Agent should respond in Hebrew when addressed in Hebrew."""
    response = await client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "שלום, מה שלומך?"}],
            "stream": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Check that the response contains Hebrew characters
    # Hebrew Unicode range: \u0590-\u05FF
    has_hebrew = any("\u0590" <= c <= "\u05FF" for c in data["response"])
    assert has_hebrew, f"Expected Hebrew in response, got: {data['response'][:100]}"


@pytest.mark.asyncio
@pytest.mark.skipif(not has_api_key, reason="No OpenAI API key configured")
async def test_chat_multi_turn_context(client: AsyncClient):
    """Agent should use conversation history for context."""
    response = await client.post(
        "/api/v1/chat",
        json={
            "messages": [
                {"role": "user", "content": "My name is TestUser123."},
                {"role": "assistant", "content": "Nice to meet you, TestUser123!"},
                {"role": "user", "content": "What is my name?"},
            ],
            "stream": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "testuser123" in data["response"].lower(), (
        f"Agent should remember name from context, got: {data['response'][:200]}"
    )
