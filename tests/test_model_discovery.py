"""Tests for model discovery and fuzzy matching system."""


from fakeai.models_registry.discovery import (
    MatchResult,
    ModelMatcher,
    fuzzy_match_model,
    infer_model_characteristics,
    normalize_model_id,
    parse_fine_tuned_model,
    suggest_similar_models,
)


class TestNormalization:
    """Tests for model ID normalization."""

    def test_normalize_basic(self):
        """Test basic normalization."""
        assert normalize_model_id("GPT-4") == "gpt4"
        assert normalize_model_id("gpt-3.5-turbo") == "gpt35turbo"

    def test_normalize_provider_prefix(self):
        """Test removal of provider prefixes."""
        assert normalize_model_id("openai/gpt-4") == "gpt4"
        assert normalize_model_id("meta/llama-2") == "llama2"
        assert normalize_model_id("anthropic/claude-3") == "claude3"
        assert normalize_model_id("meta-llama/Llama-3-8B") == "llama38b"
        assert normalize_model_id("deepseek-ai/DeepSeek-R1") == "deepseekr1"

    def test_normalize_separators(self):
        """Test separator standardization."""
        assert normalize_model_id("gpt_4_turbo") == "gpt4turbo"
        assert normalize_model_id("gpt-4-turbo") == "gpt4turbo"
        assert normalize_model_id("gpt/4/turbo") == "gpt4turbo"
        assert normalize_model_id("gpt_4-turbo/v2") == "gpt4turbov2"

    def test_normalize_version_suffix(self):
        """Test version suffix removal."""
        assert normalize_model_id("gpt-4-v1") == "gpt4"
        assert normalize_model_id("gpt-4-v2") == "gpt4"
        assert normalize_model_id("claude-3-v10") == "claude3"

    def test_normalize_whitespace(self):
        """Test whitespace trimming."""
        assert normalize_model_id("  gpt-4  ") == "gpt4"
        assert normalize_model_id("\tgpt-4\n") == "gpt4"

    def test_normalize_empty(self):
        """Test empty string normalization."""
        assert normalize_model_id("") == ""
        assert normalize_model_id(None) == ""

    def test_normalize_complex(self):
        """Test complex normalization scenarios."""
        assert normalize_model_id("OpenAI/GPT-4_Turbo-v2") == "gpt4turbo"
        assert (
            normalize_model_id("Meta-Llama/Llama-3.1-405B-Instruct")
            == "llama31405binstruct"
        )


class TestFuzzyMatching:
    """Tests for fuzzy model matching."""

    def test_exact_match(self):
        """Test exact matching (highest confidence)."""
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        match, confidence = fuzzy_match_model("gpt-4", models)
        assert match == "gpt-4"
        assert confidence == 1.0

    def test_normalized_match(self):
        """Test normalized matching."""
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        match, confidence = fuzzy_match_model("GPT-4", models)
        assert match == "gpt-4"
        assert confidence == 0.95

    def test_normalized_match_with_prefix(self):
        """Test normalized matching with provider prefix."""
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        match, confidence = fuzzy_match_model("openai/gpt-4", models)
        assert match == "gpt-4"
        assert confidence == 0.95

    def test_substring_match(self):
        """Test substring matching."""
        models = ["gpt-4-turbo", "gpt-3.5-turbo", "claude-3"]
        match, confidence = fuzzy_match_model("gpt-4", models)
        assert match == "gpt-4-turbo"
        assert 0.85 <= confidence <= 0.95

    def test_substring_match_normalized(self):
        """Test substring matching with normalization."""
        models = ["gpt-4-turbo-preview", "gpt-3.5-turbo", "claude-3"]
        match, confidence = fuzzy_match_model("gpt4turbo", models)
        assert match == "gpt-4-turbo-preview"
        assert 0.80 <= confidence <= 0.95

    def test_edit_distance_match(self):
        """Test edit distance matching."""
        models = ["gpt-4", "gpt-3", "claude-3"]
        match, confidence = fuzzy_match_model("gpt4", models)
        assert match == "gpt-4"
        assert confidence >= 0.6

    def test_no_match_below_threshold(self):
        """Test that no match is returned below threshold."""
        models = ["gpt-4", "claude-3", "llama-2"]
        match, confidence = fuzzy_match_model(
            "completely-different", models, threshold=0.8
        )
        assert match is None
        assert confidence == 0.0

    def test_threshold_adjustment(self):
        """Test threshold adjustment."""
        models = ["gpt-4", "gpt-3"]
        # Low threshold should find a match
        match1, conf1 = fuzzy_match_model("gpt", models, threshold=0.5)
        assert match1 is not None
        # High threshold might not
        match2, conf2 = fuzzy_match_model("xyz", models, threshold=0.9)
        assert match2 is None

    def test_empty_inputs(self):
        """Test empty input handling."""
        assert fuzzy_match_model("", ["gpt-4"]) == (None, 0.0)
        assert fuzzy_match_model("gpt-4", []) == (None, 0.0)
        assert fuzzy_match_model("", []) == (None, 0.0)

    def test_best_match_selection(self):
        """Test that the best match is selected."""
        models = ["gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview"]
        match, confidence = fuzzy_match_model("gpt-4", models)
        assert match == "gpt-4"  # Exact match should win

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        models = ["GPT-4", "gpt-3.5-turbo"]
        match, confidence = fuzzy_match_model("gpt-4", models)
        assert match == "GPT-4"
        assert confidence >= 0.95


class TestModelCharacteristics:
    """Tests for model characteristic inference."""

    def test_reasoning_models(self):
        """Test reasoning model detection."""
        assert infer_model_characteristics("gpt-oss-120b").is_reasoning
        assert infer_model_characteristics("deepseek-ai/DeepSeek-R1").is_reasoning
        assert infer_model_characteristics("o1-preview").is_reasoning
        assert infer_model_characteristics("o3-mini").is_reasoning
        assert not infer_model_characteristics("gpt-4").is_reasoning

    def test_moe_models(self):
        """Test MoE model detection."""
        assert infer_model_characteristics("mixtral-8x7b").is_moe
        assert infer_model_characteristics("gpt-oss-120b").is_moe
        assert infer_model_characteristics("deepseek-v3").is_moe
        assert not infer_model_characteristics("gpt-4").is_moe

    def test_vision_models(self):
        """Test vision model detection."""
        assert infer_model_characteristics("gpt-4o").is_vision
        assert infer_model_characteristics("gpt-4-turbo").is_vision
        assert infer_model_characteristics("claude-3-opus").is_vision
        assert infer_model_characteristics("gemini-pro-vision").is_vision
        assert not infer_model_characteristics("gpt-3.5-turbo").is_vision

    def test_audio_models(self):
        """Test audio model detection."""
        assert infer_model_characteristics("whisper-1").is_audio
        assert infer_model_characteristics("tts-1").is_audio
        assert not infer_model_characteristics("gpt-4").is_audio

    def test_video_models(self):
        """Test video model detection."""
        assert infer_model_characteristics("cosmos-1").is_video
        assert not infer_model_characteristics("gpt-4").is_video

    def test_parameter_size_extraction(self):
        """Test parameter size extraction."""
        assert infer_model_characteristics("gpt-oss-120b").estimated_size == "120b"
        assert infer_model_characteristics("llama-2-7b").estimated_size == "7b"
        assert infer_model_characteristics("llama-3.1-405b").estimated_size == "405b"
        assert infer_model_characteristics("gpt-4").estimated_size is None

    def test_provider_detection(self):
        """Test provider detection."""
        assert infer_model_characteristics("openai/gpt-4").provider == "openai"
        assert infer_model_characteristics("gpt-4").provider == "openai"
        assert infer_model_characteristics("meta/llama-2").provider == "meta"
        assert infer_model_characteristics("anthropic/claude-3").provider == "anthropic"
        assert (
            infer_model_characteristics("deepseek-ai/DeepSeek-R1").provider
            == "deepseek"
        )

    def test_fine_tuned_model(self):
        """Test fine-tuned model detection."""
        chars = infer_model_characteristics("ft:gpt-4:acme::abc123")
        assert chars.is_fine_tuned
        assert chars.base_model == "gpt-4"

    def test_multiple_characteristics(self):
        """Test models with multiple characteristics."""
        chars = infer_model_characteristics("openai/gpt-oss-120b")
        assert chars.is_reasoning
        assert chars.is_moe
        assert chars.estimated_size == "120b"
        assert chars.provider == "openai"

    def test_empty_model_id(self):
        """Test empty model ID."""
        chars = infer_model_characteristics("")
        assert not chars.is_reasoning
        assert not chars.is_moe
        assert chars.provider is None


class TestFineTunedParsing:
    """Tests for fine-tuned model ID parsing."""

    def test_basic_parsing(self):
        """Test basic fine-tuned model parsing."""
        info = parse_fine_tuned_model("ft:gpt-4:acme::abc123")
        assert info is not None
        assert info.base_model == "gpt-4"
        assert info.organization == "acme"
        assert info.job_id == "abc123"
        assert info.full_id == "ft:gpt-4:acme::abc123"

    def test_parsing_with_provider(self):
        """Test parsing with provider prefix in base model."""
        info = parse_fine_tuned_model("ft:openai/gpt-4:acme::abc123")
        assert info is not None
        assert info.base_model == "openai/gpt-4"
        assert info.organization == "acme"
        assert info.job_id == "abc123"

    def test_parsing_complex_base_model(self):
        """Test parsing with complex base model name."""
        info = parse_fine_tuned_model("ft:meta-llama/Llama-3-8B:acme::xyz789")
        assert info is not None
        assert info.base_model == "meta-llama/Llama-3-8B"
        assert info.organization == "acme"
        assert info.job_id == "xyz789"

    def test_invalid_format_no_prefix(self):
        """Test invalid format without ft: prefix."""
        assert parse_fine_tuned_model("gpt-4:acme::abc123") is None

    def test_invalid_format_no_double_colon(self):
        """Test invalid format without double colon."""
        assert parse_fine_tuned_model("ft:gpt-4:acme:abc123") is None

    def test_invalid_format_missing_parts(self):
        """Test invalid format with missing parts."""
        assert parse_fine_tuned_model("ft:gpt-4::abc123") is None
        assert parse_fine_tuned_model("ft:::abc123") is None

    def test_empty_input(self):
        """Test empty input."""
        assert parse_fine_tuned_model("") is None
        assert parse_fine_tuned_model(None) is None

    def test_job_id_with_special_chars(self):
        """Test job ID with special characters."""
        info = parse_fine_tuned_model("ft:gpt-4:acme::abc-123-xyz")
        assert info is not None
        assert info.job_id == "abc-123-xyz"


class TestSimilarModels:
    """Tests for similar model suggestions."""

    def test_basic_suggestions(self):
        """Test basic similar model suggestions."""
        models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3"]
        suggestions = suggest_similar_models("gpt", models, limit=3)
        assert len(suggestions) <= 3
        assert all(isinstance(s, tuple) and len(s) == 2 for s in suggestions)
        # GPT models should be at the top
        assert any("gpt" in s[0].lower() for s in suggestions[:3])

    def test_suggestions_sorted_by_confidence(self):
        """Test that suggestions are sorted by confidence."""
        models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3"]
        suggestions = suggest_similar_models("gpt-4", models, limit=5)
        confidences = [conf for _, conf in suggestions]
        assert confidences == sorted(confidences, reverse=True)

    def test_limit_respected(self):
        """Test that the limit is respected."""
        models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3", "llama-2"]
        suggestions = suggest_similar_models("gpt", models, limit=2)
        assert len(suggestions) == 2

    def test_exact_match_highest(self):
        """Test that exact match has highest confidence."""
        models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        suggestions = suggest_similar_models("gpt-4", models)
        assert suggestions[0][0] == "gpt-4"
        assert suggestions[0][1] == 1.0

    def test_empty_query(self):
        """Test empty query."""
        models = ["gpt-4", "claude-3"]
        suggestions = suggest_similar_models("", models)
        assert suggestions == []

    def test_empty_models(self):
        """Test empty model list."""
        suggestions = suggest_similar_models("gpt-4", [])
        assert suggestions == []

    def test_no_similar_models(self):
        """Test when no models are similar."""
        models = ["completely", "different", "models"]
        suggestions = suggest_similar_models("xyz123", models, limit=3)
        # Should still return results, but with low confidence
        assert len(suggestions) <= 3


class TestModelMatcher:
    """Tests for the learning-based ModelMatcher."""

    def test_basic_matching(self):
        """Test basic matching functionality."""
        matcher = ModelMatcher()
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        result = matcher.match("gpt-4", models)
        assert result is not None
        assert result.matched_model == "gpt-4"
        assert result.confidence == 1.0

    def test_learned_preferences(self):
        """Test that matcher learns from successful matches."""
        matcher = ModelMatcher()
        models = ["gpt-4", "gpt-40"]

        # Record successful match
        matcher.record_success("gpt4", "gpt-4")
        matcher.record_success("gpt4", "gpt-4")

        # Should prefer the learned match
        result = matcher.match("gpt4", models)
        assert result.matched_model == "gpt-4"
        assert result.strategy == "learned"

    def test_learned_boost_confidence(self):
        """Test that learned matches have boosted confidence."""
        matcher = ModelMatcher()
        models = ["gpt-4", "claude-3"]

        # Record multiple successful matches
        for _ in range(5):
            matcher.record_success("gpt", "gpt-4")

        result = matcher.match("gpt", models)
        # Confidence should be boosted by usage
        assert result.confidence > 0.8

    def test_failure_recording(self):
        """Test failure recording."""
        matcher = ModelMatcher()
        matcher.record_failure("gpt4", "wrong-model")
        assert ("gpt4", "wrong-model") in matcher.failed_matches

    def test_match_history(self):
        """Test match history retrieval."""
        matcher = ModelMatcher()
        matcher.record_success("gpt-4", "gpt-4-turbo")
        matcher.record_success("gpt-4", "gpt-4-turbo")
        matcher.record_success("gpt-4", "gpt-4")

        history = matcher.get_match_history("gpt-4")
        assert history["gpt-4-turbo"] == 2
        assert history["gpt-4"] == 1

    def test_popular_models(self):
        """Test popular models tracking."""
        matcher = ModelMatcher()
        matcher.record_success("query1", "gpt-4")
        matcher.record_success("query2", "gpt-4")
        matcher.record_success("query3", "claude-3")

        popular = matcher.get_popular_models(limit=2)
        assert len(popular) == 2
        assert popular[0][0] == "gpt-4"
        assert popular[0][1] == 2
        assert popular[1][0] == "claude-3"
        assert popular[1][1] == 1

    def test_fallback_to_fuzzy(self):
        """Test fallback to fuzzy matching when no learned match."""
        matcher = ModelMatcher()
        models = ["gpt-4", "claude-3"]

        # No learned matches, should use fuzzy
        result = matcher.match("gpt-4", models)
        assert result is not None
        assert result.matched_model == "gpt-4"
        assert result.strategy == "fuzzy"

    def test_threshold_respected(self):
        """Test that threshold is respected."""
        matcher = ModelMatcher()
        models = ["gpt-4", "claude-3"]

        result = matcher.match("completely-different", models, threshold=0.9)
        assert result is None

    def test_multiple_queries_same_model(self):
        """Test that different queries can match to the same model."""
        matcher = ModelMatcher()
        models = ["gpt-4-turbo"]

        matcher.record_success("gpt4", "gpt-4-turbo")
        matcher.record_success("gpt-4", "gpt-4-turbo")

        result1 = matcher.match("gpt4", models)
        result2 = matcher.match("gpt-4", models)

        assert result1.matched_model == "gpt-4-turbo"
        assert result2.matched_model == "gpt-4-turbo"


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_match_result_creation(self):
        """Test MatchResult creation."""
        result = MatchResult(
            matched_model="gpt-4",
            confidence=0.95,
            strategy="normalized",
            normalized_query="gpt4",
            normalized_match="gpt4",
        )
        assert result.matched_model == "gpt-4"
        assert result.confidence == 0.95
        assert result.strategy == "normalized"


class TestEdgeCases:
    """Tests for edge cases and corner scenarios."""

    def test_unicode_model_names(self):
        """Test Unicode characters in model names."""
        models = ["gpt-4", "model-\u4e2d\u6587"]
        match, conf = fuzzy_match_model("gpt-4", models)
        assert match == "gpt-4"

    def test_very_long_model_names(self):
        """Test very long model names."""
        long_name = "very-long-model-name-" * 10 + "final"
        models = [long_name, "gpt-4"]
        match, conf = fuzzy_match_model(long_name, models)
        assert match == long_name
        assert conf == 1.0

    def test_special_characters_in_names(self):
        """Test special characters in model names."""
        models = ["model@v1", "model#v2", "model$v3"]
        normalized = normalize_model_id("model@v1")
        # Should handle without crashing
        assert isinstance(normalized, str)

    def test_numeric_only_model_names(self):
        """Test numeric-only model names."""
        models = ["123", "456", "789"]
        match, conf = fuzzy_match_model("123", models)
        assert match == "123"
        assert conf == 1.0
