#!/usr/bin/env python3
"""
Example demonstrating reasoning content support in FakeAI.

This shows how reasoning models (gpt-oss and deepseek-ai/DeepSeek-R1) include reasoning_content
showing their internal thinking process before generating the final answer.

GPT-OSS models are OpenAI's new open-source reasoning models (Apache 2.0, Aug 2025).
"""
import asyncio
from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role


async def test_non_streaming():
    """Test non-streaming response with reasoning content."""
    print("=" * 70)
    print("NON-STREAMING GPT-OSS MODEL TEST")
    print("=" * 70)
    print()

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Test with gpt-oss-120b model
    request = ChatCompletionRequest(
        model="gpt-oss-120b",
        messages=[Message(role=Role.USER, content="What is 2+2?")],
    )

    response = await service.create_chat_completion(request)

    print(f"Model: {response.model}")
    print(f"Message content: {response.choices[0].message.content}")
    print()
    print("Reasoning content:")
    print(response.choices[0].message.reasoning_content)
    print()
    print(f"Token usage:")
    print(f"  Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    if response.usage.completion_tokens_details:
        print(f"  Reasoning tokens: {response.usage.completion_tokens_details.reasoning_tokens}")
    print()


async def test_streaming():
    """Test streaming response with reasoning content."""
    print("=" * 70)
    print("STREAMING GPT-OSS MODEL TEST")
    print("=" * 70)
    print()

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Test with gpt-oss-20b model (optimized for low latency)
    request = ChatCompletionRequest(
        model="gpt-oss-20b",
        messages=[Message(role=Role.USER, content="Explain quantum computing")],
        stream=True,
    )

    print("Streaming reasoning tokens (shown as they arrive):")
    print("-" * 70)

    reasoning_chunks = []
    content_chunks = []

    async for chunk in service.create_chat_completion_stream(request):
        if chunk.choices and chunk.choices[0].delta:
            delta = chunk.choices[0].delta

            if delta.reasoning_content:
                reasoning_chunks.append(delta.reasoning_content)
                print(f"[REASONING] {delta.reasoning_content}", end="", flush=True)

            if delta.content:
                content_chunks.append(delta.content)
                # Start new line when transitioning from reasoning to content
                if reasoning_chunks and not content_chunks[:-1]:
                    print()
                    print()
                    print("Streaming content tokens (shown as they arrive):")
                    print("-" * 70)
                print(f"[CONTENT] {delta.content}", end="", flush=True)

    print()
    print()
    print("=" * 70)
    print("FULL RESPONSE ASSEMBLED")
    print("=" * 70)
    print()
    print("Reasoning:")
    print("".join(reasoning_chunks))
    print()
    print("Content:")
    print("".join(content_chunks))
    print()


async def test_regular_model():
    """Test that regular models don't include reasoning content."""
    print("=" * 70)
    print("REGULAR MODEL TEST (GPT-4 - NO REASONING)")
    print("=" * 70)
    print()

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Hello!")],
    )

    response = await service.create_chat_completion(request)

    print(f"Model: {response.model}")
    print(f"Message content: {response.choices[0].message.content}")
    print(f"Reasoning content: {response.choices[0].message.reasoning_content}")
    print()
    print("Note: Regular models like openai/gpt-oss-120b don't have reasoning content.")
    print()


async def main():
    """Run all tests."""
    await test_non_streaming()
    await test_streaming()
    await test_regular_model()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("GPT-OSS Reasoning Models (gpt-oss-120b, gpt-oss-20b):")
    print("  • Open-source under Apache 2.0 license (Aug 2025)")
    print("  • Mixture-of-experts architecture")
    print("  • reasoning_content field showing internal thinking")
    print("  • reasoning_tokens in usage.completion_tokens_details")
    print("  • In streaming: reasoning tokens come first, then content")
    print()
    print("O1 Models (deepseek-ai/DeepSeek-R1, deepseek-ai/DeepSeek-R1, deepseek-ai/DeepSeek-R1-Distill-Qwen-32B) - Legacy:")
    print("  • Same reasoning content features as gpt-oss")
    print()
    print("Regular models (openai/gpt-oss-120b, meta-llama/Llama-3.1-8B-Instruct) do NOT include reasoning.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
