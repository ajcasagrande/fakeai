"""
Tests for max_completion_tokens parameter handling.

Validates that both max_tokens and max_completion_tokens are respected,
and that max_completion_tokens takes precedence when both are provided.
"""

import pytest

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role


class TestMaxCompletionTokens:
    """Test max_completion_tokens parameter."""

    @pytest.mark.asyncio
    async def test_max_tokens_respected(self):
        """Test that max_tokens limits response length."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            max_tokens=50,
        )

        response = await service.create_chat_completion(request)

        # Response should be limited by max_tokens
        assert (
            response.usage.completion_tokens <= 50
        ), f"Completion tokens {response.usage.completion_tokens} should be <= 50"

    @pytest.mark.asyncio
    async def test_max_completion_tokens_respected(self):
        """Test that max_completion_tokens limits response length."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="deepseek-ai/DeepSeek-R1",
            messages=[Message(role=Role.USER, content="Test")],
            max_completion_tokens=30,
        )

        response = await service.create_chat_completion(request)

        # Response should be limited by max_completion_tokens
        assert (
            response.usage.completion_tokens <= 30
        ), f"Completion tokens {response.usage.completion_tokens} should be <= 30"

    @pytest.mark.asyncio
    async def test_max_completion_tokens_takes_precedence(self):
        """Test that max_completion_tokens overrides max_tokens when both provided."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="deepseek-ai/DeepSeek-R1",
            messages=[Message(role=Role.USER, content="Test")],
            max_tokens=100,
            max_completion_tokens=25,  # Should use this one
        )

        response = await service.create_chat_completion(request)

        # Should respect max_completion_tokens (25), not max_tokens (100)
        assert (
            response.usage.completion_tokens <= 25
        ), f"Completion tokens {response.usage.completion_tokens} should respect max_completion_tokens=25"

    @pytest.mark.asyncio
    async def test_default_when_neither_provided(self):
        """Test default of 100 tokens when neither parameter provided."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
        )

        response = await service.create_chat_completion(request)

        # Should use default of 100
        assert response.usage.completion_tokens <= 100

    @pytest.mark.asyncio
    async def test_streaming_respects_max_completion_tokens(self):
        """Test streaming also respects max_completion_tokens."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="deepseek-ai/DeepSeek-R1",
            messages=[Message(role=Role.USER, content="Test")],
            max_completion_tokens=20,
            stream=True,
        )

        token_count = 0
        async for chunk in service.create_chat_completion_stream(request):
            if chunk.choices and chunk.choices[0].delta.content:
                # Count tokens in stream
                token_count += 1

        # Should not exceed max_completion_tokens
        assert token_count <= 20, f"Streamed {token_count} tokens, should be <= 20"

    @pytest.mark.asyncio
    async def test_finish_reason_length_when_limit_hit(self):
        """Test finish_reason is 'length' when token limit hit."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Set very low limit to ensure it's hit
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Generate long text")],
            max_completion_tokens=5,
        )

        response = await service.create_chat_completion(request)

        # Finish reason should be "length" if limit was reached
        if response.usage.completion_tokens >= 5:
            assert (
                response.choices[0].finish_reason == "length"
            ), "Finish reason should be 'length' when token limit hit"

    def test_get_effective_max_tokens_helper(self):
        """Test the helper function directly."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Test max_completion_tokens takes precedence
        class MockRequest:
            max_tokens = 100
            max_completion_tokens = 50

        assert service._get_effective_max_tokens(MockRequest()) == 50

        # Test max_tokens when max_completion_tokens is None
        class MockRequest2:
            max_tokens = 75
            max_completion_tokens = None

        assert service._get_effective_max_tokens(MockRequest2()) == 75

        # Test default when both are None
        class MockRequest3:
            max_tokens = None
            max_completion_tokens = None

        assert service._get_effective_max_tokens(MockRequest3()) == 100

    @pytest.mark.asyncio
    async def test_large_max_completion_tokens(self):
        """Test with very large max_completion_tokens value."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="deepseek-ai/DeepSeek-R1",
            messages=[Message(role=Role.USER, content="Test")],
            max_completion_tokens=10000,  # Very large
        )

        response = await service.create_chat_completion(request)

        # Should generate up to the limit (or stop naturally)
        assert response.usage.completion_tokens > 0
        assert response.usage.completion_tokens <= 10000
        # Finish reason should be "stop" (not hitting limit)
        assert response.choices[0].finish_reason == "stop"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
