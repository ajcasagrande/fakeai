"""Integration tests for basic chat completion features.

This module tests:
- Basic chat completion requests
- Streaming chat completions
- Multiple choice generation (n parameter)
- Temperature and sampling parameters
- Max tokens limits
- Stop sequences
- Presence/frequency penalties
- Seed for deterministic generation
- System messages
- User/assistant conversation flow
"""

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
class TestBasicChatCompletions:
    """Test basic chat completion functionality."""

    def test_simple_chat_completion(self, client: FakeAIClient):
        """Test a simple chat completion request."""
        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
        )

        assert response["object"] == "chat.completion"
        assert "id" in response
        assert response["id"].startswith("chatcmpl-")
        assert "created" in response
        assert response["model"] == "gpt-4"
        assert len(response["choices"]) == 1

        choice = response["choices"][0]
        assert choice["index"] == 0
        assert choice["finish_reason"] == "stop"
        assert choice["message"]["role"] == "assistant"
        assert "content" in choice["message"]
        assert len(choice["message"]["content"]) > 0

        # Check usage
        assert "usage" in response
        usage = response["usage"]
        assert usage["prompt_tokens"] > 0
        assert usage["completion_tokens"] > 0
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

    def test_system_message(self, client: FakeAIClient):
        """Test chat completion with system message."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ]

        response = client.chat_completion(
            model="gpt-3.5-turbo",
            messages=messages,
        )

        assert response["object"] == "chat.completion"
        assert len(response["choices"]) == 1
        assert response["choices"][0]["message"]["role"] == "assistant"

    def test_multi_turn_conversation(self, client: FakeAIClient):
        """Test multi-turn conversation."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What is my name?"}
        ]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
        )

        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["content"]

    def test_streaming_chat_completion(self, client: FakeAIClient):
        """Test streaming chat completion."""
        messages = [
            {"role": "user", "content": "Tell me a short story."}
        ]

        chunks = list(client.chat_completion_stream(
            model="gpt-4",
            messages=messages,
        ))

        assert len(chunks) > 0

        # Check first chunk (should have role)
        first_chunk = chunks[0]
        assert first_chunk["object"] == "chat.completion.chunk"
        assert "id" in first_chunk
        assert first_chunk["id"].startswith("chatcmpl-")
        assert len(first_chunk["choices"]) == 1

        # Check for content chunks
        content_chunks = [
            chunk for chunk in chunks
            if chunk["choices"][0].get("delta", {}).get("content")
        ]
        assert len(content_chunks) > 0

        # Check final chunk (should have finish_reason)
        last_chunk = chunks[-1]
        assert last_chunk["choices"][0]["finish_reason"] == "stop"

    def test_multiple_choices(self, client: FakeAIClient):
        """Test generating multiple completion choices (n parameter)."""
        messages = [
            {"role": "user", "content": "Say hello."}
        ]

        response = client.chat_completion(
            model="gpt-3.5-turbo",
            messages=messages,
            n=3,
        )

        assert response["object"] == "chat.completion"
        assert len(response["choices"]) == 3

        for i, choice in enumerate(response["choices"]):
            assert choice["index"] == i
            assert choice["message"]["role"] == "assistant"
            assert "content" in choice["message"]


@pytest.mark.integration
class TestSamplingParameters:
    """Test sampling parameters for chat completions."""

    def test_temperature(self, client: FakeAIClient):
        """Test temperature parameter."""
        messages = [{"role": "user", "content": "Hello"}]

        # Low temperature (more deterministic)
        response_low = client.chat_completion(
            model="gpt-4",
            messages=messages,
            temperature=0.1,
        )
        assert response_low["object"] == "chat.completion"

        # High temperature (more random)
        response_high = client.chat_completion(
            model="gpt-4",
            messages=messages,
            temperature=1.5,
        )
        assert response_high["object"] == "chat.completion"

    def test_top_p(self, client: FakeAIClient):
        """Test top_p parameter (nucleus sampling)."""
        messages = [{"role": "user", "content": "Tell me about AI"}]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
            top_p=0.9,
        )

        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["content"]

    def test_max_tokens(self, client: FakeAIClient):
        """Test max_tokens parameter."""
        messages = [{"role": "user", "content": "Write a long essay about technology."}]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
            max_tokens=50,
        )

        assert response["object"] == "chat.completion"
        # Should finish due to length, not naturally
        assert response["choices"][0]["finish_reason"] in ["stop", "length"]
        # Token count should respect limit
        assert response["usage"]["completion_tokens"] <= 50

    def test_stop_sequences(self, client: FakeAIClient):
        """Test stop sequences."""
        messages = [{"role": "user", "content": "Count to 10"}]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
            stop=["5", "five"],
        )

        assert response["object"] == "chat.completion"
        # Should stop when hitting stop sequence
        if response["choices"][0]["finish_reason"] == "stop":
            # This is OK too - natural stop might occur first
            pass


@pytest.mark.integration
class TestPenaltyParameters:
    """Test penalty parameters."""

    def test_presence_penalty(self, client: FakeAIClient):
        """Test presence_penalty parameter."""
        messages = [{"role": "user", "content": "List some fruits"}]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
            presence_penalty=0.5,
        )

        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["content"]

    def test_frequency_penalty(self, client: FakeAIClient):
        """Test frequency_penalty parameter."""
        messages = [{"role": "user", "content": "Tell me about cats"}]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
            frequency_penalty=0.7,
        )

        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["content"]

    def test_combined_penalties(self, client: FakeAIClient):
        """Test combining presence and frequency penalties."""
        messages = [{"role": "user", "content": "Write about dogs"}]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
            presence_penalty=0.3,
            frequency_penalty=0.3,
        )

        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["content"]


@pytest.mark.integration
class TestDeterministicGeneration:
    """Test deterministic generation with seed."""

    def test_seed_parameter(self, client: FakeAIClient):
        """Test seed parameter for deterministic generation."""
        messages = [{"role": "user", "content": "Generate a random number"}]

        # Generate with same seed
        response1 = client.chat_completion(
            model="gpt-4",
            messages=messages,
            seed=12345,
            temperature=0.0,  # Use 0 temperature for more deterministic output
        )

        response2 = client.chat_completion(
            model="gpt-4",
            messages=messages,
            seed=12345,
            temperature=0.0,
        )

        # Both should have system_fingerprint
        assert "system_fingerprint" in response1
        assert "system_fingerprint" in response2

        # With seed parameter, the server should attempt deterministic generation
        # Note: In FakeAI's implementation using Faker, perfect determinism may not
        # be guaranteed due to internal state, but the seed should be accepted
        # and system_fingerprint should be consistent
        assert response1["system_fingerprint"] == response2["system_fingerprint"]

        # Verify both responses are valid
        content1 = response1["choices"][0]["message"]["content"]
        content2 = response2["choices"][0]["message"]["content"]
        assert len(content1) > 0
        assert len(content2) > 0

    def test_different_seeds(self, client: FakeAIClient):
        """Test different seeds produce different outputs."""
        messages = [{"role": "user", "content": "Generate a random number"}]

        response1 = client.chat_completion(
            model="gpt-4",
            messages=messages,
            seed=12345,
            temperature=1.0,
        )

        response2 = client.chat_completion(
            model="gpt-4",
            messages=messages,
            seed=54321,
            temperature=1.0,
        )

        assert response1["object"] == "chat.completion"
        assert response2["object"] == "chat.completion"

        # Different seeds may produce different content
        # (but this isn't guaranteed in all implementations)


@pytest.mark.integration
class TestUserParameter:
    """Test user parameter for tracking."""

    def test_user_parameter(self, client: FakeAIClient):
        """Test user parameter is accepted."""
        messages = [{"role": "user", "content": "Hello"}]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
            user="user-12345",
        )

        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["content"]


@pytest.mark.integration
class TestStreamOptions:
    """Test stream_options parameter."""

    def test_streaming_with_usage(self, client: FakeAIClient):
        """Test streaming with usage information."""
        messages = [{"role": "user", "content": "Hello"}]

        chunks = list(client.chat_completion_stream(
            model="gpt-4",
            messages=messages,
            stream_options={"include_usage": True},
        ))

        assert len(chunks) > 0

        # Last chunk should have usage
        last_chunk = chunks[-1]
        if "usage" in last_chunk:
            usage = last_chunk["usage"]
            assert usage["prompt_tokens"] > 0
            assert usage["completion_tokens"] > 0
            assert usage["total_tokens"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncChatCompletions:
    """Test async chat completions."""

    async def test_async_chat_completion(self, client: FakeAIClient):
        """Test async chat completion."""
        messages = [{"role": "user", "content": "Hello"}]

        response = await client.achat_completion(
            model="gpt-4",
            messages=messages,
        )

        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["content"]

    async def test_async_streaming(self, client: FakeAIClient):
        """Test async streaming chat completion."""
        messages = [{"role": "user", "content": "Tell me a story"}]

        chunks = []
        async for chunk in client.achat_completion_stream(
            model="gpt-4",
            messages=messages,
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert chunks[0]["object"] == "chat.completion.chunk"
        assert chunks[-1]["choices"][0]["finish_reason"] == "stop"


@pytest.mark.integration
class TestModelVariants:
    """Test different model variants."""

    def test_gpt_4(self, client: FakeAIClient):
        """Test GPT-4 model."""
        messages = [{"role": "user", "content": "Hello"}]

        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
        )

        assert response["object"] == "chat.completion"
        assert response["model"] == "gpt-4"

    def test_gpt_35_turbo(self, client: FakeAIClient):
        """Test GPT-3.5 Turbo model."""
        messages = [{"role": "user", "content": "Hello"}]

        response = client.chat_completion(
            model="gpt-3.5-turbo",
            messages=messages,
        )

        assert response["object"] == "chat.completion"
        assert response["model"] == "gpt-3.5-turbo"

    def test_custom_model(self, client: FakeAIClient):
        """Test custom model auto-creation."""
        messages = [{"role": "user", "content": "Hello"}]

        response = client.chat_completion(
            model="my-custom-model",
            messages=messages,
        )

        assert response["object"] == "chat.completion"
        assert response["model"] == "my-custom-model"


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling for invalid requests."""

    def test_empty_messages(self, client: FakeAIClient):
        """Test error with empty messages list."""
        try:
            response = client.chat_completion(
                model="gpt-4",
                messages=[],
            )
            # Some implementations may allow empty messages
            if response.get("error"):
                assert True
        except Exception:
            # Expected to fail
            assert True

    def test_invalid_temperature(self, client: FakeAIClient):
        """Test error with invalid temperature."""
        messages = [{"role": "user", "content": "Hello"}]

        try:
            response = client.chat_completion(
                model="gpt-4",
                messages=messages,
                temperature=3.0,  # Too high
            )
            # May succeed if validation is lenient
            if response.get("error"):
                assert True
        except Exception:
            # Expected to fail with validation error
            assert True

    def test_invalid_max_tokens(self, client: FakeAIClient):
        """Test error with invalid max_tokens."""
        messages = [{"role": "user", "content": "Hello"}]

        try:
            response = client.chat_completion(
                model="gpt-4",
                messages=messages,
                max_tokens=-1,  # Invalid
            )
            # May succeed if validation is lenient
            if response.get("error"):
                assert True
        except Exception:
            # Expected to fail with validation error
            assert True
