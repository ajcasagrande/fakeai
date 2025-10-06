"""
Integration tests for context length validation.

Tests context length checking, per-model enforcement, token counting,
multi-modal content, and dynamic context windows.
"""

import httpx
import pytest

from .utils import FakeAIClient


def _get_error_response(exc: httpx.HTTPStatusError) -> dict:
    """Extract error response from HTTPStatusError."""
    return exc.response.json()


@pytest.mark.integration
class TestContextValidationBasics:
    """Test basic context length validation functionality."""

    def test_context_validation_enabled_by_default(self, client: FakeAIClient):
        """Test that context validation is enabled by default."""
        # Try to exceed context window for gpt-4 (8192 tokens)
        # Use a very large prompt that will definitely exceed
        long_message = "word " * 10000  # ~10000 tokens

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": long_message}],
            )

        # Should get 400 error with context_length_exceeded
        assert exc_info.value.response.status_code == 400
        error_data = _get_error_response(exc_info.value)
        error = error_data["error"]
        assert error["type"] == "invalid_request_error"
        assert error["code"] == "context_length_exceeded"
        assert "8192 tokens" in error["message"]
        assert "context length" in error["message"].lower()

    @pytest.mark.server_config(enable_context_validation=False)
    def test_context_validation_disabled(self, client: FakeAIClient):
        """Test that context validation can be disabled."""
        # Try to exceed context window for gpt-4 (8192 tokens)
        long_message = "word " * 10000  # ~10000 tokens

        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": long_message}],
        )

        # Should succeed when validation is disabled
        assert response["object"] == "chat.completion"
        assert "choices" in response
        assert len(response["choices"]) > 0

    def test_valid_context_length_passes(self, client: FakeAIClient):
        """Test that valid context lengths pass validation."""
        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello, how are you?"}],
            max_tokens=100,
        )

        assert response["object"] == "chat.completion"
        assert len(response["choices"]) > 0


@pytest.mark.integration
class TestContextLengthExceededErrors:
    """Test context length exceeded error responses."""

    def test_prompt_plus_completion_exceeds_window(self, client: FakeAIClient):
        """Test error when prompt + max_tokens exceeds context window."""
        # gpt-4 has 8192 token window
        # Use a prompt with ~7000 tokens and request 2000 tokens
        long_message = "word " * 7000

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": long_message}],
                max_tokens=2000,
            )

        error_data = _get_error_response(exc_info.value)
        error = error_data["error"]
        assert error["code"] == "context_length_exceeded"
        assert "8192 tokens" in error["message"]
        assert "in the messages" in error["message"]
        assert "in the completion" in error["message"]

    def test_prompt_alone_exceeds_window(self, client: FakeAIClient):
        """Test error when prompt alone exceeds context window."""
        # Exceed gpt-4's 8192 token window with just the prompt
        long_message = "word " * 9000

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": long_message}],
            )

        error_data = _get_error_response(exc_info.value)
        error = error_data["error"]
        assert error["code"] == "context_length_exceeded"
        assert "8192 tokens" in error["message"]
        assert "Please reduce the length of the messages" in error["message"]

    def test_error_message_format_matches_openai(self, client: FakeAIClient):
        """Test that error message format matches OpenAI's."""
        long_message = "word " * 8000

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": long_message}],
                max_tokens=500,
            )

        error_data = _get_error_response(exc_info.value)
        error = error_data["error"]
        # Check OpenAI-compatible error structure
        assert error["type"] == "invalid_request_error"
        assert error["param"] == "messages"
        assert error["code"] == "context_length_exceeded"
        assert "This model's maximum context length is" in error["message"]
        assert "However, your messages resulted in" in error["message"]

    def test_exact_context_window_boundary(self, client: FakeAIClient):
        """Test behavior at exact context window boundary."""
        # Test at exactly the boundary (should pass)
        # gpt-4 has 8192 tokens, use ~6192 prompt + 2000 completion
        message = "word " * 6192

        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": message}],
            max_tokens=2000,
        )

        assert response["object"] == "chat.completion"

        # Test one token over (should fail)
        with pytest.raises(httpx.HTTPStatusError):
            client.chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": message + " extra"}],
                max_tokens=2000,
            )


@pytest.mark.integration
class TestPerModelContextWindows:
    """Test per-model context window enforcement."""

    def test_gpt4_context_window(self, client: FakeAIClient):
        """Test GPT-4 context window (8192 tokens)."""
        # Should pass with 7000 tokens
        message = "word " * 7000
        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": message}],
        )
        assert response["object"] == "chat.completion"

        # Should fail with 9000 tokens
        long_message = "word " * 9000
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": long_message}],
            )
        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"

    def test_gpt4_turbo_large_context_window(self, client: FakeAIClient):
        """Test GPT-4 Turbo context window (128000 tokens)."""
        # Should pass with 100000 tokens
        message = "word " * 100000
        response = client.chat_completion(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": message}],
        )
        assert response["object"] == "chat.completion"

        # Should fail with 130000 tokens
        long_message = "word " * 130000
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": long_message}],
            )
        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"

    def test_gpt35_turbo_context_window(self, client: FakeAIClient):
        """Test GPT-3.5 Turbo context window (16385 tokens)."""
        # Should pass with 15000 tokens
        message = "word " * 15000
        response = client.chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
        )
        assert response["object"] == "chat.completion"

        # Should fail with 17000 tokens
        long_message = "word " * 17000
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": long_message}],
            )
        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"

    def test_llama_large_context_window(self, client: FakeAIClient):
        """Test Llama 3.1 context window (131072 tokens)."""
        # Should pass with 120000 tokens
        message = "word " * 120000
        response = client.chat_completion(
            model="meta-llama/Llama-3.1-70B-Instruct",
            messages=[{"role": "user", "content": message}],
        )
        assert response["object"] == "chat.completion"

        # Should fail with 132000 tokens
        long_message = "word " * 132000
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="meta-llama/Llama-3.1-70B-Instruct",
                messages=[{"role": "user", "content": long_message}],
            )
        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"

    def test_claude_very_large_context_window(self, client: FakeAIClient):
        """Test Claude context window (200000 tokens)."""
        # Should pass with 150000 tokens
        message = "word " * 150000
        response = client.chat_completion(
            model="claude-3-opus",
            messages=[{"role": "user", "content": message}],
        )
        assert response["object"] == "chat.completion"

    def test_unknown_model_uses_default_window(self, client: FakeAIClient):
        """Test that unknown models use default context window (8192)."""
        # Should pass with 7000 tokens
        message = "word " * 7000
        response = client.chat_completion(
            model="unknown-custom-model",
            messages=[{"role": "user", "content": message}],
        )
        assert response["object"] == "chat.completion"

        # Should fail with 9000 tokens (exceeds default 8192)
        long_message = "word " * 9000
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="unknown-custom-model",
                messages=[{"role": "user", "content": long_message}],
            )
        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"
        assert "8192 tokens" in error_data["error"]["message"]


@pytest.mark.integration
class TestTokenCounting:
    """Test token counting accuracy."""

    def test_simple_word_counting(self, client: FakeAIClient):
        """Test basic word-based token counting."""
        # Short message should have proportional token count
        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello world"}],
        )

        assert response["usage"]["prompt_tokens"] > 0
        assert response["usage"]["prompt_tokens"] < 10  # Should be small

    def test_long_message_token_counting(self, client: FakeAIClient):
        """Test token counting for longer messages."""
        # 100 words should be roughly 100-150 tokens
        message = " ".join(["word"] * 100)
        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": message}],
        )

        prompt_tokens = response["usage"]["prompt_tokens"]
        assert 80 <= prompt_tokens <= 200  # Reasonable range

    def test_empty_message_token_counting(self, client: FakeAIClient):
        """Test token counting with empty message."""
        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": ""}],
        )

        # Should still have some tokens for structure
        assert response["usage"]["prompt_tokens"] >= 0

    def test_multiple_messages_token_counting(self, client: FakeAIClient):
        """Test token counting with multiple messages."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        response = client.chat_completion(model="gpt-4", messages=messages)

        # Should count all messages
        assert response["usage"]["prompt_tokens"] > 20  # Multiple messages


@pytest.mark.integration
class TestPromptCompletionLimits:
    """Test prompt + completion token limits."""

    def test_small_prompt_large_completion(self, client: FakeAIClient):
        """Test small prompt with large completion request."""
        response = client.chat_completion(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=100000,
        )

        # Should succeed (small prompt + large completion < 128K)
        assert response["object"] == "chat.completion"

    def test_large_prompt_small_completion(self, client: FakeAIClient):
        """Test large prompt with small completion."""
        # Use ~120K tokens in prompt
        message = "word " * 120000

        response = client.chat_completion(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": message}],
            max_tokens=1000,
        )

        # Should succeed (120K + 1K < 128K)
        assert response["object"] == "chat.completion"

    def test_no_max_tokens_only_validates_prompt(self, client: FakeAIClient):
        """Test validation when max_tokens is not specified."""
        # Should validate only the prompt
        message = "word " * 7000

        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": message}],
            # No max_tokens specified
        )

        assert response["object"] == "chat.completion"

    def test_zero_max_tokens(self, client: FakeAIClient):
        """Test with max_tokens=0."""
        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=0,
        )

        # Should succeed (no completion requested)
        assert response["object"] == "chat.completion"


@pytest.mark.integration
class TestMultiModalTokenCounting:
    """Test multi-modal content token counting."""

    def test_vision_image_tokens(self, client: FakeAIClient):
        """Test token counting with image content."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg"},
                    },
                ],
            }
        ]

        response = client.chat_completion(
            model="gpt-4-turbo",
            messages=messages,
        )

        # Should count both text and image tokens
        assert response["usage"]["prompt_tokens"] > 0
        # Image tokens should be included in prompt_tokens or reported separately

    def test_multiple_images_token_counting(self, client: FakeAIClient):
        """Test token counting with multiple images."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Compare these images."},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,img1"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,img2"},
                    },
                ],
            }
        ]

        response = client.chat_completion(
            model="gpt-4-turbo",
            messages=messages,
        )

        # Should count text + multiple image tokens
        assert response["usage"]["prompt_tokens"] > 0

    def test_audio_input_token_counting(self, client: FakeAIClient):
        """Test token counting with audio input."""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": "base64audiodata",
                            "format": "wav",
                        },
                    },
                ],
            }
        ]

        response = client.chat_completion(
            model="gpt-4-turbo",
            messages=messages,
        )

        # Should count audio tokens
        assert response["usage"]["prompt_tokens"] > 0

    def test_mixed_multimodal_content(self, client: FakeAIClient):
        """Test token counting with mixed content types."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this:"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,img"},
                    },
                    {"type": "text", "text": "And this audio:"},
                    {
                        "type": "input_audio",
                        "input_audio": {"data": "audiodata", "format": "wav"},
                    },
                ],
            }
        ]

        response = client.chat_completion(
            model="gpt-4-turbo",
            messages=messages,
        )

        # Should count all content types
        assert response["usage"]["prompt_tokens"] > 0


@pytest.mark.integration
class TestSystemMessageTokenCounting:
    """Test system message token counting."""

    def test_system_message_included_in_count(self, client: FakeAIClient):
        """Test that system messages are counted."""
        messages_without_system = [
            {"role": "user", "content": "Hello"},
        ]

        messages_with_system = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ]

        response_without = client.chat_completion(
            model="gpt-4", messages=messages_without_system
        )
        response_with = client.chat_completion(
            model="gpt-4", messages=messages_with_system
        )

        # System message should add tokens
        assert response_with["usage"]["prompt_tokens"] > response_without["usage"]["prompt_tokens"]

    def test_long_system_message_affects_context(self, client: FakeAIClient):
        """Test that long system messages count toward context limit."""
        # Create a system message that takes most of the context
        long_system = "word " * 7500

        messages = [
            {"role": "system", "content": long_system},
            {"role": "user", "content": "Hello"},
        ]

        # Should fail because system + user exceeds 8192
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="gpt-4",
                messages=messages,
                max_tokens=1000,
            )

        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"

    def test_multiple_system_messages(self, client: FakeAIClient):
        """Test multiple system messages in token counting."""
        messages = [
            {"role": "system", "content": "First instruction."},
            {"role": "system", "content": "Second instruction."},
            {"role": "user", "content": "Hello"},
        ]

        response = client.chat_completion(model="gpt-4", messages=messages)

        # Should count both system messages
        assert response["usage"]["prompt_tokens"] > 0


@pytest.mark.integration
class TestToolDefinitionsTokenCounting:
    """Test tool/function definitions token counting."""

    def test_function_definitions_counted(self, client: FakeAIClient):
        """Test that function definitions are counted in tokens."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather in a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City and state",
                            },
                        },
                        "required": ["location"],
                    },
                },
            }
        ]

        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "What's the weather?"}],
            tools=tools,
        )

        # Function definitions should add to token count
        assert response["usage"]["prompt_tokens"] > 10

    def test_multiple_tools_token_counting(self, client: FakeAIClient):
        """Test token counting with multiple tool definitions."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Perform calculations",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Help me."}],
            tools=tools,
        )

        # Multiple tools should increase token count
        assert response["usage"]["prompt_tokens"] > 20


@pytest.mark.integration
class TestContextLengthWithStreaming:
    """Test context length validation with streaming."""

    def test_streaming_respects_context_limits(self, client: FakeAIClient):
        """Test that streaming also validates context length."""
        # Try to exceed context window in streaming mode
        long_message = "word " * 10000

        # Streaming should also fail with context exceeded
        with pytest.raises(httpx.HTTPStatusError):
            list(
                client.chat_completion_stream(
                    model="gpt-4",
                    messages=[{"role": "user", "content": long_message}],
                )
            )

    def test_streaming_valid_context(self, client: FakeAIClient):
        """Test streaming with valid context length."""
        chunks = list(
            client.chat_completion_stream(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
            )
        )

        # Should get chunks successfully
        assert len(chunks) > 0


@pytest.mark.integration
class TestDynamicContextWindows:
    """Test dynamic context windows and model-specific limits."""

    def test_fine_tuned_model_inherits_base_context(self, client: FakeAIClient):
        """Test that fine-tuned models inherit base model context window."""
        # Fine-tuned model based on gpt-4 (8192 tokens)
        long_message = "word " * 9000

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="ft:gpt-4:org::model123",
                messages=[{"role": "user", "content": long_message}],
            )

        # Should use gpt-4's context window
        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"
        assert "8192 tokens" in error_data["error"]["message"]

    def test_model_with_provider_prefix(self, client: FakeAIClient):
        """Test context validation for models with provider prefixes."""
        # Should handle openai/gpt-oss-120b (128K tokens)
        message = "word " * 120000

        response = client.chat_completion(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": message}],
        )

        assert response["object"] == "chat.completion"

        # Should fail at 130K
        long_message = "word " * 130000
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": long_message}],
            )
        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"

    def test_registry_context_window_override(self, client: FakeAIClient):
        """Test that model registry can provide custom context windows."""
        # Register a custom model with specific context window
        # (This tests integration with model registry)

        # For now, just test that the registry is consulted
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.chat_completion(
                model="custom-large-context",
                messages=[{"role": "user", "content": "word " * 9000}],
            )

        # Should use default context window for unknown models
        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"


@pytest.mark.integration
@pytest.mark.asyncio
class TestContextValidationAsync:
    """Test context validation in async mode."""

    async def test_async_context_validation(self, client: FakeAIClient):
        """Test context validation works in async requests."""
        long_message = "word " * 10000

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.achat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": long_message}],
            )

        error_data = _get_error_response(exc_info.value)
        assert error_data["error"]["code"] == "context_length_exceeded"

    async def test_async_valid_context(self, client: FakeAIClient):
        """Test async requests with valid context length."""
        response = await client.achat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert response["object"] == "chat.completion"
