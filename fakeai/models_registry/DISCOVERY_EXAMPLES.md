# Model Discovery System - Usage Examples

This document provides practical examples of using the model discovery and fuzzy matching system.

## Table of Contents
- [Basic Fuzzy Matching](#basic-fuzzy-matching)
- [Model Normalization](#model-normalization)
- [Characteristic Inference](#characteristic-inference)
- [Fine-Tuned Model Parsing](#fine-tuned-model-parsing)
- [Similar Model Suggestions](#similar-model-suggestions)
- [Learning-Based Matching](#learning-based-matching)
- [Integration Patterns](#integration-patterns)

## Basic Fuzzy Matching

### Simple Matching

```python
from fakeai.models_registry.discovery import fuzzy_match_model

available_models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "llama-2"]

# Exact match
match, confidence = fuzzy_match_model("gpt-4", available_models)
print(f"{match}: {confidence}")  # gpt-4: 1.0

# Case-insensitive match
match, confidence = fuzzy_match_model("GPT-4", available_models)
print(f"{match}: {confidence}")  # gpt-4: 0.95

# Prefix removal match
match, confidence = fuzzy_match_model("openai/gpt-4", available_models)
print(f"{match}: {confidence}")  # gpt-4: 0.95
```

### Substring Matching

```python
# Query is substring of available model
match, confidence = fuzzy_match_model("gpt-3", ["gpt-3.5-turbo"])
print(f"{match}: {confidence}")  # gpt-3.5-turbo: ~0.87

# Normalized substring
match, confidence = fuzzy_match_model("gpt35", ["gpt-3.5-turbo"])
print(f"{match}: {confidence}")  # gpt-3.5-turbo: ~0.82
```

### Threshold Control

```python
models = ["gpt-4", "claude-3", "llama-2"]

# Low threshold - more permissive
match, confidence = fuzzy_match_model("gpt", models, threshold=0.5)
print(f"{match}: {confidence}")  # gpt-4: ~0.65

# High threshold - strict matching
match, confidence = fuzzy_match_model("gpt", models, threshold=0.95)
print(f"{match}: {confidence}")  # None: 0.0
```

### No Match Handling

```python
match, confidence = fuzzy_match_model("nonexistent", available_models)

if match is None:
    print("No matching model found")
    # Suggest alternatives
    from fakeai.models_registry.discovery import suggest_similar_models
    suggestions = suggest_similar_models("nonexistent", available_models, limit=3)
    print("Did you mean:", [m for m, _ in suggestions])
```

## Model Normalization

### Basic Normalization

```python
from fakeai.models_registry.discovery import normalize_model_id

# Case normalization
print(normalize_model_id("GPT-4"))  # gpt4
print(normalize_model_id("Claude-3"))  # claude3

# Provider prefix removal
print(normalize_model_id("openai/gpt-4"))  # gpt4
print(normalize_model_id("meta/llama-2"))  # llama2
print(normalize_model_id("anthropic/claude-3"))  # claude3
```

### Separator Standardization

```python
# Different separators normalized to same result
print(normalize_model_id("gpt-4-turbo"))  # gpt4turbo
print(normalize_model_id("gpt_4_turbo"))  # gpt4turbo
print(normalize_model_id("gpt/4/turbo"))  # gpt4turbo
```

### Version Suffix Removal

```python
print(normalize_model_id("gpt-4-v1"))  # gpt4
print(normalize_model_id("gpt-4-v2"))  # gpt4
print(normalize_model_id("claude-3-v10"))  # claude3
```

### Complex Normalization

```python
# All normalize to same result
inputs = [
    "OpenAI/GPT-4_Turbo-v2",
    "openai/gpt-4-turbo-v2",
    "GPT_4_TURBO-V2",
    "gpt/4/turbo/v2"
]

for input_id in inputs:
    print(f"{input_id} -> {normalize_model_id(input_id)}")
    # All output: gpt4turbo
```

## Characteristic Inference

### Reasoning Models

```python
from fakeai.models_registry.discovery import infer_model_characteristics

# GPT-OSS (reasoning + MoE)
chars = infer_model_characteristics("openai/gpt-oss-120b")
print(f"Reasoning: {chars.is_reasoning}")  # True
print(f"MoE: {chars.is_moe}")  # True
print(f"Size: {chars.estimated_size}")  # 120b
print(f"Provider: {chars.provider}")  # openai

# DeepSeek R1 (reasoning)
chars = infer_model_characteristics("deepseek-ai/DeepSeek-R1")
print(f"Reasoning: {chars.is_reasoning}")  # True
print(f"Provider: {chars.provider}")  # deepseek

# O1/O3 models
chars = infer_model_characteristics("o1-preview")
print(f"Reasoning: {chars.is_reasoning}")  # True
```

### Vision Models

```python
# GPT-4 Vision
chars = infer_model_characteristics("gpt-4o")
print(f"Vision: {chars.is_vision}")  # True
print(f"Provider: {chars.provider}")  # openai

# Claude 3 Vision
chars = infer_model_characteristics("claude-3-opus")
print(f"Vision: {chars.is_vision}")  # True
print(f"Provider: {chars.provider}")  # anthropic

# Gemini Vision
chars = infer_model_characteristics("gemini-pro-vision")
print(f"Vision: {chars.is_vision}")  # True
print(f"Provider: {chars.provider}")  # google
```

### MoE Models

```python
# Mixtral
chars = infer_model_characteristics("mixtral-8x7b")
print(f"MoE: {chars.is_moe}")  # True
print(f"Size: {chars.estimated_size}")  # 7b
print(f"Provider: {chars.provider}")  # mistral

# DeepSeek V3
chars = infer_model_characteristics("deepseek-v3")
print(f"MoE: {chars.is_moe}")  # True
print(f"Provider: {chars.provider}")  # deepseek
```

### Fine-Tuned Models

```python
chars = infer_model_characteristics("ft:gpt-4:acme::abc123")
print(f"Fine-tuned: {chars.is_fine_tuned}")  # True
print(f"Base model: {chars.base_model}")  # gpt-4

# Base model characteristics are inferred from base
print(f"Provider: {chars.provider}")  # openai
```

### Multiple Characteristics

```python
# Model with multiple capabilities
chars = infer_model_characteristics("openai/gpt-oss-120b")

if chars.is_reasoning and chars.is_moe:
    print("This model supports reasoning with MoE architecture")
    print(f"Estimated size: {chars.estimated_size}")
    print(f"Provider: {chars.provider}")
```

## Fine-Tuned Model Parsing

### Basic Parsing

```python
from fakeai.models_registry.discovery import parse_fine_tuned_model

# Standard format: ft:base_model:organization::job_id
info = parse_fine_tuned_model("ft:gpt-4:acme::abc123")

print(f"Base model: {info.base_model}")  # gpt-4
print(f"Organization: {info.organization}")  # acme
print(f"Job ID: {info.job_id}")  # abc123
print(f"Full ID: {info.full_id}")  # ft:gpt-4:acme::abc123
```

### With Provider Prefix

```python
info = parse_fine_tuned_model("ft:openai/gpt-4:acme::xyz789")

print(f"Base model: {info.base_model}")  # openai/gpt-4
print(f"Organization: {info.organization}")  # acme
print(f"Job ID: {info.job_id}")  # xyz789
```

### Complex Base Models

```python
# Base model with multiple parts
info = parse_fine_tuned_model("ft:meta-llama/Llama-3-8B:myorg::job123")

print(f"Base model: {info.base_model}")  # meta-llama/Llama-3-8B
print(f"Organization: {info.organization}")  # myorg
```

### Error Handling

```python
# Invalid formats return None
result = parse_fine_tuned_model("not-a-fine-tuned-model")
if result is None:
    print("Not a fine-tuned model")

result = parse_fine_tuned_model("ft:gpt-4::missing-org")
if result is None:
    print("Invalid fine-tuned format")
```

### Integration with Characteristics

```python
# Combine parsing with characteristic inference
model_id = "ft:openai/gpt-oss-120b:acme::abc123"

info = parse_fine_tuned_model(model_id)
if info:
    # Get characteristics of base model
    chars = infer_model_characteristics(info.base_model)
    print(f"Base: {info.base_model}")
    print(f"Reasoning: {chars.is_reasoning}")
    print(f"MoE: {chars.is_moe}")
    print(f"Size: {chars.estimated_size}")
```

## Similar Model Suggestions

### Basic Suggestions

```python
from fakeai.models_registry.discovery import suggest_similar_models

all_models = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "claude-3-opus",
    "claude-3-sonnet",
    "llama-2-7b",
    "llama-2-13b"
]

# Get top 3 suggestions
suggestions = suggest_similar_models("gpt", all_models, limit=3)

for model, confidence in suggestions:
    print(f"{model}: {confidence:.2f}")
# Output:
# gpt-4: 0.93
# gpt-4-turbo: 0.88
# gpt-3.5-turbo: 0.88
```

### Typo Correction

```python
# User made a typo
query = "gtp-4"  # meant "gpt-4"
suggestions = suggest_similar_models(query, all_models, limit=3)

print(f"Did you mean: {suggestions[0][0]}?")  # gpt-4
```

### Family-Based Suggestions

```python
# Find models in same family
query = "claude"
suggestions = suggest_similar_models(query, all_models, limit=5)

print("Claude models:")
for model, conf in suggestions:
    if "claude" in model.lower():
        print(f"  {model} ({conf:.2f})")
```

### Error Recovery

```python
def find_model_or_suggest(query: str, available: list[str]) -> str:
    """Find exact model or suggest alternatives."""
    match, confidence = fuzzy_match_model(query, available)

    if confidence >= 0.95:
        return match

    # Lower confidence - suggest alternatives
    suggestions = suggest_similar_models(query, available, limit=3)
    print(f"Model '{query}' not found. Did you mean:")
    for model, conf in suggestions:
        print(f"  - {model} ({conf:.2f})")

    return suggestions[0][0] if suggestions else None
```

## Learning-Based Matching

### Basic Usage

```python
from fakeai.models_registry.discovery import ModelMatcher

matcher = ModelMatcher()
available_models = ["gpt-4", "gpt-4-turbo", "claude-3"]

# Initial match uses fuzzy matching
result = matcher.match("gpt4", available_models)
print(f"Match: {result.matched_model}")
print(f"Strategy: {result.strategy}")  # fuzzy
print(f"Confidence: {result.confidence:.2f}")
```

### Recording Success

```python
# User confirms this was correct
matcher.record_success("gpt4", "gpt-4")

# Next time, it remembers
result = matcher.match("gpt4", available_models)
print(f"Strategy: {result.strategy}")  # learned
print(f"Confidence: {result.confidence:.2f}")  # higher
```

### Preference Learning

```python
# Record multiple successful matches
matcher.record_success("gpt", "gpt-4-turbo")
matcher.record_success("gpt", "gpt-4-turbo")
matcher.record_success("gpt", "gpt-4")

# Most frequent match is preferred
result = matcher.match("gpt", available_models)
print(f"Preferred: {result.matched_model}")  # gpt-4-turbo (2 votes vs 1)
```

### Match History

```python
# View match history for a query
history = matcher.get_match_history("gpt4")
for model, count in history.items():
    print(f"{model}: {count} times")
```

### Popular Models

```python
# Track most-used models
matcher.record_success("query1", "gpt-4")
matcher.record_success("query2", "gpt-4")
matcher.record_success("query3", "claude-3")

popular = matcher.get_popular_models(limit=5)
for model, count in popular:
    print(f"{model}: {count} uses")
# Output:
# gpt-4: 2 uses
# claude-3: 1 uses
```

### Failure Tracking

```python
# Record when a match fails
matcher.record_failure("gpt5", "gpt-4")

# Check if a match has failed before
if ("gpt5", "gpt-4") in matcher.failed_matches:
    print("This match has failed before")
```

## Integration Patterns

### Model Registry Integration

```python
from fakeai.models_registry.discovery import (
    fuzzy_match_model,
    infer_model_characteristics,
    ModelMatcher
)

class ModelRegistry:
    def __init__(self):
        self.models = {}
        self.matcher = ModelMatcher()

    def get_model(self, query: str):
        """Get model with fuzzy matching and learning."""
        # Try exact match first
        if query in self.models:
            self.matcher.record_success(query, query)
            return self.models[query]

        # Fuzzy match
        available = list(self.models.keys())
        result = self.matcher.match(query, available, threshold=0.7)

        if result:
            self.matcher.record_success(query, result.matched_model)
            return self.models[result.matched_model]

        # No match found
        self.matcher.record_failure(query, None)
        return None

    def register_model(self, model_id: str):
        """Register model with automatic characteristic inference."""
        chars = infer_model_characteristics(model_id)
        self.models[model_id] = {
            "id": model_id,
            "characteristics": chars
        }
```

### Auto-Discovery Pattern

```python
def discover_and_register(model_id: str, registry: ModelRegistry):
    """Automatically discover model characteristics and register."""
    chars = infer_model_characteristics(model_id)

    # Configure based on characteristics
    config = {
        "id": model_id,
        "supports_reasoning": chars.is_reasoning,
        "supports_vision": chars.is_vision,
        "architecture": "moe" if chars.is_moe else "standard",
        "estimated_size": chars.estimated_size,
        "provider": chars.provider
    }

    # Handle fine-tuned models
    if chars.is_fine_tuned and chars.base_model:
        base_chars = infer_model_characteristics(chars.base_model)
        config["base_model"] = chars.base_model
        config["inherits_from"] = base_chars

    registry.register_model(model_id)
    return config
```

### API Endpoint Integration

```python
from fastapi import HTTPException

async def handle_model_request(model_id: str, registry: ModelRegistry):
    """Handle API request with fuzzy matching."""
    # Try to find model
    model = registry.get_model(model_id)

    if model is None:
        # Suggest alternatives
        available = list(registry.models.keys())
        suggestions = suggest_similar_models(model_id, available, limit=3)

        suggestion_list = [m for m, _ in suggestions]
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Model '{model_id}' not found",
                "suggestions": suggestion_list
            }
        )

    return model
```

### Configuration-Based Matching

```python
class MatchConfig:
    def __init__(
        self,
        threshold: float = 0.7,
        enable_learning: bool = True,
        max_suggestions: int = 3
    ):
        self.threshold = threshold
        self.enable_learning = enable_learning
        self.max_suggestions = max_suggestions

def smart_match(query: str, models: list[str], config: MatchConfig):
    """Match with configurable behavior."""
    if config.enable_learning:
        matcher = ModelMatcher()
        result = matcher.match(query, models, threshold=config.threshold)
        if result:
            return result.matched_model
    else:
        match, conf = fuzzy_match_model(query, models, threshold=config.threshold)
        if match:
            return match

    # No match - return suggestions
    suggestions = suggest_similar_models(
        query,
        models,
        limit=config.max_suggestions
    )
    return None, suggestions
```

### Batch Processing

```python
def batch_match_models(queries: list[str], available: list[str]):
    """Match multiple queries efficiently."""
    matcher = ModelMatcher()
    results = []

    for query in queries:
        result = matcher.match(query, available)
        if result:
            results.append({
                "query": query,
                "match": result.matched_model,
                "confidence": result.confidence,
                "strategy": result.strategy
            })
            matcher.record_success(query, result.matched_model)
        else:
            suggestions = suggest_similar_models(query, available, limit=3)
            results.append({
                "query": query,
                "match": None,
                "suggestions": [m for m, _ in suggestions]
            })

    return results
```

## Best Practices

### 1. Always Handle No-Match Cases

```python
match, confidence = fuzzy_match_model(query, available_models)

if match is None:
    # Provide helpful suggestions
    suggestions = suggest_similar_models(query, available_models)
    # Log for analysis
    # Return user-friendly error
```

### 2. Use Appropriate Thresholds

```python
# User input - be permissive
match = fuzzy_match_model(user_input, models, threshold=0.6)

# API validation - be strict
match = fuzzy_match_model(api_model, models, threshold=0.9)
```

### 3. Leverage Learning for Frequent Queries

```python
# Create persistent matcher
matcher = ModelMatcher()

# Record successful matches
if user_confirms_match:
    matcher.record_success(query, matched_model)
```

### 4. Combine Multiple Strategies

```python
def intelligent_match(query: str, available: list[str]):
    # 1. Try exact match
    if query in available:
        return query, 1.0, "exact"

    # 2. Try learned match
    if matcher.has_learned(query):
        return matcher.get_learned(query)

    # 3. Try fuzzy match
    match, conf = fuzzy_match_model(query, available)
    if match and conf >= 0.8:
        return match, conf, "fuzzy"

    # 4. Return suggestions
    suggestions = suggest_similar_models(query, available)
    return None, 0.0, "suggestions", suggestions
```

### 5. Normalize for Comparison, Not Storage

```python
# DO: Normalize for matching
normalized = normalize_model_id(query)
if normalized == normalize_model_id(stored_model):
    return stored_model

# DON'T: Store normalized IDs
# This loses important information
models[normalize_model_id(model_id)] = model  # BAD
```
