#!/usr/bin/env python3
"""
Simple example demonstrating FakeAI Client SDK usage.

This is the minimal example for quick testing.
"""
#  SPDX-License-Identifier: Apache-2.0

from fakeai import FakeAIClient, assert_response_valid, collect_stream_content


def main():
    """Run simple examples."""
    print("FakeAI Client SDK - Simple Example\n")

    # Example 1: Basic chat with auto-started server
    print("1. Basic Chat:")
    with FakeAIClient(auto_start=True) as client:
        response = client.chat("Hello, how are you?")
        assert_response_valid(response)
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Tokens: {response.usage.total_tokens}\n")

    # Example 2: Streaming
    print("2. Streaming Chat:")
    with FakeAIClient(auto_start=True) as client:
        stream = client.stream_chat("Count from 1 to 5")
        content = collect_stream_content(stream)
        print(f"   Content: {content}\n")

    # Example 3: Embeddings
    print("3. Embeddings:")
    with FakeAIClient(auto_start=True) as client:
        response = client.embed("Hello world!")
        print(f"   Embedding size: {len(response.data[0].embedding)}\n")

    # Example 4: Multiple models
    print("4. Multiple Models:")
    with FakeAIClient(auto_start=True) as client:
        models = client.list_models()
        print(f"   Available models: {len(models.data)}")
        for model in models.data[:3]:
            print(f"   - {model.id}\n")

    print("All examples completed successfully!")


if __name__ == "__main__":
    main()
