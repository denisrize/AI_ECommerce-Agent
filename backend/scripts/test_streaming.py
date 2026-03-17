"""
Manual test script for the chat endpoint.

Run with:
    cd backend
    conda activate ecommerce-agent
    python -m scripts.test_streaming

Prerequisites:
    - App running: uvicorn app.main:app --reload --port 8000
    - Valid OPENAI_API_KEY in backend/.env

This tests three things:
    1. SSE streaming works (you see words appear one by one)
    2. Non-streaming works (you get a complete JSON response)
    3. Hebrew detection works (agent responds in Hebrew)
"""
import asyncio
import json
import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def test_streaming():
    """Test SSE streaming — words should appear progressively."""
    print("=" * 60)
    print("TEST 1: SSE Streaming")
    print("=" * 60)
    print("Sending: 'What products do you sell?'\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/chat/",
            json={
                "messages": [
                    {"role": "user", "content": "What products do you sell?"}
                ],
                "stream": True,
            },
        ) as response:
            # Read the SSE stream line by line
            # SSE format: "event: message\ndata: {...}\n\n"
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    if "content" in data:
                        # Print each chunk immediately (no newline)
                        # This shows the streaming effect in the terminal
                        print(data["content"], end="", flush=True)
                    elif "status" in data:
                        print(f"\n\n✅ Stream complete.\n")


async def test_non_streaming():
    """Test non-streaming mode — should return complete JSON."""
    print("=" * 60)
    print("TEST 2: Non-streaming (JSON response)")
    print("=" * 60)
    print("Sending: 'Tell me about your return policy.'\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/chat/",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Tell me about your return policy.",
                    }
                ],
                "stream": False,
            },
        )

        data = response.json()
        print(data["response"])
        print(f"\n✅ Non-streaming complete.\n")


async def test_hebrew():
    """Test Hebrew language detection — agent should respond in Hebrew."""
    print("=" * 60)
    print("TEST 3: Hebrew response")
    print("=" * 60)
    print("Sending: 'שלום, אילו מוצרים יש לכם?'\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "שלום, אילו מוצרים יש לכם?",
                    }
                ],
                "stream": False,
            },
        )

        data = response.json()
        print(data["response"])
        print(f"\n✅ Hebrew test complete.\n")


async def test_multi_turn():
    """Test multi-turn conversation — context should be maintained."""
    print("=" * 60)
    print("TEST 4: Multi-turn conversation")
    print("=" * 60)
    print("Turn 1: 'My name is David.'")
    print("Turn 2: 'What is my name?'\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # The client sends the FULL conversation history each time.
        # This is how stateless chat works — the server doesn't
        # remember anything between requests.
        response = await client.post(
            f"{BASE_URL}/chat",
            json={
                "messages": [
                    {"role": "user", "content": "My name is David."},
                    {
                        "role": "assistant",
                        "content": "Nice to meet you, David! How can I help?",
                    },
                    {"role": "user", "content": "What is my name?"},
                ],
                "stream": False,
            },
        )

        data = response.json()
        print(f"Agent: {data['response']}")

        # Verify the agent remembered the name from context
        if "david" in data["response"].lower():
            print("\n✅ Multi-turn context works — agent remembered the name.\n")
        else:
            print("\n⚠️  Agent might not have picked up the name.\n")


async def test_policy_boundary():
    """Test that the agent refuses out-of-scope requests."""
    print("=" * 60)
    print("TEST 5: Policy boundary (should refuse medical advice)")
    print("=" * 60)
    print("Sending: 'I have a headache, what medicine should I take?'\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "I have a headache, what medicine should I take?",
                    }
                ],
                "stream": False,
            },
        )

        data = response.json()
        print(f"Agent: {data['response']}")
        print(f"\n✅ Policy boundary test complete.\n")


async def main():
    print("\n🤖 ShopFlow Agent — Manual Test Suite\n")
    await test_streaming()
    await test_non_streaming()
    await test_hebrew()
    await test_multi_turn()
    await test_policy_boundary()
    print("=" * 60)
    print("All manual tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
