#!/usr/bin/env python3
"""
Example demonstrating token-based streaming in FakeAI.

This shows how streaming now returns token-sized chunks (words + punctuation)
instead of character-by-character or arbitrary word groups.
"""
import asyncio

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role


async def main():
    # Create service with no delays for faster demo
    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Say hello!")],
        stream=True,
    )

    print("Token-Based Streaming Demo")
    print("=" * 60)
    print("Each chunk represents one token (word or punctuation mark)")
    print("=" * 60)
    print()

    chunk_num = 0
    full_response = ""

    async for chunk in service.create_chat_completion_stream(request):
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            chunk_num += 1

            # Show the token with visual markers
            token_repr = repr(content)  # Shows spaces and special chars
            print(f"Token {chunk_num:2d}: {token_repr:20s} (length: {len(content)})")

    print()
    print("=" * 60)
    print(f"Full response: {full_response}")
    print(f"Total tokens streamed: {chunk_num}")
    print()
    print("Notice how:")
    print("  • Words are separate tokens (e.g., 'Hello')")
    print("  • Punctuation is separate tokens (e.g., '!')")
    print("  • Spaces are added before words automatically")


if __name__ == "__main__":
    asyncio.run(main())
