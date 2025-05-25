#!/usr/bin/env python3
"""
Example script for using the FakeAI server with the OpenAI Python client.

This script demonstrates various uses of the FakeAI server using the official OpenAI client.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time

from openai import OpenAI


async def main():
    """Run examples of using the FakeAI server."""
    print("FakeAI Server Example Client")
    print("============================\n")

    # Initialize the client with the FakeAI server URL
    client = OpenAI(
        api_key="sk-fakeai-1234567890abcdef",  # Any key from the allowed list
        base_url="http://localhost:8000/v1",
    )

    print("1. List available models:")
    models = client.models.list()
    for model in models.data:
        print(f"  - {model.id} (owner: {model.owned_by})")
    print()

    # Chat completion example
    print("2. Chat completion example:")
    start_time = time.time()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Tell me about artificial intelligence in 2-3 sentences.",
            },
        ],
    )
    elapsed = time.time() - start_time
    print(f"  Response (in {elapsed:.2f}s): {response.choices[0].message.content}")
    print(
        f"  Usage: {response.usage.prompt_tokens} prompt tokens, {response.usage.completion_tokens} completion tokens"
    )
    print()

    # Streaming chat completion
    print("3. Streaming chat completion example:")
    print("  Response: ", end="", flush=True)
    start_time = time.time()
    for chunk in client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Write a short poem about technology."}],
        stream=True,
    ):
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    elapsed = time.time() - start_time
    print(f"\n  Completed in {elapsed:.2f}s")
    print()

    # Text completion example
    print("4. Text completion example:")
    start_time = time.time()
    response = client.completions.create(
        model="gpt-3.5-turbo", prompt="Once upon a time,", max_tokens=30
    )
    elapsed = time.time() - start_time
    print(f"  Response (in {elapsed:.2f}s): {response.choices[0].text}")
    print()

    # Embedding example
    print("5. Embedding example:")
    start_time = time.time()
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input="The quick brown fox jumps over the lazy dog.",
    )
    elapsed = time.time() - start_time
    embedding = response.data[0].embedding
    print(f"  Embedding (in {elapsed:.2f}s): Vector with {len(embedding)} dimensions")
    print(f"  First few values: {embedding[:5]}")
    print(f"  Usage: {response.usage.total_tokens} tokens")
    print()

    # Image generation example
    print("6. Image generation example:")
    start_time = time.time()
    response = client.images.generate(
        model="dall-e-3",
        prompt="A futuristic city with flying cars and tall skyscrapers",
        n=1,
        size="1024x1024",
    )
    elapsed = time.time() - start_time
    print(f"  Image URL (in {elapsed:.2f}s): {response.data[0].url}")
    print()

    print("All examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
