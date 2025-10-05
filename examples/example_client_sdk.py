#!/usr/bin/env python3
"""
Example usage of the FakeAI Client SDK and testing utilities.

This script demonstrates all features of the FakeAI client SDK including:
- FakeAIClient wrapper
- Context managers
- Testing assertions
- Pytest fixtures
"""
#  SPDX-License-Identifier: Apache-2.0

import time

from fakeai import (
    FakeAIClient,
    temporary_server,
    assert_response_valid,
    assert_tokens_in_range,
    assert_streaming_valid,
    collect_stream_content,
    measure_stream_timing,
    AppConfig,
)


def example_basic_usage():
    """Example 1: Basic usage with auto-started server."""
    print("=" * 70)
    print("Example 1: Basic Usage with Auto-Started Server")
    print("=" * 70)

    # Auto-start server using context manager
    with FakeAIClient(auto_start=True) as client:
        # Simple chat
        response = client.chat("Hello, how are you?")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Tokens: {response.usage.total_tokens}")

        # Validate response
        assert_response_valid(response)
        assert_tokens_in_range(response.usage, min_prompt=3, min_completion=1)
        print("✓ Response validation passed!")

    print()


def example_custom_config():
    """Example 2: Custom configuration for server."""
    print("=" * 70)
    print("Example 2: Custom Configuration")
    print("=" * 70)

    # Create custom config
    config = AppConfig(
        response_delay=0.0,  # No delay for fast tests
        random_delay=False,  # Predictable timing
        require_api_key=False,  # No auth needed
        enable_audio=True,
        enable_moderation=True,
    )

    with FakeAIClient(config=config, auto_start=True) as client:
        # Test chat with custom config
        response = client.chat(
            "Write a short poem about testing.",
            model="openai/gpt-oss-120b",
            max_tokens=50,
        )
        print(f"Response: {response.choices[0].message.content}")

        # Validate tokens are within expected range
        assert_tokens_in_range(
            response.usage,
            min_prompt=5,
            max_prompt=20,
            min_completion=10,
            max_completion=60,
        )
        print("✓ Token validation passed!")

    print()


def example_streaming():
    """Example 3: Streaming responses with timing measurements."""
    print("=" * 70)
    print("Example 3: Streaming with Timing Measurements")
    print("=" * 70)

    with FakeAIClient(auto_start=True) as client:
        # Stream a response
        print("Streaming response: ", end="", flush=True)
        stream = client.stream_chat(
            "Count from 1 to 10.",
            model="meta-llama/Llama-3.1-8B-Instruct",
        )

        # Measure timing
        timing = measure_stream_timing(stream)

        print(f"\n\nTiming metrics:")
        print(f"  - Time to first token: {timing['time_to_first_token']*1000:.2f}ms")
        print(f"  - Total time: {timing['total_time']:.2f}s")
        print(f"  - Chunks received: {timing['chunks_count']}")
        print(f"  - Avg inter-token latency: {timing['avg_inter_token_latency']*1000:.2f}ms")

        # Create another stream for validation
        stream2 = client.stream_chat("Hello!", model="openai/gpt-oss-120b")
        assert_streaming_valid(stream2)
        print("✓ Stream validation passed!")

    print()


def example_embeddings():
    """Example 4: Creating embeddings."""
    print("=" * 70)
    print("Example 4: Embeddings")
    print("=" * 70)

    with FakeAIClient(auto_start=True) as client:
        # Single text embedding
        response = client.embed("Hello world!")
        embedding = response.data[0].embedding
        print(f"Embedding dimensions: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")

        # Multiple texts
        texts = ["First text", "Second text", "Third text"]
        response = client.embed(texts)
        print(f"\nEmbedded {len(response.data)} texts")
        for i, data in enumerate(response.data):
            print(f"  Text {i+1}: {len(data.embedding)} dimensions")

    print()


def example_moderation():
    """Example 5: Content moderation."""
    print("=" * 70)
    print("Example 5: Content Moderation")
    print("=" * 70)

    config = AppConfig(
        response_delay=0.0,
        enable_moderation=True,
        moderation_threshold=0.5,
    )

    with FakeAIClient(config=config, auto_start=True) as client:
        # Check benign content
        safe_text = "Hello, how are you today?"
        result = client.moderate(safe_text)
        print(f"Safe text flagged: {result.results[0].flagged}")

        # Check potentially harmful content
        harmful_text = "I want to hurt someone badly with violence"
        result = client.moderate(harmful_text)
        print(f"Harmful text flagged: {result.results[0].flagged}")

        if result.results[0].flagged:
            categories = result.results[0].categories.model_dump()
            flagged_categories = [k for k, v in categories.items() if v]
            print(f"Flagged categories: {flagged_categories}")

    print()


def example_temporary_server():
    """Example 6: Using temporary_server context manager."""
    print("=" * 70)
    print("Example 6: Temporary Server Context Manager")
    print("=" * 70)

    # Custom config for temporary server
    config = AppConfig(
        response_delay=0.1,
        enable_audio=True,
        enable_safety_features=True,
    )

    with temporary_server(config=config) as client:
        # Server is automatically started and stopped
        print("Server is running!")

        # Test multiple endpoints
        models = client.list_models()
        print(f"Available models: {len(models.data)}")

        # Chat completion
        response = client.chat("What is 2+2?")
        print(f"Response: {response.choices[0].message.content}")

        # Embeddings
        embedding_response = client.embed("Test text")
        print(f"Embedding size: {len(embedding_response.data[0].embedding)}")

        print("✓ All endpoints working!")

    print("Server automatically stopped!")
    print()


def example_model_operations():
    """Example 7: Model listing and retrieval."""
    print("=" * 70)
    print("Example 7: Model Operations")
    print("=" * 70)

    with FakeAIClient(auto_start=True) as client:
        # List all models
        models = client.list_models()
        print(f"Total models: {len(models.data)}")
        print("\nFirst 5 models:")
        for model in models.data[:5]:
            print(f"  - {model.id} (owner: {model.owned_by})")

        # Get specific model
        model = client.get_model("openai/gpt-oss-120b")
        print(f"\nModel details for 'openai/gpt-oss-120b':")
        print(f"  - Context window: {model.context_window}")
        print(f"  - Max output tokens: {model.max_output_tokens}")
        print(f"  - Supports vision: {model.supports_vision}")
        print(f"  - Supports tools: {model.supports_tools}")

        # Get a custom model (auto-created)
        custom_model = client.get_model("my-custom-model")
        print(f"\nCustom model auto-created: {custom_model.id}")

    print()


def example_advanced_chat():
    """Example 8: Advanced chat with system message and streaming."""
    print("=" * 70)
    print("Example 8: Advanced Chat Features")
    print("=" * 70)

    with FakeAIClient(auto_start=True) as client:
        # Chat with system message
        response = client.chat(
            "Tell me a joke",
            system="You are a comedian who tells programming jokes.",
            model="openai/gpt-oss-120b",
            temperature=0.8,
            max_tokens=100,
        )
        print(f"Joke: {response.choices[0].message.content}\n")

        # Streaming with system message
        print("Streaming response with system message:")
        stream = client.stream_chat(
            "Tell me another joke",
            system="You are a comedian who tells programming jokes.",
            model="meta-llama/Llama-3.1-8B-Instruct",
        )

        # Collect and display content
        content = collect_stream_content(stream)
        print(f"{content}\n")

        print("✓ Advanced features working!")

    print()


def example_error_handling():
    """Example 9: Error handling and validation."""
    print("=" * 70)
    print("Example 9: Error Handling")
    print("=" * 70)

    with FakeAIClient(auto_start=True) as client:
        # Test with various inputs
        try:
            # Valid request
            response = client.chat("Hello!", max_tokens=10)
            assert_response_valid(response)
            print("✓ Valid request passed")

            # Token range validation
            assert_tokens_in_range(response.usage, min_prompt=1, min_completion=1)
            print("✓ Token range validation passed")

            # Streaming validation
            stream = client.stream_chat("Hi!")
            assert_streaming_valid(stream)
            print("✓ Streaming validation passed")

        except AssertionError as e:
            print(f"✗ Validation failed: {e}")

    print()


def example_performance_testing():
    """Example 10: Performance testing with timing."""
    print("=" * 70)
    print("Example 10: Performance Testing")
    print("=" * 70)

    # Use zero delay for performance testing
    config = AppConfig(response_delay=0.0, random_delay=False)

    with FakeAIClient(config=config, auto_start=True) as client:
        # Measure non-streaming performance
        start = time.time()
        response = client.chat("Test message")
        elapsed = time.time() - start
        print(f"Non-streaming request: {elapsed*1000:.2f}ms")

        # Measure streaming performance
        start = time.time()
        stream = client.stream_chat("Test message")
        timing = measure_stream_timing(stream)
        print(f"Streaming request:")
        print(f"  - TTFT: {timing['time_to_first_token']*1000:.2f}ms")
        print(f"  - Total: {timing['total_time']*1000:.2f}ms")
        print(f"  - Chunks: {timing['chunks_count']}")

        # Batch requests
        print("\nBatch processing 10 requests:")
        start = time.time()
        for i in range(10):
            response = client.chat(f"Request {i+1}")
        elapsed = time.time() - start
        print(f"Total time: {elapsed:.2f}s")
        print(f"Avg per request: {elapsed/10*1000:.2f}ms")

    print()


def main():
    """Run all examples."""
    print("\n")
    print("=" * 70)
    print("FakeAI Client SDK Examples")
    print("=" * 70)
    print("\n")

    examples = [
        ("Basic Usage", example_basic_usage),
        ("Custom Config", example_custom_config),
        ("Streaming", example_streaming),
        ("Embeddings", example_embeddings),
        ("Moderation", example_moderation),
        ("Temporary Server", example_temporary_server),
        ("Model Operations", example_model_operations),
        ("Advanced Chat", example_advanced_chat),
        ("Error Handling", example_error_handling),
        ("Performance Testing", example_performance_testing),
    ]

    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"✗ Example '{name}' failed: {e}\n")
            import traceback
            traceback.print_exc()

    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
