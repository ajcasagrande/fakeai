"""
Tests for context_validator module.
"""

import pytest

from fakeai.context_validator import (
    MODEL_CONTEXT_WINDOWS,
    calculate_remaining_budget,
    create_context_length_error,
    get_model_context_window,
    validate_context_length,
)


class TestGetModelContextWindow:
    """Tests for get_model_context_window()."""

    def test_direct_model_lookup(self):
        """Test direct model name lookup."""
        assert get_model_context_window("gpt-4") == 8192
        assert get_model_context_window("gpt-4-turbo") == 128000
        assert get_model_context_window("gpt-oss-120b") == 128000

    def test_model_with_prefix(self):
        """Test model names with provider prefixes."""
        assert get_model_context_window("openai/gpt-oss-120b") == 128000
        assert get_model_context_window("meta-llama/Llama-3.1-70B-Instruct") == 131072

    def test_fine_tuned_model(self):
        """Test fine-tuned model format (ft:base:org::id)."""
        assert get_model_context_window("ft:gpt-oss-20b:my-org::abc123") == 32768
        assert (
            get_model_context_window("ft:openai/gpt-oss-120b:my-org::xyz789") == 128000
        )
        assert get_model_context_window("ft:gpt-4:acme::model123") == 8192

    def test_unknown_model_uses_default(self):
        """Test unknown models fall back to default context window."""
        assert get_model_context_window("unknown-model-xyz") == 8192
        assert get_model_context_window("custom-model-2024") == 8192

    def test_all_models_in_dict(self):
        """Test all models defined in MODEL_CONTEXT_WINDOWS."""
        for model, expected_window in MODEL_CONTEXT_WINDOWS.items():
            if model != "default":
                assert get_model_context_window(model) == expected_window


class TestValidateContextLength:
    """Tests for validate_context_length()."""

    def test_valid_context_length(self):
        """Test valid prompt + max_tokens within context window."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=4000,
            max_tokens=2000,
        )
        assert is_valid is True
        assert error is None

    def test_exact_context_window_limit(self):
        """Test prompt + max_tokens exactly at context window limit."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=6192,
            max_tokens=2000,
        )
        assert is_valid is True
        assert error is None

    def test_exceeds_context_window(self):
        """Test prompt + max_tokens exceeds context window."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=7000,
            max_tokens=2000,
        )
        assert is_valid is False
        assert error is not None
        assert "8192 tokens" in error
        assert "9000 tokens" in error
        assert "7000 in the messages" in error
        assert "2000 in the completion" in error

    def test_prompt_only_exceeds_window(self):
        """Test prompt alone exceeds context window."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=10000,
            max_tokens=100,
        )
        assert is_valid is False
        assert error is not None
        assert "10100 tokens" in error

    def test_none_max_tokens_valid(self):
        """Test validation with max_tokens=None (prompt only)."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=5000,
            max_tokens=None,
        )
        assert is_valid is True
        assert error is None

    def test_none_max_tokens_exceeds(self):
        """Test validation with max_tokens=None when prompt exceeds window."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=10000,
            max_tokens=None,
        )
        assert is_valid is False
        assert error is not None
        assert "10000 tokens" in error
        assert "Please reduce the length of the messages." in error

    def test_multi_modal_tokens_included(self):
        """Test image/audio/video tokens are included in validation."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=4000,
            max_tokens=2000,
            image_tokens=1500,
            audio_tokens=500,
            video_tokens=500,
        )
        # Total: 4000 + 2000 + 1500 + 500 + 500 = 8500 > 8192
        assert is_valid is False
        assert error is not None
        assert "8500 tokens" in error
        assert "6500 in the messages" in error  # 4000 + 1500 + 500 + 500

    def test_multi_modal_tokens_valid(self):
        """Test multi-modal tokens within valid range."""
        is_valid, error = validate_context_length(
            model="gpt-oss-120b",
            prompt_tokens=50000,
            max_tokens=20000,
            image_tokens=30000,
            audio_tokens=10000,
            video_tokens=15000,
        )
        # Total: 50000 + 20000 + 30000 + 10000 + 15000 = 125000 < 128000
        assert is_valid is True
        assert error is None

    def test_large_context_window_model(self):
        """Test models with large context windows."""
        is_valid, error = validate_context_length(
            model="meta-llama/Llama-3.1-70B-Instruct",
            prompt_tokens=100000,
            max_tokens=20000,
        )
        assert is_valid is True
        assert error is None

    def test_zero_prompt_tokens(self):
        """Test validation with zero prompt tokens."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=0,
            max_tokens=1000,
        )
        assert is_valid is True
        assert error is None

    def test_zero_max_tokens(self):
        """Test validation with zero max_tokens."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=5000,
            max_tokens=0,
        )
        assert is_valid is True
        assert error is None

    def test_fine_tuned_model_validation(self):
        """Test validation uses base model context window for fine-tuned models."""
        is_valid, error = validate_context_length(
            model="ft:gpt-oss-20b:org::id123",
            prompt_tokens=30000,
            max_tokens=3000,
        )
        # gpt-oss-20b has 32768 context window
        assert is_valid is False
        assert error is not None

    def test_error_message_format(self):
        """Test error message matches OpenAI format."""
        _, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=7500,
            max_tokens=1500,
        )
        assert "This model's maximum context length is 8192 tokens" in error
        assert "However, your messages resulted in 9000 tokens" in error
        assert "(7500 in the messages, 1500 in the completion)" in error
        assert "Please reduce the length of the messages or completion" in error


class TestCalculateRemainingBudget:
    """Tests for calculate_remaining_budget()."""

    def test_basic_remaining_budget(self):
        """Test basic remaining budget calculation."""
        remaining = calculate_remaining_budget(
            model="gpt-4",
            prompt_tokens=4000,
            reserved_tokens=1000,
        )
        # 8192 - 4000 - 1000 = 3192
        assert remaining == 3192

    def test_no_reserved_tokens(self):
        """Test with custom reserved tokens."""
        remaining = calculate_remaining_budget(
            model="gpt-4",
            prompt_tokens=4000,
            reserved_tokens=0,
        )
        # 8192 - 4000 - 0 = 4192
        assert remaining == 4192

    def test_large_reserved_buffer(self):
        """Test with large reserved token buffer."""
        remaining = calculate_remaining_budget(
            model="gpt-4",
            prompt_tokens=2000,
            reserved_tokens=5000,
        )
        # 8192 - 2000 - 5000 = 1192
        assert remaining == 1192

    def test_negative_remaining_returns_zero(self):
        """Test negative remaining budget returns 0."""
        remaining = calculate_remaining_budget(
            model="gpt-4",
            prompt_tokens=7000,
            reserved_tokens=2000,
        )
        # 8192 - 7000 - 2000 = -808, should return 0
        assert remaining == 0

    def test_large_context_model(self):
        """Test with large context window model."""
        remaining = calculate_remaining_budget(
            model="claude-3-opus",
            prompt_tokens=100000,
            reserved_tokens=1000,
        )
        # 200000 - 100000 - 1000 = 99000
        assert remaining == 99000

    def test_default_reserved_tokens(self):
        """Test default reserved_tokens parameter."""
        remaining = calculate_remaining_budget(
            model="gpt-4",
            prompt_tokens=3000,
        )
        # 8192 - 3000 - 1000 = 4192
        assert remaining == 4192

    def test_exact_capacity_used(self):
        """Test when prompt + reserved exactly equals context window."""
        remaining = calculate_remaining_budget(
            model="gpt-4",
            prompt_tokens=7192,
            reserved_tokens=1000,
        )
        # 8192 - 7192 - 1000 = 0
        assert remaining == 0


class TestCreateContextLengthError:
    """Tests for create_context_length_error()."""

    def test_error_response_structure(self):
        """Test error response has correct structure."""
        error_msg = "Test error message"
        error_response = create_context_length_error(error_msg)

        assert "error" in error_response
        assert error_response["error"]["message"] == error_msg
        assert error_response["error"]["type"] == "invalid_request_error"
        assert error_response["error"]["param"] == "messages"
        assert error_response["error"]["code"] == "context_length_exceeded"

    def test_error_with_validation_message(self):
        """Test error creation with actual validation message."""
        _, error_msg = validate_context_length(
            model="gpt-4",
            prompt_tokens=7000,
            max_tokens=2000,
        )
        error_response = create_context_length_error(error_msg)

        assert error_response["error"]["message"] == error_msg
        assert "9000 tokens" in error_response["error"]["message"]


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_max_tokens(self):
        """Test with very small max_tokens (1 token)."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=8191,
            max_tokens=1,
        )
        assert is_valid is True
        assert error is None

    def test_very_large_prompt_small_completion(self):
        """Test large prompt with small completion."""
        is_valid, error = validate_context_length(
            model="gpt-4-turbo",
            prompt_tokens=127000,
            max_tokens=500,
        )
        assert is_valid is True
        assert error is None

    def test_all_multi_modal_no_text(self):
        """Test validation with only multi-modal tokens, no text."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=0,
            max_tokens=2000,
            image_tokens=6000,
        )
        # Total: 0 + 2000 + 6000 = 8000 < 8192
        assert is_valid is True
        assert error is None

    def test_model_name_case_sensitivity(self):
        """Test model names are case-sensitive."""
        # Should use default for GPT-4 (uppercase)
        window_upper = get_model_context_window("GPT-4")
        window_lower = get_model_context_window("gpt-4")
        assert window_upper == MODEL_CONTEXT_WINDOWS["default"]
        assert window_lower == 8192

    def test_minimum_context_window_default(self):
        """Test default context window is reasonable minimum."""
        assert MODEL_CONTEXT_WINDOWS["default"] == 8192

    def test_validation_with_all_zero_values(self):
        """Test validation with all zero token values."""
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=0,
            max_tokens=0,
            image_tokens=0,
            audio_tokens=0,
            video_tokens=0,
        )
        assert is_valid is True
        assert error is None
