#!/usr/bin/env python3
"""
Production-Ready Workflow with FakeAI.

This comprehensive example demonstrates a production-grade implementation
combining all FakeAI features:

- Content moderation (safety)
- KV cache reuse (performance)
- Reasoning models (accuracy)
- Streaming responses (user experience)
- Error handling and retries (reliability)
- Metrics collection (observability)
- Tool calling (functionality)
- Multimodal content (richness)

This is a complete reference implementation showing best practices
for building production AI applications with FakeAI.
"""
import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator, Optional

import httpx
from openai import APIError, AsyncOpenAI

# Base URL for FakeAI server
BASE_URL = "http://localhost:8000"


class MessageType(Enum):
    """Types of messages in the system."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class RequestMetrics:
    """Metrics for a single request."""

    request_id: str
    moderation_time_ms: float
    cache_hit: bool
    cached_tokens: int
    llm_time_ms: float
    total_time_ms: float
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int
    retries: int
    error: Optional[str] = None


class ProductionChatService:
    """
    Production-ready chat service with all features.

    Features:
    - Content moderation
    - KV cache optimization
    - Error handling with retries
    - Metrics tracking
    - Support for reasoning models
    - Tool calling
    - Streaming support
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        api_key: str = "test-key",
        max_retries: int = 3,
        timeout: float = 30.0,
        enable_moderation: bool = True,
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
        )
        self.enable_moderation = enable_moderation
        self.metrics: list[RequestMetrics] = []

    async def moderate_content(self, text: str) -> tuple[bool, float]:
        """
        Moderate content before sending to LLM.

        Returns:
            (is_safe, time_ms)
        """
        start = time.time()

        response = await self.client.moderations.create(
            input=text,
            model="omni-moderation-latest",
        )

        elapsed = (time.time() - start) * 1000
        is_safe = not response.results[0].flagged

        return is_safe, elapsed

    async def chat_completion(
        self,
        messages: list[dict],
        model: str = "openai/gpt-oss-120b",
        use_reasoning: bool = False,
        use_streaming: bool = False,
        tools: Optional[list[dict]] = None,
        request_id: Optional[str] = None,
    ) -> tuple[str, RequestMetrics]:
        """
        Process chat completion with full production features.

        Args:
            messages: Conversation history
            model: Model to use
            use_reasoning: Whether to use reasoning model
            use_streaming: Whether to stream response
            tools: Optional tool definitions
            request_id: Optional request ID for tracking

        Returns:
            (response_text, metrics)
        """
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"

        total_start = time.time()
        retries = 0

        # Override model if reasoning requested
        if use_reasoning:
            model = "gpt-oss-120b"

        # Step 1: Moderate user input
        moderation_time = 0.0
        if self.enable_moderation and messages:
            last_user_msg = next(
                (m for m in reversed(messages) if m["role"] == "user"), None
            )

            if last_user_msg:
                user_text = self._extract_text(last_user_msg["content"])
                is_safe, moderation_time = await self.moderate_content(user_text)

                if not is_safe:
                    # Content flagged - return error
                    elapsed = (time.time() - total_start) * 1000
                    metrics = RequestMetrics(
                        request_id=request_id,
                        moderation_time_ms=moderation_time,
                        cache_hit=False,
                        cached_tokens=0,
                        llm_time_ms=0,
                        total_time_ms=elapsed,
                        prompt_tokens=0,
                        completion_tokens=0,
                        reasoning_tokens=0,
                        retries=0,
                        error="content_policy_violation",
                    )
                    self.metrics.append(metrics)

                    return "I'm sorry, I can't process that request.", metrics

        # Step 2: Call LLM with retries
        llm_start = time.time()
        last_error = None

        for attempt in range(3):
            try:
                if use_streaming:
                    # Streaming response
                    response_text = ""
                    cached_tokens = 0
                    prompt_tokens = 0
                    completion_tokens = 0
                    reasoning_tokens = 0

                    stream = await self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools,
                        stream=True,
                    )

                    async for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            response_text += chunk.choices[0].delta.content

                        # Get usage from final chunk
                        if hasattr(chunk, "usage") and chunk.usage:
                            prompt_tokens = chunk.usage.prompt_tokens
                            completion_tokens = chunk.usage.completion_tokens
                            if chunk.usage.prompt_tokens_details:
                                cached_tokens = (
                                    chunk.usage.prompt_tokens_details.cached_tokens
                                )
                            if chunk.usage.completion_tokens_details:
                                reasoning_tokens = (
                                    chunk.usage.completion_tokens_details.reasoning_tokens
                                )

                    llm_time = (time.time() - llm_start) * 1000

                    # Build metrics
                    elapsed = (time.time() - total_start) * 1000
                    metrics = RequestMetrics(
                        request_id=request_id,
                        moderation_time_ms=moderation_time,
                        cache_hit=cached_tokens > 0,
                        cached_tokens=cached_tokens,
                        llm_time_ms=llm_time,
                        total_time_ms=elapsed,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        reasoning_tokens=reasoning_tokens,
                        retries=retries,
                    )
                    self.metrics.append(metrics)

                    return response_text, metrics

                else:
                    # Non-streaming response
                    response = await self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools,
                    )

                    llm_time = (time.time() - llm_start) * 1000

                    # Extract response
                    response_text = response.choices[0].message.content or ""

                    # Handle tool calls
                    if response.choices[0].message.tool_calls:
                        response_text = f"[Tool calls: {len(response.choices[0].message.tool_calls)}]"

                    # Build metrics
                    cached_tokens = 0
                    if response.usage.prompt_tokens_details:
                        cached_tokens = (
                            response.usage.prompt_tokens_details.cached_tokens
                        )

                    reasoning_tokens = 0
                    if response.usage.completion_tokens_details:
                        reasoning_tokens = (
                            response.usage.completion_tokens_details.reasoning_tokens
                        )

                    elapsed = (time.time() - total_start) * 1000
                    metrics = RequestMetrics(
                        request_id=request_id,
                        moderation_time_ms=moderation_time,
                        cache_hit=cached_tokens > 0,
                        cached_tokens=cached_tokens,
                        llm_time_ms=llm_time,
                        total_time_ms=elapsed,
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        reasoning_tokens=reasoning_tokens,
                        retries=retries,
                    )
                    self.metrics.append(metrics)

                    return response_text, metrics

            except Exception as e:
                last_error = str(e)
                retries += 1

                if attempt < 2:
                    # Exponential backoff
                    await asyncio.sleep(2**attempt)
                    continue

                # All retries failed
                elapsed = (time.time() - total_start) * 1000
                metrics = RequestMetrics(
                    request_id=request_id,
                    moderation_time_ms=moderation_time,
                    cache_hit=False,
                    cached_tokens=0,
                    llm_time_ms=(time.time() - llm_start) * 1000,
                    total_time_ms=elapsed,
                    prompt_tokens=0,
                    completion_tokens=0,
                    reasoning_tokens=0,
                    retries=retries,
                    error=last_error,
                )
                self.metrics.append(metrics)

                return f"Error: {last_error}", metrics

    def _extract_text(self, content) -> str:
        """Extract text from message content (handles multimodal)."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            texts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    texts.append(part.get("text", ""))
            return " ".join(texts)
        return ""

    def get_metrics_summary(self) -> dict:
        """Get aggregated metrics."""
        if not self.metrics:
            return {}

        total_requests = len(self.metrics)
        successful = [m for m in self.metrics if not m.error]
        failed = [m for m in self.metrics if m.error]
        cache_hits = [m for m in self.metrics if m.cache_hit]

        return {
            "total_requests": total_requests,
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / total_requests * 100,
            "cache_hit_rate": (
                len(cache_hits) / total_requests * 100 if total_requests > 0 else 0
            ),
            "avg_total_time_ms": (
                sum(m.total_time_ms for m in successful) / len(successful)
                if successful
                else 0
            ),
            "avg_llm_time_ms": (
                sum(m.llm_time_ms for m in successful) / len(successful)
                if successful
                else 0
            ),
            "avg_moderation_time_ms": sum(m.moderation_time_ms for m in self.metrics)
            / total_requests,
            "total_prompt_tokens": sum(m.prompt_tokens for m in successful),
            "total_completion_tokens": sum(m.completion_tokens for m in successful),
            "total_reasoning_tokens": sum(m.reasoning_tokens for m in successful),
            "total_cached_tokens": sum(m.cached_tokens for m in successful),
        }


async def demonstrate_basic_workflow():
    """Demonstrate basic production workflow."""
    print("=" * 80)
    print("PART 1: BASIC PRODUCTION WORKFLOW")
    print("=" * 80)
    print()

    service = ProductionChatService()

    print("Processing: 'What is machine learning?'")
    print("-" * 80)

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What is machine learning?"},
    ]

    response, metrics = await service.chat_completion(messages)

    print(f"Response: {response[:150]}...")
    print()
    print("Metrics:")
    print(f"  Request ID:        {metrics.request_id}")
    print(f"  Moderation time:   {metrics.moderation_time_ms:.2f}ms")
    print(f"  LLM time:          {metrics.llm_time_ms:.2f}ms")
    print(f"  Total time:        {metrics.total_time_ms:.2f}ms")
    print(f"  Cache hit:         {metrics.cache_hit}")
    print(f"  Prompt tokens:     {metrics.prompt_tokens}")
    print(f"  Completion tokens: {metrics.completion_tokens}")
    print()


async def demonstrate_moderation_protection():
    """Demonstrate content moderation protection."""
    print("=" * 80)
    print("PART 2: CONTENT MODERATION PROTECTION")
    print("=" * 80)
    print()

    service = ProductionChatService(enable_moderation=True)

    test_cases = [
        "How do I learn Python?",  # Safe
        "I want to hurt someone",  # Unsafe
        "What's the weather like?",  # Safe
    ]

    for i, user_msg in enumerate(test_cases, 1):
        print(f"Test {i}: {user_msg}")
        print("-" * 80)

        messages = [{"role": "user", "content": user_msg}]

        response, metrics = await service.chat_completion(messages)

        if metrics.error == "content_policy_violation":
            print("🛡️  BLOCKED by content moderation")
            print(f"   Moderation time: {metrics.moderation_time_ms:.2f}ms")
        else:
            print(f"✓ Response: {response[:80]}...")

        print()


async def demonstrate_cache_optimization():
    """Demonstrate KV cache optimization."""
    print("=" * 80)
    print("PART 3: KV CACHE OPTIMIZATION")
    print("=" * 80)
    print()

    service = ProductionChatService()

    # Use consistent system message for cache hits
    system_msg = "You are an expert in computer science."

    print("Making 3 requests with same system message (cache optimization)...")
    print()

    questions = [
        "What is an algorithm?",
        "Explain data structures",
        "What are design patterns?",
    ]

    for i, question in enumerate(questions, 1):
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": question},
        ]

        response, metrics = await service.chat_completion(messages)

        cache_status = "HIT" if metrics.cache_hit else "MISS"
        print(
            f"Request {i}: [{cache_status}] {metrics.cached_tokens} tokens cached, "
            f"{metrics.llm_time_ms:.2f}ms"
        )

    print()


async def demonstrate_reasoning_workflow():
    """Demonstrate reasoning model usage."""
    print("=" * 80)
    print("PART 4: REASONING MODEL WORKFLOW")
    print("=" * 80)
    print()

    service = ProductionChatService()

    print("Using reasoning model for complex problem...")
    print()

    messages = [
        {
            "role": "user",
            "content": "If I have $100 and spend 30% on groceries and 20% on gas, how much remains?",
        }
    ]

    response, metrics = await service.chat_completion(
        messages,
        use_reasoning=True,
    )

    print(f"Response: {response}")
    print()
    print("Metrics:")
    print(f"  Reasoning tokens:  {metrics.reasoning_tokens}")
    print(
        f"  Content tokens:    {metrics.completion_tokens - metrics.reasoning_tokens}"
    )
    print(f"  Total time:        {metrics.total_time_ms:.2f}ms")
    print()


async def demonstrate_streaming_workflow():
    """Demonstrate streaming with production features."""
    print("=" * 80)
    print("PART 5: STREAMING WORKFLOW")
    print("=" * 80)
    print()

    service = ProductionChatService()

    print("Streaming response...")
    print("-" * 80)

    messages = [{"role": "user", "content": "Count from 1 to 5"}]

    response, metrics = await service.chat_completion(
        messages,
        use_streaming=True,
    )

    print(f"\n\nResponse complete!")
    print(f"Total time: {metrics.total_time_ms:.2f}ms")
    print()


async def demonstrate_error_handling():
    """Demonstrate error handling and retries."""
    print("=" * 80)
    print("PART 6: ERROR HANDLING & RETRIES")
    print("=" * 80)
    print()

    # Use invalid URL to trigger errors
    service = ProductionChatService(
        base_url="http://localhost:9999",  # Wrong port
        max_retries=2,
    )

    print("Attempting request to unavailable server...")
    print("(This will demonstrate retry logic)")
    print()

    messages = [{"role": "user", "content": "Hello"}]

    response, metrics = await service.chat_completion(messages)

    if metrics.error:
        print(f"❌ Request failed after {metrics.retries} retries")
        print(f"   Error: {metrics.error[:80]}...")
        print(f"   Total time: {metrics.total_time_ms:.2f}ms")

    print()


async def demonstrate_comprehensive_workflow():
    """Demonstrate comprehensive production workflow."""
    print("=" * 80)
    print("PART 7: COMPREHENSIVE WORKFLOW")
    print("=" * 80)
    print()

    service = ProductionChatService()

    print("Simulating production chat session...")
    print()

    # Conversation with multiple turns
    conversation = []
    system_msg = {"role": "system", "content": "You are a helpful coding assistant."}

    user_inputs = [
        "How do I create a list in Python?",
        "Can you show me an example?",
        "What about dictionaries?",
    ]

    for i, user_input in enumerate(user_inputs, 1):
        print(f"Turn {i}")
        print("-" * 80)
        print(f"User: {user_input}")

        # Build messages
        messages = (
            [system_msg] + conversation + [{"role": "user", "content": user_input}]
        )

        # Get response
        response, metrics = await service.chat_completion(messages)

        print(f"Assistant: {response[:100]}...")
        print(
            f"  Time: {metrics.llm_time_ms:.2f}ms | "
            f"Cached: {metrics.cached_tokens} tokens | "
            f"Cache hit: {metrics.cache_hit}"
        )
        print()

        # Add to conversation
        conversation.append({"role": "user", "content": user_input})
        conversation.append({"role": "assistant", "content": response})

    # Print aggregate metrics
    print("Session Metrics:")
    print("-" * 80)
    summary = service.get_metrics_summary()
    print(f"  Total requests:      {summary['total_requests']}")
    print(f"  Success rate:        {summary['success_rate']:.1f}%")
    print(f"  Cache hit rate:      {summary['cache_hit_rate']:.1f}%")
    print(f"  Avg response time:   {summary['avg_llm_time_ms']:.2f}ms")
    print(
        f"  Total tokens:        {summary['total_prompt_tokens'] + summary['total_completion_tokens']}"
    )
    print(f"  Cached tokens saved: {summary['total_cached_tokens']}")
    print()


async def main():
    """Run all production workflow demonstrations."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "FakeAI Production Workflow Demo" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This demo shows a complete production-ready implementation combining")
    print("all FakeAI features with error handling, retries, and metrics.")
    print()
    input("Press Enter to start...")
    print()

    try:
        await demonstrate_basic_workflow()
        input("Press Enter to continue...")
        print()

        await demonstrate_moderation_protection()
        input("Press Enter to continue...")
        print()

        await demonstrate_cache_optimization()
        input("Press Enter to continue...")
        print()

        await demonstrate_reasoning_workflow()
        input("Press Enter to continue...")
        print()

        await demonstrate_streaming_workflow()
        input("Press Enter to continue...")
        print()

        # Skip error handling demo in normal flow (requires wrong server)
        # await demonstrate_error_handling()

        await demonstrate_comprehensive_workflow()

        print("=" * 80)
        print("PRODUCTION BEST PRACTICES SUMMARY")
        print("=" * 80)
        print()
        print("1. Safety First:")
        print("   • Moderate ALL user input before LLM")
        print("   • Handle flagged content gracefully")
        print("   • Provide appropriate user messages")
        print()
        print("2. Performance Optimization:")
        print("   • Use consistent system messages (cache hits)")
        print("   • Track cached token metrics")
        print("   • Monitor cache hit rates")
        print()
        print("3. Reliability:")
        print("   • Implement retry logic with exponential backoff")
        print("   • Handle all error cases")
        print("   • Set appropriate timeouts")
        print()
        print("4. Observability:")
        print("   • Track request metrics")
        print("   • Log errors with context")
        print("   • Monitor success rates")
        print("   • Aggregate statistics")
        print()
        print("5. Feature Selection:")
        print("   • Use reasoning models for complex tasks")
        print("   • Use streaming for better UX")
        print("   • Use tools when appropriate")
        print()
        print("6. Cost Management:")
        print("   • Track token usage")
        print("   • Optimize with caching")
        print("   • Choose appropriate models")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure FakeAI server is running:")
        print("  python run_server.py")
        print()


if __name__ == "__main__":
    asyncio.run(main())
