#!/usr/bin/env python3
"""
Tests for the FakeAI Client SDK and testing utilities.

This test suite demonstrates using the FakeAI client SDK fixtures and
assertions for comprehensive testing.
"""
#  SPDX-License-Identifier: Apache-2.0

import pytest
from openai import OpenAI

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
from fakeai.client import fakeai_client, fakeai_client_with_auth, fakeai_running_server


class TestFakeAIClientBasics:
    """Test basic FakeAIClient functionality."""

    def test_client_chat(self, fakeai_client):
        """Test basic chat completion."""
        response = fakeai_client.chat("Hello!")
        assert_response_valid(response)
        assert response.choices[0].message.content
        assert response.usage.total_tokens > 0

    def test_client_chat_with_system(self, fakeai_client):
        """Test chat with system message."""
        response = fakeai_client.chat(
            "Tell me a joke",
            system="You are a comedian.",
            model="openai/gpt-oss-120b",
        )
        assert_response_valid(response)
        assert response.model == "openai/gpt-oss-120b"

    def test_client_streaming(self, fakeai_client):
        """Test streaming chat completion."""
        stream = fakeai_client.stream_chat("Count to 5")
        assert_streaming_valid(stream)

    def test_client_embeddings(self, fakeai_client):
        """Test embeddings creation."""
        response = fakeai_client.embed("Hello world")
        assert len(response.data) == 1
        assert len(response.data[0].embedding) > 0

    def test_client_embeddings_batch(self, fakeai_client):
        """Test batch embeddings creation."""
        texts = ["First", "Second", "Third"]
        response = fakeai_client.embed(texts)
        assert len(response.data) == 3
        for data in response.data:
            assert len(data.embedding) > 0

    def test_client_moderation(self, fakeai_client):
        """Test content moderation."""
        response = fakeai_client.moderate("Hello world")
        assert len(response.results) > 0

    def test_client_list_models(self, fakeai_client):
        """Test listing models."""
        models = fakeai_client.list_models()
        assert len(models.data) > 0

    def test_client_get_model(self, fakeai_client):
        """Test getting specific model."""
        model = fakeai_client.get_model("openai/gpt-oss-120b")
        assert model.id == "openai/gpt-oss-120b"
        assert model.context_window > 0

    def test_client_custom_model(self, fakeai_client):
        """Test auto-creation of custom model."""
        model = fakeai_client.get_model("my-custom-model")
        assert model.id == "my-custom-model"


class TestFakeAIClientWithAuth:
    """Test FakeAIClient with authentication."""

    def test_client_with_auth(self, fakeai_client_with_auth):
        """Test client with authentication enabled."""
        response = fakeai_client_with_auth.chat("Hello!")
        assert_response_valid(response)

    def test_auth_required(self):
        """Test that authentication is required when configured."""
        config = AppConfig(
            response_delay=0.0,
            require_api_key=True,
            api_keys=["test-key"],
        )

        with FakeAIClient(config=config, auto_start=True, api_key="test-key") as client:
            response = client.chat("Hello!")
            assert_response_valid(response)


class TestResponseValidation:
    """Test response validation utilities."""

    def test_assert_response_valid(self, fakeai_client):
        """Test response validation assertion."""
        response = fakeai_client.chat("Hello!")
        assert_response_valid(response)  # Should not raise

    def test_assert_tokens_in_range(self, fakeai_client):
        """Test token range validation."""
        response = fakeai_client.chat("Hello!")
        assert_tokens_in_range(response.usage, min_prompt=1, min_completion=1)

    def test_assert_tokens_with_max(self, fakeai_client):
        """Test token range validation with maximum."""
        response = fakeai_client.chat("Hi", max_tokens=20)
        assert_tokens_in_range(
            response.usage,
            min_prompt=1,
            max_prompt=10,
            min_completion=1,
            max_completion=30,
        )

    def test_token_validation_failure(self, fakeai_client):
        """Test that token validation fails when out of range."""
        response = fakeai_client.chat("Hello!")
        with pytest.raises(AssertionError):
            assert_tokens_in_range(
                response.usage,
                min_prompt=10000,  # Unrealistically high
            )


class TestStreamingValidation:
    """Test streaming validation utilities."""

    def test_assert_streaming_valid(self, fakeai_client):
        """Test streaming validation assertion."""
        stream = fakeai_client.stream_chat("Hello!")
        assert_streaming_valid(stream)  # Should not raise

    def test_collect_stream_content(self, fakeai_client):
        """Test collecting content from stream."""
        stream = fakeai_client.stream_chat("Hello!")
        content = collect_stream_content(stream)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_measure_stream_timing(self, fakeai_client):
        """Test measuring stream timing metrics."""
        stream = fakeai_client.stream_chat("Hello!")
        timing = measure_stream_timing(stream)

        assert "time_to_first_token" in timing
        assert "total_time" in timing
        assert "chunks_count" in timing
        assert "avg_inter_token_latency" in timing

        assert timing["time_to_first_token"] >= 0
        assert timing["total_time"] > 0
        assert timing["chunks_count"] > 0


class TestTemporaryServer:
    """Test temporary_server context manager."""

    def test_temporary_server_basic(self):
        """Test basic temporary server usage."""
        with temporary_server() as client:
            response = client.chat("Hello!")
            assert_response_valid(response)

    def test_temporary_server_custom_config(self):
        """Test temporary server with custom config."""
        config = AppConfig(
            response_delay=0.0,
            random_delay=False,
            enable_audio=True,
        )

        with temporary_server(config=config) as client:
            response = client.chat("Hello!")
            assert_response_valid(response)

    def test_temporary_server_multiple_requests(self):
        """Test multiple requests to temporary server."""
        with temporary_server() as client:
            # Chat
            response1 = client.chat("First request")
            assert_response_valid(response1)

            # Embeddings
            response2 = client.embed("Test text")
            assert len(response2.data) > 0

            # Models
            models = client.list_models()
            assert len(models.data) > 0


class TestRunningServerFixture:
    """Test fakeai_running_server fixture."""

    def test_running_server_fixture(self, fakeai_running_server):
        """Test using the running server fixture."""
        # Create OpenAI client from fixture
        client = OpenAI(
            api_key="test",
            base_url=fakeai_running_server["url"],
        )

        # Test request
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hello!"}],
        )

        assert response.choices[0].message.content

    def test_running_server_info(self, fakeai_running_server):
        """Test that running server fixture provides correct info."""
        assert "url" in fakeai_running_server
        assert "host" in fakeai_running_server
        assert "port" in fakeai_running_server
        assert "config" in fakeai_running_server
        assert "client" in fakeai_running_server

    def test_running_server_multiple_endpoints(self, fakeai_running_server):
        """Test multiple endpoints with running server fixture."""
        client = OpenAI(
            api_key="test",
            base_url=fakeai_running_server["url"],
        )

        # Models
        models = client.models.list()
        assert len(models.data) > 0

        # Chat
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        assert response.choices[0].message.content

        # Embeddings
        embedding = client.embeddings.create(
            model="sentence-transformers/all-mpnet-base-v2",
            input="Test",
        )
        assert len(embedding.data) > 0


class TestAdvancedFeatures:
    """Test advanced client SDK features."""

    def test_chat_with_parameters(self, fakeai_client):
        """Test chat with various parameters."""
        response = fakeai_client.chat(
            "Tell me a story",
            model="openai/gpt-oss-120b",
            system="You are a storyteller.",
            temperature=0.8,
            max_tokens=100,
            top_p=0.9,
        )
        assert_response_valid(response)

    def test_streaming_with_parameters(self, fakeai_client):
        """Test streaming with various parameters."""
        stream = fakeai_client.stream_chat(
            "Count to 10",
            model="meta-llama/Llama-3.1-8B-Instruct",
            temperature=0.5,
            max_tokens=50,
        )
        content = collect_stream_content(stream)
        assert len(content) > 0

    def test_multiple_models(self, fakeai_client):
        """Test requests with different models."""
        models = ["meta-llama/Llama-3.1-8B-Instruct", "openai/gpt-oss-120b", "openai/gpt-oss-120b"]

        for model_name in models:
            response = fakeai_client.chat("Hello!", model=model_name)
            assert_response_valid(response)
            assert response.model == model_name

    def test_batch_embeddings(self, fakeai_client):
        """Test batch embedding generation."""
        texts = [f"Text number {i}" for i in range(10)]
        response = fakeai_client.embed(texts)
        assert len(response.data) == 10

    def test_different_embedding_models(self, fakeai_client):
        """Test different embedding models."""
        models = ["sentence-transformers/all-mpnet-base-v2", "nomic-ai/nomic-embed-text-v1.5", "BAAI/bge-m3"]

        for model in models:
            response = fakeai_client.embed("Test text", model=model)
            assert len(response.data) > 0


class TestPerformance:
    """Test performance-related features."""

    def test_zero_delay_config(self):
        """Test that zero delay config works for fast tests."""
        config = AppConfig(response_delay=0.0, random_delay=False)

        with FakeAIClient(config=config, auto_start=True) as client:
            import time
            start = time.time()
            response = client.chat("Hello!")
            elapsed = time.time() - start

            assert_response_valid(response)
            # Should be very fast with zero delay
            assert elapsed < 1.0

    def test_batch_requests(self, fakeai_client):
        """Test multiple sequential requests."""
        for i in range(5):
            response = fakeai_client.chat(f"Request {i}")
            assert_response_valid(response)

    def test_streaming_timing(self, fakeai_client):
        """Test that streaming timing is measured correctly."""
        stream = fakeai_client.stream_chat("Count to 10")
        timing = measure_stream_timing(stream)

        # Should have timing data
        assert timing["time_to_first_token"] > 0
        assert timing["total_time"] > 0
        assert timing["chunks_count"] > 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_message(self, fakeai_client):
        """Test handling of empty messages."""
        # Even empty messages should work
        response = fakeai_client.chat("")
        assert_response_valid(response)

    def test_very_long_message(self, fakeai_client):
        """Test handling of very long messages."""
        long_message = "Hello " * 1000
        response = fakeai_client.chat(long_message, max_tokens=50)
        assert_response_valid(response)

    def test_special_characters(self, fakeai_client):
        """Test handling of special characters."""
        special_text = "Hello! @#$%^&*() 你好 مرحبا"
        response = fakeai_client.chat(special_text)
        assert_response_valid(response)

    def test_unicode_in_embeddings(self, fakeai_client):
        """Test unicode text in embeddings."""
        unicode_texts = ["Hello", "你好", "مرحبا", "Привет", "🔥🎉"]
        response = fakeai_client.embed(unicode_texts)
        assert len(response.data) == len(unicode_texts)


class TestContextManagers:
    """Test context manager functionality."""

    def test_context_manager_cleanup(self):
        """Test that context manager properly cleans up."""
        # Should not raise any errors
        with FakeAIClient(auto_start=True) as client:
            response = client.chat("Hello!")
            assert_response_valid(response)
        # Server should be stopped here

    def test_nested_context_managers(self):
        """Test nested context managers."""
        config1 = AppConfig(response_delay=0.0, port=8001)
        config2 = AppConfig(response_delay=0.0, port=8002)

        with FakeAIClient(config=config1, auto_start=True, port=8001) as client1:
            with FakeAIClient(config=config2, auto_start=True, port=8002) as client2:
                response1 = client1.chat("Hello from server 1")
                response2 = client2.chat("Hello from server 2")

                assert_response_valid(response1)
                assert_response_valid(response2)

    def test_temporary_server_exception_handling(self):
        """Test that temporary server cleans up even on exception."""
        try:
            with temporary_server() as client:
                response = client.chat("Hello!")
                assert_response_valid(response)
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        # Server should still be cleaned up


class TestDocumentedExamples:
    """Test all examples from documentation."""

    def test_quick_start_example(self):
        """Test quick start example from docs."""
        # Example from README
        with FakeAIClient(auto_start=True) as client:
            response = client.chat("Hello!")
            assert_response_valid(response)

    def test_streaming_example(self):
        """Test streaming example from docs."""
        with FakeAIClient(auto_start=True) as client:
            stream = client.stream_chat("Count to 5")
            content = collect_stream_content(stream)
            assert len(content) > 0

    def test_validation_example(self):
        """Test validation example from docs."""
        with FakeAIClient(auto_start=True) as client:
            response = client.chat("Hello!")
            assert_response_valid(response)
            assert_tokens_in_range(response.usage, min_prompt=1, min_completion=1)

    def test_timing_example(self):
        """Test timing measurement example from docs."""
        with FakeAIClient(auto_start=True) as client:
            stream = client.stream_chat("Hello!")
            timing = measure_stream_timing(stream)
            assert timing["time_to_first_token"] >= 0
            assert timing["chunks_count"] > 0


# Pytest configuration for this test file
@pytest.fixture(scope="module")
def module_config():
    """Shared config for all tests in this module."""
    return AppConfig(
        response_delay=0.0,
        random_delay=False,
        require_api_key=False,
    )
