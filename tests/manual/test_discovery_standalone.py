#!/usr/bin/env python3
"""Standalone test script for model discovery module.

This script tests the discovery module without requiring pytest or the full
fakeai package to be properly configured. Useful for quick verification.
"""

import importlib.util
import sys

# Import discovery module directly
spec = importlib.util.spec_from_file_location(
    'discovery',
    '/home/anthony/projects/fakeai/fakeai/models_registry/discovery.py'
)
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)

# Import test functions
fuzzy_match_model = discovery.fuzzy_match_model
normalize_model_id = discovery.normalize_model_id
infer_model_characteristics = discovery.infer_model_characteristics
parse_fine_tuned_model = discovery.parse_fine_tuned_model
suggest_similar_models = discovery.suggest_similar_models
ModelMatcher = discovery.ModelMatcher


def test_fuzzy_matching():
    """Test fuzzy matching functionality."""
    print("Testing fuzzy matching...")

    # Exact match
    match, conf = fuzzy_match_model("gpt-4", ["gpt-4", "gpt-3.5-turbo"])
    assert match == "gpt-4" and conf == 1.0, f"Exact match failed: {match}, {conf}"

    # Normalized match
    match, conf = fuzzy_match_model("GPT-4", ["gpt-4", "gpt-3.5-turbo"])
    assert match == "gpt-4" and conf == 0.95, f"Normalized match failed: {match}, {conf}"

    # Prefix match
    match, conf = fuzzy_match_model("openai/gpt-4", ["gpt-4", "claude-3"])
    assert match == "gpt-4" and conf == 0.95, f"Prefix match failed: {match}, {conf}"

    # Substring match
    match, conf = fuzzy_match_model("gpt-4", ["gpt-4-turbo", "claude-3"])
    assert match == "gpt-4-turbo" and conf >= 0.85, f"Substring match failed: {match}, {conf}"

    # No match
    match, conf = fuzzy_match_model("xyz", ["gpt-4"], threshold=0.9)
    assert match is None and conf == 0.0, f"No match failed: {match}, {conf}"

    print("  ✓ All fuzzy matching tests passed")


def test_normalization():
    """Test model ID normalization."""
    print("Testing normalization...")

    assert normalize_model_id("GPT-4") == "gpt4"
    assert normalize_model_id("openai/gpt-4") == "gpt4"
    assert normalize_model_id("meta-llama/Llama-3-8B") == "llama38b"
    assert normalize_model_id("gpt_4_turbo") == "gpt4turbo"
    assert normalize_model_id("gpt-4-v2") == "gpt4"
    assert normalize_model_id("") == ""

    print("  ✓ All normalization tests passed")


def test_characteristics():
    """Test model characteristic inference."""
    print("Testing characteristic inference...")

    # Reasoning models
    chars = infer_model_characteristics("gpt-oss-120b")
    assert chars.is_reasoning and chars.is_moe and chars.estimated_size == "120b"

    chars = infer_model_characteristics("deepseek-ai/DeepSeek-R1")
    assert chars.is_reasoning and chars.provider == "deepseek"

    # Vision models
    chars = infer_model_characteristics("gpt-4o")
    assert chars.is_vision and chars.provider == "openai"

    chars = infer_model_characteristics("claude-3-opus")
    assert chars.is_vision and chars.provider == "anthropic"

    # MoE models
    chars = infer_model_characteristics("mixtral-8x7b")
    assert chars.is_moe and chars.provider == "mistral"

    # Parameter size
    chars = infer_model_characteristics("llama-2-7b")
    assert chars.estimated_size == "7b"

    # Fine-tuned
    chars = infer_model_characteristics("ft:gpt-4:acme::abc123")
    assert chars.is_fine_tuned and chars.base_model == "gpt-4"

    print("  ✓ All characteristic inference tests passed")


def test_fine_tuned_parsing():
    """Test fine-tuned model parsing."""
    print("Testing fine-tuned parsing...")

    # Basic parsing
    info = parse_fine_tuned_model("ft:gpt-4:acme::abc123")
    assert info.base_model == "gpt-4"
    assert info.organization == "acme"
    assert info.job_id == "abc123"

    # With provider prefix
    info = parse_fine_tuned_model("ft:openai/gpt-4:acme::xyz789")
    assert info.base_model == "openai/gpt-4"
    assert info.organization == "acme"

    # Complex base model
    info = parse_fine_tuned_model("ft:meta-llama/Llama-3-8B:org::id123")
    assert info.base_model == "meta-llama/Llama-3-8B"

    # Invalid formats
    assert parse_fine_tuned_model("gpt-4:acme::abc") is None
    assert parse_fine_tuned_model("ft:gpt-4::abc") is None
    assert parse_fine_tuned_model("") is None

    print("  ✓ All fine-tuned parsing tests passed")


def test_suggestions():
    """Test similar model suggestions."""
    print("Testing similar model suggestions...")

    models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3", "llama-2"]

    # Basic suggestions
    suggestions = suggest_similar_models("gpt", models, limit=3)
    assert len(suggestions) <= 3
    assert all(isinstance(s, tuple) and len(s) == 2 for s in suggestions)

    # Sorted by confidence
    suggestions = suggest_similar_models("gpt-4", models, limit=5)
    confidences = [conf for _, conf in suggestions]
    assert confidences == sorted(confidences, reverse=True)

    # Exact match highest
    assert suggestions[0][0] == "gpt-4"
    assert suggestions[0][1] == 1.0

    # Empty inputs
    assert suggest_similar_models("", models) == []
    assert suggest_similar_models("gpt", []) == []

    print("  ✓ All suggestion tests passed")


def test_model_matcher():
    """Test ModelMatcher class."""
    print("Testing ModelMatcher...")

    matcher = ModelMatcher()
    models = ["gpt-4", "gpt-40", "claude-3"]

    # Basic matching
    result = matcher.match("gpt-4", models)
    assert result.matched_model == "gpt-4"
    assert result.confidence == 1.0

    # Learning
    matcher.record_success("gpt4", "gpt-4")
    matcher.record_success("gpt4", "gpt-4")
    result = matcher.match("gpt4", models)
    assert result.matched_model == "gpt-4"
    assert result.strategy == "learned"
    assert result.confidence >= 0.8

    # Match history
    history = matcher.get_match_history("gpt4")
    assert history["gpt-4"] == 2

    # Popular models
    popular = matcher.get_popular_models(limit=3)
    assert len(popular) > 0
    assert popular[0][0] == "gpt-4"
    assert popular[0][1] == 2

    # Failure recording
    matcher.record_failure("xyz", "wrong-model")
    assert ("xyz", "wrong-model") in matcher.failed_matches

    print("  ✓ All ModelMatcher tests passed")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running Model Discovery Standalone Tests")
    print("="*60 + "\n")

    tests = [
        test_normalization,
        test_fuzzy_matching,
        test_characteristics,
        test_fine_tuned_parsing,
        test_suggestions,
        test_model_matcher,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
