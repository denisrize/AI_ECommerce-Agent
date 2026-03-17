"""
Chat endpoint with SSE streaming.

This is the main interface between the frontend and the AI agent.
It accepts a conversation history and returns the agent's response,
either streamed (SSE) or complete (JSON).

SSE Protocol Recap:
-------------------
Server-Sent Events use a simple text format:

    event: message\n
    data: {"content": "Hello"}\n
    \n

Each event has:
  - An event TYPE (message, done, error) — the client uses this
    to decide how to handle the data.
  - A data PAYLOAD (JSON string) — the actual content.
  - A blank line delimiter — signals the end of one event.

The sse-starlette library handles the formatting for us. We just
yield dicts with "event" and "data" keys.
"""
from fastapi import APIRouter, HTTPException
from typing import List
import json

from sse_starlette.sse import EventSourceResponse
from app.agent.orchestrator import stream_chat_completion, get_chat_completion
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Endpoint ──────────────────────────────────────────────────

@router.post("")
async def chat(request: ChatRequest):
    """
    Chat with the AI agent.

    Two modes:
      stream=true  (default) → Returns Server-Sent Events
      stream=false           → Returns complete JSON response

    Example request:
    ```json
    {
      "messages": [
        {"role": "user", "content": "Do you have headphones?"}
      ],
      "stream": true
    }
    ```

    Example SSE events:
    ```
    event: message
    data: {"content": "Yes"}

    event: message
    data: {"content": ", we have"}

    event: message
    data: {"content": " Wireless Headphones Pro!"}

    event: done
    data: {"status": "complete"}
    ```
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")

    # Convert Pydantic models to dicts for OpenAI
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    if request.stream:
        return EventSourceResponse(
            stream_generator(messages),
            media_type="text/event-stream",
        )
    else:
        response = await get_chat_completion(messages)
        return ChatResponse(response=response)


# ── SSE Generator ─────────────────────────────────────────────

async def stream_generator(messages: List[dict]):
    """
    Async generator that yields SSE events.

    This is the bridge between OpenAI's streaming response and the
    client's EventSource. For each chunk from OpenAI, we wrap it
    in an SSE event and yield it.

    Event types:
      "message" — a chunk of the response text
      "done"    — signals the stream is complete (client stops listening)
      "error"   — something went wrong (client shows error message)

    Why wrap chunks in JSON? Raw text would work for simple cases,
    but JSON lets us add metadata later (e.g., tool call indicators,
    confidence scores, source references) without changing the protocol.
    """
    try:
        async for chunk in stream_chat_completion(messages):
            yield {
                "event": "message",
                "data": json.dumps({"content": chunk}),
            }

        # Signal that the stream is complete
        yield {
            "event": "done",
            "data": json.dumps({"status": "complete"}),
        }

    except Exception as e:
        # Send the error to the client instead of crashing silently.
        # Common errors:
        #   - Invalid API key → AuthenticationError
        #   - Rate limited → RateLimitError
        #   - Model overloaded → APIError
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)}),
        }