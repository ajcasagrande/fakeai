#!/usr/bin/env python3
"""
KV Cache Demonstration with FakeAI.

This example demonstrates FakeAI's KV cache reuse simulation, showing:
- Cache hits vs misses with repeated prompts
- Token reuse metrics
- Smart routing with multiple workers
- Latency improvements with cache hits
- Comparison of cached vs uncached requests

The KV cache simulates NVIDIA AI-Dynamo's intelligent prefix caching,
which dramatically reduces latency for repeated prompt prefixes.
"""
import asyncio
import time

from openai import AsyncOpenAI

# Base URL for FakeAI server (start with: python run_server.py)
BASE_URL = "http://localhost:8000"


async def demonstrate_basic_cache():
    """Demonstrate basic KV cache behavior with repeated prompts."""
    print("=" * 80)
    print("PART 1: BASIC KV CACHE DEMONSTRATION")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    # Define a common prefix that will be cached
    system_message = """You are a helpful assistant with expertise in programming.
You provide clear, concise answers with code examples when appropriate.
Always explain your reasoning step by step."""

    # First request - cache miss (no prefix cached yet)
    print("Request 1: Initial request (CACHE MISS expected)")
    print("-" * 80)

    start = time.time()
    response1 = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": "What is Python?"},
        ],
    )
    latency1 = (time.time() - start) * 1000

    print(f"Response: {response1.choices[0].message.content[:100]}...")
    print(f"Prompt tokens: {response1.usage.prompt_tokens}")
    print(f"Cached tokens: {response1.usage.prompt_tokens_details.cached_tokens}")
    print(f"Latency: {latency1:.2f}ms")
    print()

    # Second request - cache hit (same system message prefix)
    print("Request 2: Same system message (CACHE HIT expected)")
    print("-" * 80)

    start = time.time()
    response2 = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": "What is JavaScript?"},
        ],
    )
    latency2 = (time.time() - start) * 1000

    print(f"Response: {response2.choices[0].message.content[:100]}...")
    print(f"Prompt tokens: {response2.usage.prompt_tokens}")
    print(f"Cached tokens: {response2.usage.prompt_tokens_details.cached_tokens}")
    print(f"Latency: {latency2:.2f}ms")
    print()

    # Calculate speedup
    speedup = ((latency1 - latency2) / latency1 * 100) if latency1 > 0 else 0
    print(f"Latency improvement: {speedup:.1f}%")
    print(f"Token reuse: {response2.usage.prompt_tokens_details.cached_tokens} tokens")
    print()


async def demonstrate_conversation_cache():
    """Demonstrate cache reuse in a multi-turn conversation."""
    print("=" * 80)
    print("PART 2: MULTI-TURN CONVERSATION WITH CACHE")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    # Build a conversation with growing context
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to calculate factorial."},
    ]

    print("Turn 1: Initial question")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
    )

    print(f"Prompt tokens: {response.usage.prompt_tokens}")
    print(f"Cached tokens: {response.usage.prompt_tokens_details.cached_tokens}")
    print()

    # Add assistant response to conversation
    messages.append(
        {"role": "assistant", "content": response.choices[0].message.content}
    )

    # Turn 2 - entire conversation prefix should be cached
    messages.append(
        {"role": "user", "content": "Now add error handling to that function."}
    )

    print("Turn 2: Follow-up question (entire prefix cached)")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
    )

    print(f"Prompt tokens: {response.usage.prompt_tokens}")
    print(f"Cached tokens: {response.usage.prompt_tokens_details.cached_tokens}")
    print(
        f"Cache hit rate: {(response.usage.prompt_tokens_details.cached_tokens / response.usage.prompt_tokens * 100):.1f}%"
    )
    print()

    # Turn 3
    messages.append(
        {"role": "assistant", "content": response.choices[0].message.content}
    )
    messages.append({"role": "user", "content": "Can you add type hints?"})

    print("Turn 3: Another follow-up (even more cached)")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
    )

    print(f"Prompt tokens: {response.usage.prompt_tokens}")
    print(f"Cached tokens: {response.usage.prompt_tokens_details.cached_tokens}")
    print(
        f"Cache hit rate: {(response.usage.prompt_tokens_details.cached_tokens / response.usage.prompt_tokens * 100):.1f}%"
    )
    print()


async def demonstrate_cache_metrics():
    """Show overall cache performance metrics."""
    print("=" * 80)
    print("PART 3: CACHE PERFORMANCE METRICS")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    # Make multiple requests to build up cache statistics
    print("Making 10 requests with varying prefixes...")
    print()

    common_prefix = "You are an expert in machine learning and AI."

    for i in range(10):
        messages = [
            {"role": "system", "content": common_prefix},
            {
                "role": "user",
                "content": f"Question {i+1}: Tell me about neural networks.",
            },
        ]

        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
        )

        cached_pct = (
            (
                response.usage.prompt_tokens_details.cached_tokens
                / response.usage.prompt_tokens
                * 100
            )
            if response.usage.prompt_tokens > 0
            else 0
        )

        print(
            f"Request {i+1}: {response.usage.prompt_tokens} tokens, "
            f"{response.usage.prompt_tokens_details.cached_tokens} cached ({cached_pct:.1f}%)"
        )

    print()
    print("Check http://localhost:8000/metrics for detailed cache statistics!")
    print()


async def demonstrate_cache_comparison():
    """Compare performance with and without cache."""
    print("=" * 80)
    print("PART 4: WITH vs WITHOUT CACHE COMPARISON")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    # Test with cache enabled (repeated prompt)
    print("With Cache: Making 5 requests with same prefix")
    print("-" * 80)

    cached_latencies = []
    cached_prefix = "You are a helpful assistant specialized in data science."

    for i in range(5):
        start = time.time()
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": cached_prefix},
                {"role": "user", "content": f"Question {i+1}"},
            ],
        )
        latency = (time.time() - start) * 1000
        cached_latencies.append(latency)

        print(
            f"Request {i+1}: {latency:.2f}ms, "
            f"cached: {response.usage.prompt_tokens_details.cached_tokens} tokens"
        )

    print()

    # Test without cache (different prompts each time)
    print("Without Cache: Making 5 requests with different prefixes")
    print("-" * 80)

    uncached_latencies = []

    for i in range(5):
        start = time.time()
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": f"You are assistant number {i+1}."},
                {"role": "user", "content": f"Question {i+1}"},
            ],
        )
        latency = (time.time() - start) * 1000
        uncached_latencies.append(latency)

        print(
            f"Request {i+1}: {latency:.2f}ms, "
            f"cached: {response.usage.prompt_tokens_details.cached_tokens} tokens"
        )

    print()

    # Calculate statistics
    avg_cached = sum(cached_latencies) / len(cached_latencies)
    avg_uncached = sum(uncached_latencies) / len(uncached_latencies)
    improvement = (
        ((avg_uncached - avg_cached) / avg_uncached * 100) if avg_uncached > 0 else 0
    )

    print("RESULTS:")
    print(f"Average latency WITH cache:    {avg_cached:.2f}ms")
    print(f"Average latency WITHOUT cache: {avg_uncached:.2f}ms")
    print(f"Performance improvement:       {improvement:.1f}%")
    print()


async def demonstrate_streaming_with_cache():
    """Show cache benefits with streaming responses."""
    print("=" * 80)
    print("PART 5: STREAMING WITH CACHE")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    system_msg = "You are a helpful assistant."

    # First streaming request
    print("Streaming Request 1: (cache miss)")
    print("-" * 80)

    start = time.time()
    first_token_time = None

    stream = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": "Count to 5"},
        ],
        stream=True,
    )

    chunk_count = 0
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            if first_token_time is None:
                first_token_time = (time.time() - start) * 1000
            chunk_count += 1

    total_time1 = (time.time() - start) * 1000

    print(f"Time to first token: {first_token_time:.2f}ms")
    print(f"Total time: {total_time1:.2f}ms")
    print(f"Chunks received: {chunk_count}")
    print()

    # Second streaming request with same prefix
    print("Streaming Request 2: (cache hit on system message)")
    print("-" * 80)

    start = time.time()
    first_token_time = None

    stream = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": "Count to 10"},
        ],
        stream=True,
    )

    chunk_count = 0
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            if first_token_time is None:
                first_token_time = (time.time() - start) * 1000
            chunk_count += 1

    total_time2 = (time.time() - start) * 1000

    print(f"Time to first token: {first_token_time:.2f}ms")
    print(f"Total time: {total_time2:.2f}ms")
    print(f"Chunks received: {chunk_count}")
    print()

    ttft_improvement = (
        ((total_time1 - total_time2) / total_time1 * 100) if total_time1 > 0 else 0
    )
    print(f"TTFT improvement from cache: {ttft_improvement:.1f}%")
    print()


async def main():
    """Run all KV cache demonstrations."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "FakeAI KV Cache Demonstration" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This demo shows how FakeAI simulates NVIDIA AI-Dynamo's KV cache reuse,")
    print("which dramatically improves latency for requests with repeated prefixes.")
    print()
    input("Press Enter to start...")
    print()

    try:
        await demonstrate_basic_cache()
        input("Press Enter to continue...")
        print()

        await demonstrate_conversation_cache()
        input("Press Enter to continue...")
        print()

        await demonstrate_cache_metrics()
        input("Press Enter to continue...")
        print()

        await demonstrate_cache_comparison()
        input("Press Enter to continue...")
        print()

        await demonstrate_streaming_with_cache()

        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print("KV Cache Benefits:")
        print("  • Reduces latency for requests with common prefixes")
        print("  • Especially valuable for:")
        print("    - Multi-turn conversations (entire history cached)")
        print("    - Requests with common system messages")
        print("    - RAG systems with fixed instruction templates")
        print("    - Agent workflows with repeated tool descriptions")
        print()
        print("Metrics tracked:")
        print("  • cached_tokens in usage.prompt_tokens_details")
        print("  • Cache hit rate in /metrics endpoint")
        print("  • Token reuse percentage")
        print("  • Latency improvements")
        print()
        print("View detailed metrics: http://localhost:8000/metrics")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure FakeAI server is running:")
        print("  python run_server.py")
        print()


if __name__ == "__main__":
    asyncio.run(main())
