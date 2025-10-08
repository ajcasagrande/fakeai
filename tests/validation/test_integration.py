"""
Integration tests for the complete validation framework.

Tests end-to-end scenarios with real-world use cases.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import BaseModel, Field

from fakeai.validation.factory import (
    create_chat_validators,
    create_validators_for_endpoint,
)


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""

    model: str = Field(description="Model ID")
    messages: list[dict] = Field(description="List of messages")
    temperature: float | None = Field(default=1.0, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    stream: bool = Field(default=False)


class TestEndToEndValidation:
    """End-to-end validation tests."""

    def test_valid_chat_request(self):
        """Test validating a complete valid chat request."""
        pipeline = create_chat_validators(
            schema=ChatCompletionRequest,
            require_auth=True,
            check_rate_limits=False,  # Disable for testing
            check_content_policy=False,
        )

        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Hello!"},
            ],
            temperature=0.7,
            max_tokens=100,
        )

        context = {
            "api_key": "test-key",
            "model": "gpt-4",
            "prompt_tokens": 10,
            "max_tokens": 100,
            "messages": request.messages,
        }

        result = pipeline.validate(request, context)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_invalid_chat_request_multiple_errors(self):
        """Test validating a chat request with multiple errors."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
            fail_fast=False,  # Collect all errors
        )

        request = {
            "model": "gpt-4",
            "temperature": 3.0,  # Invalid: > 2
            "top_p": 1.5,  # Invalid: > 1
            "frequency_penalty": 3.0,  # Invalid: > 2
        }

        result = pipeline.validate(request)

        assert result.valid is False
        assert len(result.errors) >= 3  # At least 3 parameter errors

    def test_fail_fast_stops_at_first_error(self):
        """Test fail-fast mode stops at first error."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
            fail_fast=True,
        )

        request = {
            "model": "gpt-4",
            "temperature": 3.0,  # Invalid
            "top_p": 1.5,  # Invalid
            "frequency_penalty": 3.0,  # Invalid
        }

        result = pipeline.validate(request)

        assert result.valid is False
        # Should stop at first error
        assert "failed_validator" in result.metadata

    def test_vision_request_validation(self):
        """Test validating a vision request."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image.jpg"},
                    },
                ],
            }
        ]

        context = {
            "model": "gpt-4-vision-preview",
            "messages": messages,
            "prompt_tokens": 100,
            "max_tokens": 500,
            "image_tokens": 85,
        }

        result = pipeline.validate({}, context)

        assert result.valid is True

    def test_vision_request_wrong_model(self):
        """Test vision request with non-vision model fails."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image.jpg"},
                    },
                ],
            }
        ]

        context = {
            "model": "gpt-3.5-turbo",  # Non-vision model
            "messages": messages,
            "prompt_tokens": 100,
        }

        result = pipeline.validate({}, context)

        assert result.valid is False
        assert any("vision" in err.message.lower() for err in result.errors)

    def test_context_length_exceeded(self):
        """Test context length validation fails when exceeded."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
        )

        context = {
            "model": "gpt-4",
            "prompt_tokens": 7000,
            "max_tokens": 2000,  # Total: 9000 > 8192
        }

        result = pipeline.validate({}, context)

        assert result.valid is False
        assert any("context" in err.message.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation pipeline."""
        pipeline = create_chat_validators(
            require_auth=True,
            check_rate_limits=False,
        )

        request = {
            "model": "gpt-4",
            "temperature": 0.7,
        }

        context = {
            "api_key": "test-key",
            "model": "gpt-4",
            "prompt_tokens": 100,
        }

        result = await pipeline.validate_async(request, context)

        assert result.valid is True


class TestMultipleEndpoints:
    """Test validation across multiple endpoints."""

    def test_chat_vs_embedding_pipelines(self):
        """Test different pipelines for different endpoints."""
        chat_pipeline = create_validators_for_endpoint("chat")
        embedding_pipeline = create_validators_for_endpoint("embedding")

        # Chat pipeline should have more validators
        assert len(chat_pipeline) > len(embedding_pipeline)

        # Both should have model availability
        chat_validators = [v.name for v in chat_pipeline._validators]
        embedding_validators = [v.name for v in embedding_pipeline._validators]

        assert any("Model" in v for v in chat_validators)
        assert any("Model" in v for v in embedding_validators)

    def test_all_endpoints_create_successfully(self):
        """Test all endpoint validators can be created."""
        endpoints = [
            "chat",
            "completion",
            "embedding",
            "image",
            "audio",
            "moderation",
            "batch",
        ]

        for endpoint in endpoints:
            pipeline = create_validators_for_endpoint(endpoint)
            assert pipeline is not None
            assert len(pipeline) > 0


class TestWarningsAndErrors:
    """Test handling of warnings and errors together."""

    def test_warnings_with_valid_request(self):
        """Test warnings don't fail validation."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
        )

        request = {
            "model": "gpt-4",
            "temperature": 1.8,  # High but valid - should warn
            "max_tokens": 150000,  # Very high - should warn
        }

        context = {
            "model": "gpt-4",
            "prompt_tokens": 100,
        }

        result = pipeline.validate(request, context)

        assert result.valid is True  # Still valid
        assert len(result.warnings) > 0  # But has warnings

    def test_errors_and_warnings_together(self):
        """Test getting both errors and warnings."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
            fail_fast=False,
        )

        request = {
            "model": "gpt-4",
            "temperature": 3.0,  # Invalid - error
            "max_tokens": 150000,  # High but valid - warning
            "n": 15,  # High but valid - warning
        }

        result = pipeline.validate(request)

        assert result.valid is False  # Has errors
        assert len(result.errors) > 0
        assert len(result.warnings) > 0  # Also has warnings


class TestContentPolicy:
    """Test content policy validation."""

    def test_clean_content_passes(self):
        """Test clean content passes policy check."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
            check_content_policy=True,
        )

        messages = [
            {"role": "user", "content": "Tell me about machine learning."},
        ]

        context = {
            "model": "gpt-4",
            "messages": messages,
            "prompt_tokens": 10,
        }

        result = pipeline.validate({}, context)

        assert result.valid is True
        assert len(result.warnings) == 0

    def test_flagged_content_warning(self):
        """Test flagged content generates warning."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
            check_content_policy=True,
        )

        messages = [
            {"role": "user", "content": "How to hack a system?"},
        ]

        context = {
            "model": "gpt-4",
            "messages": messages,
            "prompt_tokens": 10,
        }

        result = pipeline.validate({}, context)

        # Non-strict mode: warning but valid
        assert result.valid is True
        assert len(result.warnings) > 0


class TestFineTunedModels:
    """Test validation with fine-tuned models."""

    def test_fine_tuned_model_validation(self):
        """Test fine-tuned model format is validated."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
        )

        context = {
            "model": "ft:gpt-4:my-org::abc123",
            "prompt_tokens": 100,
        }

        result = pipeline.validate({}, context)

        assert result.valid is True

    def test_fine_tuned_model_context_window(self):
        """Test fine-tuned models inherit base model context window."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
        )

        context = {
            "model": "ft:gpt-4:my-org::abc123",
            "prompt_tokens": 7000,
            "max_tokens": 2000,  # Should fail for gpt-4 (8192 limit)
        }

        result = pipeline.validate({}, context)

        assert result.valid is False


class TestErrorResponses:
    """Test error response formatting."""

    def test_error_response_format(self):
        """Test error responses are properly formatted."""
        pipeline = create_chat_validators(
            require_auth=True,
            check_rate_limits=False,
        )

        result = pipeline.validate(request={}, context={})

        assert result.valid is False

        error_response = result.to_error_response()

        assert "error" in error_response
        assert "message" in error_response["error"]
        assert "type" in error_response["error"]
        assert error_response["error"]["type"] == "invalid_request_error"

    def test_multiple_errors_in_response(self):
        """Test multiple errors in error response."""
        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
            fail_fast=False,
        )

        request = {
            "temperature": 3.0,
            "top_p": 1.5,
            "frequency_penalty": 3.0,
        }

        result = pipeline.validate(request)

        error_response = result.to_error_response()

        # Should have main error and additional errors
        if len(result.errors) > 1:
            assert "additional_errors" in error_response["error"]


class TestPerformance:
    """Test validation performance."""

    def test_validation_is_fast(self):
        """Test validation completes quickly."""
        import time

        pipeline = create_chat_validators(
            require_auth=False,
            check_rate_limits=False,
        )

        request = {
            "model": "gpt-4",
            "temperature": 0.7,
        }

        context = {
            "model": "gpt-4",
            "prompt_tokens": 100,
        }

        # Run validation 100 times and measure
        start = time.time()
        for _ in range(100):
            result = pipeline.validate(request, context)
        elapsed = time.time() - start

        # Should complete 100 validations in under 1 second
        assert elapsed < 1.0
        assert result.valid is True
