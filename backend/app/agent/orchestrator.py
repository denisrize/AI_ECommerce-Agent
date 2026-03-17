"""
Agent Orchestrator — the brain of the e-commerce agent.

Phase 2: Simple streaming chat (no tools yet).
Phase 3: Will add tool calling loop here.

Architecture note for your multi-LLM goal:
-------------------------------------------
Right now this module hardcodes AsyncOpenAI. When you add model
routing later, this is the file you'll refactor. The plan is:

  1. Define an abstract LLMProvider interface
  2. Create OpenAIProvider, AnthropicProvider, etc.
  3. A Router class picks the best provider per request
  4. This orchestrator calls router.get_provider() instead of
     directly using the OpenAI client

For now, we keep it simple — one provider, one model. The 
abstraction boundary is already here (this module is the ONLY
place that imports openai), so the refactor will be clean.
"""
from openai import AsyncOpenAI
from typing import AsyncGenerator, List, Dict
from app.config import settings

# ── OpenAI Client ─────────────────────────────────────────────
# AsyncOpenAI is the async version of the OpenAI client.
# We create ONE instance and reuse it (it manages its own
# connection pool internally, similar to SQLAlchemy's engine).
#
# Why not create it inside each function? Because each new client
# opens fresh HTTP connections. Reusing one client means connections
# are pooled and reused — faster and more resource-efficient.

client = AsyncOpenAI(api_key=settings.openai_api_key)


# ── System Prompt ─────────────────────────────────────────────
# This is the most important piece of prompt engineering in your
# entire project. It defines WHO the agent is, WHAT it can do,
# and WHERE its boundaries are.
#
# Key principles for a good system prompt:
#
# 1. IDENTITY: Give it a name and role (ShopFlow assistant)
# 2. CAPABILITIES: List what it can help with
# 3. BOUNDARIES: List what it must NOT do (crucial for safety)
# 4. LANGUAGE: Instructions for bilingual behavior
# 5. TONE: Professional but friendly
#
# The system prompt is sent with EVERY request but the user never
# sees it. It's like whispering instructions to an employee before
# they meet a customer.

SYSTEM_PROMPT = """\
You are a helpful customer service agent for ShopFlow, an online electronics \
and home goods store.

You assist customers with:
- Finding products and checking availability
- Order status and tracking
- Product details, pricing, and comparisons
- General store policies (shipping, returns)

Language rules:
- Detect the customer's language from their message.
- If they write in Hebrew, respond entirely in Hebrew.
- If they write in English, respond entirely in English.
- Never mix languages in a single response.

Behavioral rules:
1. Be friendly, professional, and concise.
2. Never fabricate product names, prices, or order numbers. If you \
don't have the information, say so honestly.
3. Do NOT give financial advice or make price predictions ("the price \
might drop next week").
4. Do NOT pressure customers to buy anything. Present facts, let them decide.
5. For complaints, refund disputes, or complex issues — empathize, then \
suggest contacting human support at support@shopflow.com.
6. If asked about topics outside e-commerce (medical, legal, etc.), \
politely decline and redirect.

Current limitations (Phase 2 — no tools yet):
- You cannot look up real products or orders from the database yet.
- You can answer general questions and explain how things work.
- Tool integration is coming in the next phase.
"""


async def stream_chat_completion(
    messages: List[Dict[str, str]],
) -> AsyncGenerator[str, None]:
    """
    Stream a chat completion from OpenAI.

    How streaming works under the hood:
    ------------------------------------
    1. We send the full conversation (system prompt + user messages)
       to OpenAI with stream=True.
    2. Instead of waiting for the complete response, OpenAI sends
       back tiny chunks called "deltas" as they're generated.
    3. Each delta contains a few characters/words of the response.
    4. We yield each chunk immediately — the caller (our SSE route)
       pushes it to the browser in real time.

    The result: the user sees words appearing one by one, exactly
    like ChatGPT. The total response time is the same, but the
    PERCEIVED latency is much lower because they see content
    within the first 100-200ms.

    Args:
        messages: List of message dicts with 'role' and 'content'.
                  Example: [{"role": "user", "content": "Hello!"}]

    Yields:
        Text chunks as they arrive from OpenAI.
    """
    # Prepend system prompt to the conversation
    full_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages,
    ]

    # Call OpenAI with streaming enabled
    response = await client.chat.completions.create(
        model=settings.default_model,
        messages=full_messages,
        stream=True,
        temperature=0.7,  # Slight creativity, but mostly factual
        max_tokens=1000,
    )

    # Iterate over the stream and yield each text chunk
    # The structure of each chunk:
    #   chunk.choices[0].delta.content = "Hello" (or None if no content)
    #
    # delta.content is None for:
    #   - The first chunk (which has role info)
    #   - The last chunk (which has finish_reason)
    #   - Tool call chunks (Phase 3)
    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


async def get_chat_completion(messages: List[Dict[str, str]]) -> str:
    """
    Get a complete (non-streaming) chat response.

    Used for:
    - Testing (easier to assert on a complete string)
    - Non-streaming API calls (stream=false in the request)
    - Internal agent logic that needs the full response at once

    Args:
        messages: Same format as stream_chat_completion.

    Returns:
        The complete response text as a single string.
    """
    full_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages,
    ]

    response = await client.chat.completions.create(
        model=settings.default_model,
        messages=full_messages,
        stream=False,
        temperature=0.7,
        max_tokens=1000,
    )

    return response.choices[0].message.content
