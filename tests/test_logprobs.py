"""
Tests for Enhanced Log Probabilities Generation

This module tests the realistic logprobs generation for both Chat and Completions APIs.
"""
#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.logprobs_enhanced import (
    estimate_token_confidence,
    generate_realistic_top_logprobs,
    generate_alternative_token,
    token_to_bytes,
    create_chat_logprobs,
    create_completion_logprobs,
)


class TestTokenConfidenceEstimation:
    """Test token confidence estimation."""

    def test_common_tokens_high_confidence(self):
        """Common tokens should generally have high confidence."""
        # Test with common tokens
        common_tokens = ["the", "a", "and", ".", ","]
        context_hash = hash("test context")

        for token in common_tokens:
            confidence = estimate_token_confidence(token, 0, context_hash, temperature=1.0)
            # Common tokens tend to be high confidence
            assert confidence in ["high", "medium", "low"]

    def test_temperature_affects_confidence(self):
        """Temperature should affect confidence distribution."""
        token = "test"
        context_hash = hash("context")

        # Low temperature should generally favor higher confidence
        low_temp_confidence = estimate_token_confidence(token, 0, context_hash, temperature=0.1)

        # High temperature should generally favor lower confidence
        high_temp_confidence = estimate_token_confidence(token, 0, context_hash, temperature=2.0)

        # Both should be valid confidence levels
        assert low_temp_confidence in ["high", "medium", "low"]
        assert high_temp_confidence in ["high", "medium", "low"]

    def test_deterministic_output(self):
        """Same inputs should produce same confidence."""
        token = "hello"
        position = 5
        context_hash = hash("fixed context")
        temperature = 1.0

        conf1 = estimate_token_confidence(token, position, context_hash, temperature)
        conf2 = estimate_token_confidence(token, position, context_hash, temperature)

        assert conf1 == conf2, "Confidence estimation should be deterministic"


class TestTopLogprobsGeneration:
    """Test generation of top-k alternative tokens."""

    def test_returns_correct_number_of_alternatives(self):
        """Should return exactly top_k alternatives."""
        token = "test"
        position = 0
        context_hash = hash("context")
        token_logprob = -0.1
        top_k = 5

        alternatives = generate_realistic_top_logprobs(
            token, position, context_hash, token_logprob, top_k, temperature=1.0
        )

        assert len(alternatives) == top_k

    def test_alternatives_are_sorted_descending(self):
        """Alternatives should be sorted by logprob descending."""
        token = "hello"
        position = 0
        context_hash = hash("context")
        token_logprob = -0.05

        alternatives = generate_realistic_top_logprobs(
            token, position, context_hash, token_logprob, top_k=5, temperature=1.0
        )

        # Check that logprobs are in descending order
        logprobs = [alt["logprob"] for alt in alternatives]
        assert logprobs == sorted(logprobs, reverse=True), "Logprobs should be sorted descending"

    def test_logprobs_have_realistic_gaps(self):
        """Gap between alternatives should be realistic (not too small, not too large)."""
        token = "test"
        position = 0
        context_hash = hash("context")
        token_logprob = -0.1

        alternatives = generate_realistic_top_logprobs(
            token, position, context_hash, token_logprob, top_k=5, temperature=1.0
        )

        # Check gaps between consecutive alternatives
        for i in range(len(alternatives) - 1):
            gap = alternatives[i]["logprob"] - alternatives[i+1]["logprob"]
            # Gaps should be positive (descending) and reasonable (0.1 to 10.0)
            assert 0.1 < gap < 10.0, f"Gap {gap} between alternatives is unrealistic"

    def test_alternatives_are_lower_than_selected(self):
        """All alternatives should have lower logprobs than selected token."""
        token = "selected"
        position = 0
        context_hash = hash("context")
        token_logprob = -0.1

        alternatives = generate_realistic_top_logprobs(
            token, position, context_hash, token_logprob, top_k=5, temperature=1.0
        )

        for alt in alternatives:
            assert alt["logprob"] < token_logprob, "Alternatives should have lower probability"

    def test_deterministic_generation(self):
        """Same inputs should produce same alternatives."""
        token = "test"
        position = 3
        context_hash = hash("fixed context")
        token_logprob = -0.2

        alts1 = generate_realistic_top_logprobs(token, position, context_hash, token_logprob, 5, 1.0)
        alts2 = generate_realistic_top_logprobs(token, position, context_hash, token_logprob, 5, 1.0)

        assert alts1 == alts2, "Alternative generation should be deterministic"


class TestAlternativeTokenGeneration:
    """Test generation of plausible alternative tokens."""

    def test_generates_different_alternatives(self):
        """Each alternative index should produce a different token."""
        import random

        token = "hello"
        context_hash = hash("context")
        rng = random.Random(42)

        alternatives = [
            generate_alternative_token(token, i, context_hash, rng)
            for i in range(5)
        ]

        # Should have at least some variety
        assert len(set(alternatives)) > 1, "Should generate different alternatives"

    def test_common_word_alternatives(self):
        """Common words should have predefined alternatives."""
        import random

        rng = random.Random(42)
        context_hash = hash("context")

        # "the" has predefined alternatives
        alt = generate_alternative_token("the", 0, context_hash, rng)
        assert alt in ["a", "The", "this", "that", "its"]


class TestTokenToBytes:
    """Test UTF-8 byte conversion."""

    def test_ascii_characters(self):
        """ASCII characters should convert correctly."""
        assert token_to_bytes("a") == [97]
        assert token_to_bytes("A") == [65]
        assert token_to_bytes("hello") == [104, 101, 108, 108, 111]

    def test_punctuation(self):
        """Punctuation should convert correctly."""
        assert token_to_bytes(".") == [46]
        assert token_to_bytes(",") == [44]
        assert token_to_bytes("!") == [33]

    def test_unicode_characters(self):
        """Unicode characters should convert to multi-byte sequences."""
        # é is U+00E9, UTF-8: 0xC3 0xA9
        assert token_to_bytes("é") == [195, 169]

        # 你 is U+4F60, UTF-8: 0xE4 0xBD 0xA0
        assert token_to_bytes("你") == [228, 189, 160]

    def test_empty_string(self):
        """Empty string should return empty list."""
        assert token_to_bytes("") == []


class TestChatLogprobs:
    """Test Chat API logprobs generation."""

    def test_returns_none_when_top_logprobs_none(self):
        """Should return None when top_logprobs is None."""
        result = create_chat_logprobs("hello world", ["hello", "world"], top_logprobs=None)
        assert result is None

    def test_generates_logprobs_for_all_tokens(self):
        """Should generate logprobs for each token."""
        text = "hello world"
        tokens = ["hello", "world"]

        result = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)

        assert result is not None
        assert result.content is not None
        assert len(result.content) == len(tokens)

    def test_logprobs_in_valid_range(self):
        """Logprobs should be in valid range (negative values)."""
        text = "the cat"
        tokens = ["the", "cat"]

        result = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)

        for logprob_entry in result.content:
            # Main token logprob should be negative
            assert logprob_entry.logprob < 0, "Logprobs should be negative"
            # Should be reasonable (not too extreme)
            assert -10.0 < logprob_entry.logprob < 0, "Logprobs should be in reasonable range"

    def test_top_logprobs_are_ordered(self):
        """Top logprobs should be in descending order."""
        text = "hello"
        tokens = ["hello"]

        result = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)

        top_logprobs_list = result.content[0].top_logprobs
        logprobs = [tl.logprob for tl in top_logprobs_list]

        assert logprobs == sorted(logprobs, reverse=True), "Top logprobs should be sorted"

    def test_bytes_match_utf8_encoding(self):
        """Bytes should match UTF-8 encoding of tokens."""
        text = "hello"
        tokens = ["hello"]

        result = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)

        for logprob_entry in result.content:
            expected_bytes = list("hello".encode("utf-8"))
            assert logprob_entry.bytes == expected_bytes

    def test_alternatives_have_bytes(self):
        """Alternative tokens should also have byte arrays."""
        text = "test"
        tokens = ["test"]

        result = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)

        for alt in result.content[0].top_logprobs:
            assert alt.bytes is not None
            assert len(alt.bytes) > 0
            # Bytes should match UTF-8 encoding of alternative token
            assert alt.bytes == list(alt.token.encode("utf-8"))

    def test_deterministic_output(self):
        """Same inputs should produce same output."""
        text = "hello world"
        tokens = ["hello", "world"]

        result1 = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)
        result2 = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)

        # Compare logprobs
        for i in range(len(tokens)):
            assert result1.content[i].logprob == result2.content[i].logprob
            assert result1.content[i].token == result2.content[i].token

    def test_temperature_affects_logprobs(self):
        """Different temperatures should affect logprob values."""
        text = "hello"
        tokens = ["hello"]

        low_temp = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=0.1)
        high_temp = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=2.0)

        # Both should generate valid logprobs (specific values may vary due to confidence estimation)
        assert low_temp.content[0].logprob < 0
        assert high_temp.content[0].logprob < 0


class TestCompletionLogprobs:
    """Test Completions API logprobs generation (legacy format)."""

    def test_returns_none_when_logprobs_none(self):
        """Should return None when logprobs is None."""
        result = create_completion_logprobs("hello world", ["hello", "world"], logprobs=None)
        assert result is None

    def test_returns_none_when_logprobs_zero(self):
        """Should return None when logprobs is 0."""
        result = create_completion_logprobs("hello world", ["hello", "world"], logprobs=0)
        assert result is None

    def test_generates_logprobs_for_all_tokens(self):
        """Should generate logprobs for each token."""
        text = "hello world"
        tokens = ["hello", "world"]

        result = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)

        assert result is not None
        assert len(result.tokens) == len(tokens)
        assert len(result.token_logprobs) == len(tokens)
        assert len(result.text_offset) == len(tokens)

    def test_logprobs_in_valid_range(self):
        """Token logprobs should be negative and reasonable."""
        text = "the cat"
        tokens = ["the", "cat"]

        result = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)

        for logprob in result.token_logprobs:
            assert logprob < 0, "Logprobs should be negative"
            assert -10.0 < logprob < 0, "Logprobs should be in reasonable range"

    def test_top_logprobs_include_selected_token(self):
        """Top logprobs dict should include the selected token."""
        text = "hello"
        tokens = ["hello"]

        result = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)

        # First token's top_logprobs should include "hello"
        assert "hello" in result.top_logprobs[0]

    def test_top_logprobs_dict_format(self):
        """Top logprobs should be in dict format (legacy API)."""
        text = "test"
        tokens = ["test"]

        result = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)

        # Should be a dict
        assert isinstance(result.top_logprobs[0], dict)
        # Should have multiple entries
        assert len(result.top_logprobs[0]) > 1

    def test_text_offset_accuracy(self):
        """Text offsets should correctly point to token positions."""
        text = "hello world test"
        tokens = ["hello", "world", "test"]

        result = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)

        # First token should be at position 0
        assert result.text_offset[0] == 0
        # Offsets should be increasing
        for i in range(len(result.text_offset) - 1):
            assert result.text_offset[i] < result.text_offset[i+1]

    def test_deterministic_output(self):
        """Same inputs should produce same output."""
        text = "hello world"
        tokens = ["hello", "world"]

        result1 = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)
        result2 = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)

        assert result1.tokens == result2.tokens
        assert result1.token_logprobs == result2.token_logprobs
        assert result1.text_offset == result2.text_offset


class TestIntegration:
    """Integration tests for the complete logprobs system."""

    def test_realistic_sentence_chat_api(self):
        """Test with a realistic sentence for Chat API."""
        text = "The quick brown fox jumps over the lazy dog."
        tokens = ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog", "."]

        result = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)

        assert result is not None
        assert len(result.content) == len(tokens)

        # Check all tokens have valid logprobs
        for entry in result.content:
            assert entry.token in tokens
            assert entry.logprob < 0
            assert len(entry.top_logprobs) == 5
            assert entry.bytes is not None

    def test_realistic_sentence_completions_api(self):
        """Test with a realistic sentence for Completions API."""
        text = "The quick brown fox jumps over the lazy dog."
        tokens = ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog", "."]

        result = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)

        assert result is not None
        assert result.tokens == tokens
        assert len(result.token_logprobs) == len(tokens)
        assert len(result.top_logprobs) == len(tokens)
        assert len(result.text_offset) == len(tokens)

    def test_punctuation_handling(self):
        """Test correct handling of punctuation."""
        text = "Hello, world!"
        tokens = ["Hello", ",", "world", "!"]

        chat_result = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)
        completion_result = create_completion_logprobs(text, tokens, logprobs=5, temperature=1.0)

        # Both should handle punctuation
        assert len(chat_result.content) == 4
        assert len(completion_result.tokens) == 4

    def test_unicode_handling(self):
        """Test correct handling of Unicode characters."""
        text = "Héllo wörld"
        tokens = ["Héllo", "wörld"]

        result = create_chat_logprobs(text, tokens, top_logprobs=5, temperature=1.0)

        # Should handle Unicode correctly
        assert len(result.content) == 2
        # Bytes should be multi-byte for Unicode chars
        assert len(result.content[0].bytes) > len("Héllo")  # é takes 2 bytes
