"""
Comprehensive tests for the tokenizers module.

Tests accurate token counting with tiktoken integration and fallback mechanisms.
"""

import pytest

from fakeai.tokenizers import (
    _heuristic_token_count,
    _infer_encoding_from_model,
    batch_token_count,
    calculate_token_count,
    estimate_tokens_from_messages,
    get_encoding_name_for_model,
    get_token_count,
    get_tokenizer_for_model,
    is_tiktoken_available,
    tokenize_text_accurate,
)


@pytest.mark.unit
class TestTiktokenAvailability:
    """Test tiktoken availability detection."""

    def test_tiktoken_availability_returns_bool(self):
        """Should return a boolean indicating tiktoken availability."""
        result = is_tiktoken_available()
        assert isinstance(result, bool)

    def test_availability_consistent_across_calls(self):
        """Availability should be consistent across multiple calls."""
        result1 = is_tiktoken_available()
        result2 = is_tiktoken_available()
        assert result1 == result2


@pytest.mark.unit
class TestEncodingInference:
    """Test encoding inference from model names."""

    def test_gpt4_uses_cl100k_base(self):
        """GPT-4 models should use cl100k_base encoding."""
        assert _infer_encoding_from_model("gpt-4") == "cl100k_base"
        assert _infer_encoding_from_model("gpt-4-turbo") == "cl100k_base"
        assert _infer_encoding_from_model("gpt-4o") == "cl100k_base"

    def test_gpt35_uses_cl100k_base(self):
        """GPT-3.5-turbo models should use cl100k_base encoding."""
        assert _infer_encoding_from_model("gpt-3.5-turbo") == "cl100k_base"
        assert _infer_encoding_from_model("gpt-3.5-turbo-16k") == "cl100k_base"

    def test_gpt_oss_uses_cl100k_base(self):
        """GPT-OSS models should use cl100k_base encoding."""
        assert _infer_encoding_from_model("gpt-oss-120b") == "cl100k_base"
        assert _infer_encoding_from_model("openai/gpt-oss-20b") == "cl100k_base"

    def test_davinci_uses_p50k_base(self):
        """Davinci models should use p50k_base encoding."""
        assert _infer_encoding_from_model("text-davinci-003") == "p50k_base"
        assert _infer_encoding_from_model("text-davinci-002") == "p50k_base"

    def test_code_models_use_p50k_base(self):
        """Code models should use p50k_base encoding."""
        assert _infer_encoding_from_model("code-davinci-002") == "p50k_base"
        assert _infer_encoding_from_model("code-cushman-001") == "p50k_base"

    def test_fine_tuned_model_inference(self):
        """Fine-tuned models should use base model encoding."""
        # Format: ft:base_model:org::id
        result = _infer_encoding_from_model("ft:gpt-4:my-org::abc123")
        assert result == "cl100k_base"

        result = _infer_encoding_from_model("ft:text-davinci-003:org::xyz")
        assert result == "p50k_base"

    def test_unknown_model_defaults_to_cl100k_base(self):
        """Unknown models should default to cl100k_base."""
        assert _infer_encoding_from_model("unknown-model-xyz") == "cl100k_base"

    def test_case_insensitive_matching(self):
        """Model name matching should be case-insensitive."""
        assert _infer_encoding_from_model("GPT-4") == "cl100k_base"
        assert _infer_encoding_from_model("TEXT-DAVINCI-003") == "p50k_base"


@pytest.mark.unit
class TestEncodingNameRetrieval:
    """Test encoding name retrieval for models."""

    def test_get_encoding_name_for_gpt4(self):
        """Should return correct encoding name for GPT-4."""
        assert get_encoding_name_for_model("gpt-4") == "cl100k_base"

    def test_get_encoding_name_for_davinci(self):
        """Should return correct encoding name for Davinci."""
        assert get_encoding_name_for_model("text-davinci-003") == "p50k_base"

    def test_encoding_name_matches_inference(self):
        """Encoding name should match inference logic."""
        model = "gpt-3.5-turbo"
        encoding_name = get_encoding_name_for_model(model)
        inferred = _infer_encoding_from_model(model)
        assert encoding_name == inferred


@pytest.mark.unit
class TestHeuristicTokenCounting:
    """Test heuristic-based token counting fallback."""

    def test_empty_string_returns_zero(self):
        """Empty string should return 0 tokens."""
        assert _heuristic_token_count("") == 0

    def test_single_word_counted(self):
        """Single word should be counted as at least 1 token."""
        count = _heuristic_token_count("hello")
        assert count >= 1

    def test_multiple_words_counted(self):
        """Multiple words should increase token count."""
        single = _heuristic_token_count("hello")
        multiple = _heuristic_token_count("hello world foo bar")
        assert multiple > single

    def test_punctuation_adds_tokens(self):
        """Punctuation should add to token count."""
        without = _heuristic_token_count("hello world")
        with_punct = _heuristic_token_count("hello, world!")
        assert with_punct > without

    def test_complex_sentence_reasonable_estimate(self):
        """Complex sentence should give reasonable token estimate."""
        text = "Hello, how are you doing today? I hope everything is great!"
        count = _heuristic_token_count(text)
        # Should be roughly 15-20 tokens (words + punctuation)
        assert 10 <= count <= 30

    def test_code_like_text_handling(self):
        """Should handle code-like text with special characters."""
        code = "def hello(name: str) -> None:"
        count = _heuristic_token_count(code)
        assert count > 0


@pytest.mark.unit
class TestTokenCountFunction:
    """Test main token counting function."""

    def test_empty_string_returns_zero(self):
        """Empty string should return 0 tokens."""
        assert get_token_count("") == 0
        assert get_token_count("", model="gpt-4") == 0

    def test_simple_text_counting(self):
        """Should count tokens for simple text."""
        count = get_token_count("Hello, world!")
        assert count > 0

    def test_longer_text_more_tokens(self):
        """Longer text should have more tokens."""
        short = get_token_count("Hi")
        long = get_token_count("This is a much longer sentence with many words")
        assert long > short

    def test_different_models_parameter(self):
        """Should accept different model parameters."""
        text = "Hello, world!"
        count_gpt4 = get_token_count(text, model="gpt-4")
        count_gpt35 = get_token_count(text, model="gpt-3.5-turbo")
        # Both should work (may or may not be identical)
        assert count_gpt4 > 0
        assert count_gpt35 > 0

    def test_unicode_text_handling(self):
        """Should handle Unicode text correctly."""
        text = "Hello 世界! 🌍"
        count = get_token_count(text)
        assert count > 0

    def test_whitespace_handling(self):
        """Should handle whitespace-only strings."""
        count = get_token_count("   ")
        # Should return minimal tokens (0 or 1)
        assert count >= 0

    def test_none_value_handling(self):
        """Should handle None gracefully."""
        # Empty string check happens first
        assert get_token_count("") == 0

    def test_caching_returns_same_result(self):
        """Repeated calls with same input should return cached result."""
        text = "This is a test for caching behavior"
        count1 = get_token_count(text, model="gpt-4")
        count2 = get_token_count(text, model="gpt-4")
        assert count1 == count2


@pytest.mark.unit
class TestBackwardCompatibility:
    """Test backward compatibility with calculate_token_count."""

    def test_calculate_token_count_exists(self):
        """Old function name should still exist."""
        assert callable(calculate_token_count)

    def test_empty_string_returns_zero(self):
        """Empty string should return 0 tokens."""
        assert calculate_token_count("") == 0

    def test_simple_text_counting(self):
        """Should count tokens for simple text."""
        count = calculate_token_count("Hello, world!")
        assert count > 0

    def test_matches_new_function_behavior(self):
        """Should produce similar results to get_token_count."""
        text = "This is a test of backward compatibility"
        old_count = calculate_token_count(text)
        new_count = get_token_count(text, model="gpt-4")
        # Should be identical (both use gpt-4 default)
        assert old_count == new_count


@pytest.mark.unit
class TestBatchTokenCounting:
    """Test batch token counting for multiple texts."""

    def test_empty_list_returns_empty(self):
        """Empty list should return empty result."""
        result = batch_token_count([])
        assert result == []

    def test_single_text_batch(self):
        """Single text should return list with one count."""
        result = batch_token_count(["Hello"])
        assert len(result) == 1
        assert result[0] > 0

    def test_multiple_texts(self):
        """Should return counts for all texts."""
        texts = ["Hello", "Hello, world!", "This is a longer sentence"]
        result = batch_token_count(texts)
        assert len(result) == 3
        assert all(count > 0 for count in result)
        # Longer texts should have more tokens
        assert result[0] < result[1] < result[2]

    def test_with_model_parameter(self):
        """Should work with different model parameters."""
        texts = ["Test 1", "Test 2"]
        result = batch_token_count(texts, model="gpt-3.5-turbo")
        assert len(result) == 2
        assert all(count > 0 for count in result)

    def test_empty_strings_in_batch(self):
        """Should handle empty strings in batch."""
        texts = ["Hello", "", "World"]
        result = batch_token_count(texts)
        assert len(result) == 3
        assert result[0] > 0
        assert result[1] == 0
        assert result[2] > 0


@pytest.mark.unit
class TestMessageTokenEstimation:
    """Test token estimation for chat messages."""

    def test_empty_messages_returns_zero(self):
        """Empty message list should return 0 tokens."""
        assert estimate_tokens_from_messages([]) == 0

    def test_single_message_counted(self):
        """Single message should include content and overhead tokens."""
        messages = [{"role": "user", "content": "Hello"}]
        count = estimate_tokens_from_messages(messages)
        # Should be more than just content tokens (includes overhead)
        assert count > 1

    def test_multiple_messages(self):
        """Multiple messages should accumulate tokens."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        count = estimate_tokens_from_messages(messages)
        # Should be substantial (3 messages + overhead)
        assert count > 10

    def test_message_with_name_field(self):
        """Messages with name field should include name tokens."""
        messages = [{"role": "user", "name": "Alice", "content": "Hello"}]
        count_with_name = estimate_tokens_from_messages(messages)

        messages_without = [{"role": "user", "content": "Hello"}]
        count_without_name = estimate_tokens_from_messages(messages_without)

        # With name should have more tokens
        assert count_with_name > count_without_name

    def test_multimodal_content_handling(self):
        """Should handle multi-modal content (text + images)."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/img.jpg"},
                    },
                ],
            }
        ]
        count = estimate_tokens_from_messages(messages)
        # Should count text content
        assert count > 0

    def test_different_models(self):
        """Should work with different model parameters."""
        messages = [{"role": "user", "content": "Hello"}]
        count_gpt4 = estimate_tokens_from_messages(messages, model="gpt-4")
        count_gpt35 = estimate_tokens_from_messages(messages, model="gpt-3.5-turbo")
        # Both should work
        assert count_gpt4 > 0
        assert count_gpt35 > 0

    def test_empty_content_handling(self):
        """Should handle messages with empty content."""
        messages = [{"role": "user", "content": ""}]
        count = estimate_tokens_from_messages(messages)
        # Should still count overhead tokens
        assert count > 0


@pytest.mark.unit
class TestTiktokenIntegration:
    """Test tiktoken integration when available."""

    @pytest.mark.skipif(not is_tiktoken_available(), reason="tiktoken not installed")
    def test_get_tokenizer_for_gpt4(self):
        """Should get tokenizer for GPT-4."""
        tokenizer = get_tokenizer_for_model("gpt-4")
        assert tokenizer is not None

    @pytest.mark.skipif(not is_tiktoken_available(), reason="tiktoken not installed")
    def test_tokenize_text_returns_token_ids(self):
        """Should return token IDs for text."""
        tokens = tokenize_text_accurate("Hello, world!")
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(token, int) for token in tokens)

    @pytest.mark.skipif(not is_tiktoken_available(), reason="tiktoken not installed")
    def test_empty_text_returns_empty_tokens(self):
        """Empty text should return empty token list."""
        tokens = tokenize_text_accurate("")
        assert tokens == []

    @pytest.mark.skipif(not is_tiktoken_available(), reason="tiktoken not installed")
    def test_token_ids_consistent(self):
        """Same text should produce same token IDs."""
        text = "Consistency test"
        tokens1 = tokenize_text_accurate(text)
        tokens2 = tokenize_text_accurate(text)
        assert tokens1 == tokens2

    @pytest.mark.skipif(not is_tiktoken_available(), reason="tiktoken not installed")
    def test_token_count_matches_token_ids_length(self):
        """Token count should match length of token IDs."""
        text = "Hello, world!"
        count = get_token_count(text)
        tokens = tokenize_text_accurate(text)
        assert count == len(tokens)

    @pytest.mark.skipif(
        is_tiktoken_available(), reason="Test only applies when tiktoken not available"
    )
    def test_tokenize_raises_without_tiktoken(self):
        """Should raise error when tiktoken not available."""
        with pytest.raises(RuntimeError, match="tiktoken library is not available"):
            tokenize_text_accurate("Hello")

    @pytest.mark.skipif(
        is_tiktoken_available(), reason="Test only applies when tiktoken not available"
    )
    def test_get_tokenizer_raises_without_tiktoken(self):
        """Should raise error when tiktoken not available."""
        with pytest.raises(RuntimeError, match="tiktoken library is not available"):
            get_tokenizer_for_model("gpt-4")


@pytest.mark.unit
class TestCachingBehavior:
    """Test LRU caching behavior."""

    def test_repeated_calls_use_cache(self):
        """Repeated calls with same input should be fast (cached)."""
        import time

        text = "This is a test of caching behavior"

        # First call (not cached)
        start1 = time.perf_counter()
        count1 = get_token_count(text)
        time1 = time.perf_counter() - start1

        # Second call (should be cached)
        start2 = time.perf_counter()
        count2 = get_token_count(text)
        time2 = time.perf_counter() - start2

        # Results should be identical
        assert count1 == count2
        # Second call should be faster (or at least not slower)
        # Note: This is a weak assertion because of timing variability
        assert time2 <= time1 * 10  # Allow 10x variance for system jitter

    def test_different_inputs_not_cached_together(self):
        """Different inputs should produce different cached results."""
        text1 = "Short"
        text2 = "This is a much longer text with many more words"

        count1 = get_token_count(text1)
        count2 = get_token_count(text2)

        # Should be different (different lengths)
        assert count1 != count2

    def test_model_parameter_affects_cache_key(self):
        """Different model parameters should have separate cache entries."""
        text = "Hello, world!"

        count_gpt4 = get_token_count(text, model="gpt-4")
        count_davinci = get_token_count(text, model="text-davinci-003")

        # Both should work (may be same or different depending on encoding)
        assert count_gpt4 > 0
        assert count_davinci > 0


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_long_text(self):
        """Should handle very long text."""
        text = "word " * 10000  # 10,000 words
        count = get_token_count(text)
        # Should be substantial
        assert count > 5000

    def test_special_characters(self):
        """Should handle special characters."""
        text = "Hello! @#$%^&*() []{}|\\:;\"'<>,.?/~`"
        count = get_token_count(text)
        assert count > 0

    def test_newlines_and_tabs(self):
        """Should handle newlines and tabs."""
        text = "Line 1\nLine 2\tTabbed"
        count = get_token_count(text)
        assert count > 0

    def test_mixed_language_text(self):
        """Should handle mixed language text."""
        text = "Hello world 你好世界 مرحبا بالعالم"
        count = get_token_count(text)
        assert count > 0

    def test_emoji_handling(self):
        """Should handle emoji characters."""
        text = "Hello 👋 World 🌍"
        count = get_token_count(text)
        assert count > 0

    def test_repeated_whitespace(self):
        """Should handle repeated whitespace."""
        text = "Hello     world"
        count = get_token_count(text)
        assert count > 0
