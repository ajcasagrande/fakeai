"""
Tests for individual validators.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import BaseModel, Field

from fakeai.rate_limiter import RateLimiter
from fakeai.validation.validators.auth import AuthValidator
from fakeai.validation.validators.content_policy import ContentPolicyValidator
from fakeai.validation.validators.context_length import ContextLengthValidator
from fakeai.validation.validators.model_availability import ModelAvailabilityValidator
from fakeai.validation.validators.multimodal import MultiModalValidator
from fakeai.validation.validators.parameters import ParameterValidator
from fakeai.validation.validators.rate_limit import RateLimitValidator
from fakeai.validation.validators.schema import SchemaValidator


# Test schema for SchemaValidator tests
class TestRequestSchema(BaseModel):
    """Test request schema."""

    model: str = Field(description="Model ID")
    temperature: float = Field(default=1.0, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)


class TestSchemaValidator:
    """Tests for SchemaValidator."""

    def test_valid_request_dict(self):
        """Test validating a valid request dict."""
        validator = SchemaValidator(schema=TestRequestSchema)

        request = {"model": "gpt-4", "temperature": 0.7, "max_tokens": 100}
        result = validator.validate(request)

        assert result.valid is True
        assert "validated_model" in result.metadata
        assert result.metadata["schema"] == "TestRequestSchema"

    def test_valid_request_model(self):
        """Test validating a valid Pydantic model."""
        validator = SchemaValidator(schema=TestRequestSchema)

        request = TestRequestSchema(model="gpt-4", temperature=0.7, max_tokens=100)
        result = validator.validate(request)

        assert result.valid is True

    def test_invalid_type(self):
        """Test validating request with invalid type."""
        validator = SchemaValidator(schema=TestRequestSchema)

        request = {"model": "gpt-4", "temperature": "not a number"}
        result = validator.validate(request)

        assert result.valid is False
        assert len(result.errors) > 0
        assert "temperature" in str(result.errors[0])

    def test_missing_required_field(self):
        """Test validating request with missing required field."""
        validator = SchemaValidator(schema=TestRequestSchema)

        request = {"temperature": 0.7}  # Missing 'model'
        result = validator.validate(request)

        assert result.valid is False
        assert any("model" in str(err) for err in result.errors)

    def test_out_of_range_value(self):
        """Test validating request with out-of-range value."""
        validator = SchemaValidator(schema=TestRequestSchema)

        request = {"model": "gpt-4", "temperature": 3.0}  # Outside 0-2 range
        result = validator.validate(request)

        assert result.valid is False

    def test_validator_name(self):
        """Test validator name."""
        validator = SchemaValidator(schema=TestRequestSchema)
        assert "TestRequestSchema" in validator.name

        custom_validator = SchemaValidator(schema=TestRequestSchema, name="CustomName")
        assert custom_validator.name == "CustomName"


class TestContextLengthValidator:
    """Tests for ContextLengthValidator."""

    def test_valid_context_length(self):
        """Test validating a request within context limits."""
        validator = ContextLengthValidator()

        result = validator.validate(
            request={},
            context={
                "model": "gpt-4",
                "prompt_tokens": 100,
                "max_tokens": 500,
            },
        )

        assert result.valid is True

    def test_exceeded_context_length(self):
        """Test validating a request exceeding context limits."""
        validator = ContextLengthValidator()

        result = validator.validate(
            request={},
            context={
                "model": "gpt-4",
                "prompt_tokens": 7000,
                "max_tokens": 2000,  # 7000 + 2000 = 9000 > 8192
            },
        )

        assert result.valid is False
        assert "context_length_exceeded" in result.errors[0].code

    def test_multimodal_context_length(self):
        """Test validating context length with multi-modal content."""
        validator = ContextLengthValidator()

        result = validator.validate(
            request={},
            context={
                "model": "gpt-4-turbo",
                "prompt_tokens": 1000,
                "max_tokens": 1000,
                "image_tokens": 500,
                "video_tokens": 300,
            },
        )

        assert result.valid is True

    def test_missing_model(self):
        """Test validation fails without model."""
        validator = ContextLengthValidator()

        result = validator.validate(
            request={},
            context={"prompt_tokens": 100},
        )

        assert result.valid is False
        assert "missing_model" in result.errors[0].code

    def test_missing_prompt_tokens(self):
        """Test validation fails without prompt_tokens."""
        validator = ContextLengthValidator()

        result = validator.validate(
            request={},
            context={"model": "gpt-4"},
        )

        assert result.valid is False
        assert "missing_prompt_tokens" in result.errors[0].code


class TestParameterValidator:
    """Tests for ParameterValidator."""

    def test_valid_parameters(self):
        """Test validating valid parameters."""
        validator = ParameterValidator()

        request = {
            "model": "gpt-4",
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 100,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5,
        }
        result = validator.validate(request)

        assert result.valid is True

    def test_temperature_out_of_range(self):
        """Test invalid temperature value."""
        validator = ParameterValidator()

        request = {"temperature": 3.0}
        result = validator.validate(request)

        assert result.valid is False
        assert any("temperature" in err.param for err in result.errors)

    def test_temperature_warning(self):
        """Test high temperature warning."""
        validator = ParameterValidator()

        request = {"temperature": 1.8}
        result = validator.validate(request)

        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("temperature" in warn.param for warn in result.warnings)

    def test_top_p_out_of_range(self):
        """Test invalid top_p value."""
        validator = ParameterValidator()

        request = {"top_p": 1.5}
        result = validator.validate(request)

        assert result.valid is False
        assert any("top_p" in err.param for err in result.errors)

    def test_frequency_penalty_out_of_range(self):
        """Test invalid frequency_penalty value."""
        validator = ParameterValidator()

        request = {"frequency_penalty": 3.0}
        result = validator.validate(request)

        assert result.valid is False
        assert any("frequency_penalty" in err.param for err in result.errors)

    def test_presence_penalty_out_of_range(self):
        """Test invalid presence_penalty value."""
        validator = ParameterValidator()

        request = {"presence_penalty": -3.0}
        result = validator.validate(request)

        assert result.valid is False
        assert any("presence_penalty" in err.param for err in result.errors)

    def test_max_tokens_invalid(self):
        """Test invalid max_tokens value."""
        validator = ParameterValidator()

        request = {"max_tokens": 0}
        result = validator.validate(request)

        assert result.valid is False
        assert any("max_tokens" in err.param for err in result.errors)

    def test_n_invalid(self):
        """Test invalid n value."""
        validator = ParameterValidator()

        request = {"n": 0}
        result = validator.validate(request)

        assert result.valid is False
        assert any("n" in err.param for err in result.errors)

    def test_best_of_validation(self):
        """Test best_of validation."""
        validator = ParameterValidator()

        # Valid: best_of >= n
        request = {"n": 3, "best_of": 5}
        result = validator.validate(request)
        assert result.valid is True

        # Invalid: best_of < n
        request = {"n": 5, "best_of": 3}
        result = validator.validate(request)
        assert result.valid is False

    def test_both_sampling_params_warning(self):
        """Test warning when both temperature and top_p are set."""
        validator = ParameterValidator()

        request = {"temperature": 0.8, "top_p": 0.9}
        result = validator.validate(request)

        assert result.valid is True
        assert len(result.warnings) > 0

    def test_pydantic_model_input(self):
        """Test validation with Pydantic model input."""
        validator = ParameterValidator()

        request = TestRequestSchema(model="gpt-4", temperature=0.7)
        result = validator.validate(request)

        assert result.valid is True


class TestRateLimitValidator:
    """Tests for RateLimitValidator."""

    def test_valid_request_within_limits(self):
        """Test validating a request within rate limits."""
        rate_limiter = RateLimiter()
        rate_limiter.reset()  # Reset for clean test
        validator = RateLimitValidator(rate_limiter=rate_limiter)

        result = validator.validate(
            request={},
            context={"api_key": "test-key", "tokens": 100},
        )

        assert result.valid is True
        assert "rate_limit_headers" in result.metadata

    def test_missing_api_key(self):
        """Test validation fails without API key."""
        validator = RateLimitValidator()

        result = validator.validate(
            request={},
            context={"tokens": 100},
        )

        assert result.valid is False
        assert "missing_api_key" in result.errors[0].code


class TestAuthValidator:
    """Tests for AuthValidator."""

    def test_auth_not_required(self):
        """Test when auth is not required."""
        validator = AuthValidator(require_api_key=False)

        result = validator.validate(request={}, context={})

        assert result.valid is True

    def test_auth_required_with_key(self):
        """Test when auth is required and key is provided."""
        validator = AuthValidator(require_api_key=True)

        result = validator.validate(
            request={},
            context={"api_key": "test-key"},
        )

        assert result.valid is True

    def test_auth_required_without_key(self):
        """Test when auth is required but no key provided."""
        validator = AuthValidator(require_api_key=True)

        result = validator.validate(request={}, context={})

        assert result.valid is False
        assert "missing_api_key" in result.errors[0].code

    def test_valid_api_key_list(self):
        """Test with specific list of valid API keys."""
        validator = AuthValidator(
            valid_api_keys=["key1", "key2", "key3"],
            require_api_key=True,
        )

        # Valid key
        result = validator.validate(request={}, context={"api_key": "key1"})
        assert result.valid is True

        # Invalid key
        result = validator.validate(request={}, context={"api_key": "invalid"})
        assert result.valid is False
        assert "invalid_api_key" in result.errors[0].code


class TestContentPolicyValidator:
    """Tests for ContentPolicyValidator."""

    def test_clean_content(self):
        """Test validating clean content."""
        validator = ContentPolicyValidator(strict_mode=False)

        result = validator.validate(
            request={},
            context={"content": "This is perfectly fine content."},
        )

        assert result.valid is True
        assert len(result.warnings) == 0

    def test_flagged_content_warning(self):
        """Test flagged content in non-strict mode."""
        validator = ContentPolicyValidator(strict_mode=False)

        result = validator.validate(
            request={},
            context={"content": "How to hack into a system"},
        )

        assert result.valid is True
        assert len(result.warnings) > 0
        assert "flagged_terms" in result.metadata

    def test_flagged_content_error(self):
        """Test flagged content in strict mode."""
        validator = ContentPolicyValidator(strict_mode=True)

        result = validator.validate(
            request={},
            context={"content": "How to create malware"},
        )

        assert result.valid is False
        assert len(result.errors) > 0

    def test_large_content_warning(self):
        """Test warning for very large content."""
        validator = ContentPolicyValidator()

        large_content = "a" * 1_500_000  # 1.5M characters
        result = validator.validate(
            request={},
            context={"content": large_content},
        )

        assert result.valid is True
        assert len(result.warnings) > 0


class TestMultiModalValidator:
    """Tests for MultiModalValidator."""

    def test_text_only_content(self):
        """Test validating text-only content."""
        validator = MultiModalValidator()

        messages = [
            {"role": "user", "content": "Hello!"},
        ]
        result = validator.validate(
            request={},
            context={"model": "gpt-4", "messages": messages},
        )

        assert result.valid is True

    def test_vision_model_with_images(self):
        """Test vision model with image content."""
        validator = MultiModalValidator()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
                ],
            }
        ]
        result = validator.validate(
            request={},
            context={"model": "gpt-4-vision-preview", "messages": messages},
        )

        assert result.valid is True

    def test_non_vision_model_with_images(self):
        """Test non-vision model with image content."""
        validator = MultiModalValidator()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
                ],
            }
        ]
        result = validator.validate(
            request={},
            context={"model": "gpt-4", "messages": messages},  # Non-vision model
        )

        assert result.valid is False
        assert "unsupported_modality" in result.errors[0].code

    def test_missing_model(self):
        """Test validation fails without model."""
        validator = MultiModalValidator()

        result = validator.validate(
            request={},
            context={"messages": []},
        )

        assert result.valid is False
        assert "missing_model" in result.errors[0].code


class TestModelAvailabilityValidator:
    """Tests for ModelAvailabilityValidator."""

    def test_valid_model_id(self):
        """Test validating a valid model ID."""
        validator = ModelAvailabilityValidator(allow_auto_create=True)

        result = validator.validate(
            request={},
            context={"model": "gpt-4"},
        )

        assert result.valid is True

    def test_fine_tuned_model(self):
        """Test validating a fine-tuned model ID."""
        validator = ModelAvailabilityValidator(allow_auto_create=True)

        result = validator.validate(
            request={},
            context={"model": "ft:gpt-4:my-org::abc123"},
        )

        assert result.valid is True
        assert result.metadata["is_fine_tuned"] is True

    def test_empty_model_id(self):
        """Test validation fails for empty model ID."""
        validator = ModelAvailabilityValidator()

        result = validator.validate(
            request={},
            context={"model": ""},
        )

        assert result.valid is False
        # Empty string is caught by "not model" check, so it's missing_model
        assert "missing_model" in result.errors[0].code

    def test_invalid_characters(self):
        """Test validation fails for invalid characters."""
        validator = ModelAvailabilityValidator()

        result = validator.validate(
            request={},
            context={"model": "gpt-4<script>"},
        )

        assert result.valid is False

    def test_model_not_in_available_list(self):
        """Test validation with specific available models list."""
        validator = ModelAvailabilityValidator(
            available_models={"gpt-4", "gpt-3.5-turbo"},
            allow_auto_create=False,
        )

        # Valid model
        result = validator.validate(request={}, context={"model": "gpt-4"})
        assert result.valid is True

        # Invalid model
        result = validator.validate(request={}, context={"model": "unknown-model"})
        assert result.valid is False
        assert "model_not_found" in result.errors[0].code
