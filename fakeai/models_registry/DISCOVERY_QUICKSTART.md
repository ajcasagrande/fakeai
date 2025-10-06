# Model Discovery Quick Start

One-page reference for the model discovery system.

## Installation

No external dependencies required - uses Python standard library only.

```python
from fakeai.models_registry import (
    fuzzy_match_model,
    normalize_model_id,
    infer_model_characteristics,
    parse_fine_tuned_model,
    suggest_similar_models,
    ModelMatcher
)
```

## Basic Usage

### 1. Fuzzy Matching (Most Common)

```python
# Find best match from available models
available = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
match, confidence = fuzzy_match_model("gpt4", available)

if match and confidence >= 0.8:
    print(f"Using model: {match}")
else:
    print("No good match found")
```

### 2. Normalize Model Names

```python
# Standardize model IDs for comparison
normalized = normalize_model_id("OpenAI/GPT-4_Turbo-v2")
# Result: "gpt4turbo"

# Check if two model IDs are equivalent
if normalize_model_id(id1) == normalize_model_id(id2):
    print("Same model")
```

### 3. Detect Model Capabilities

```python
# Auto-detect what a model can do
chars = infer_model_characteristics("openai/gpt-oss-120b")

if chars.is_reasoning:
    print("Supports chain-of-thought reasoning")
if chars.is_moe:
    print(f"Uses MoE architecture ({chars.estimated_size})")
if chars.is_vision:
    print("Supports image inputs")
```

### 4. Parse Fine-Tuned Models

```python
# Extract info from fine-tuned model IDs
info = parse_fine_tuned_model("ft:gpt-4:acme::abc123")

if info:
    print(f"Base: {info.base_model}")
    print(f"Org: {info.organization}")
    print(f"Job: {info.job_id}")
```

### 5. Suggest Alternatives

```python
# "Did you mean?" functionality
suggestions = suggest_similar_models("gtp4", available, limit=3)

print("Did you mean:")
for model, confidence in suggestions:
    print(f"  - {model} ({confidence:.0%})")
```

### 6. Learning-Based Matching

```python
# Matcher that learns from usage
matcher = ModelMatcher()

# Use for matching
result = matcher.match("gpt4", available)
print(f"Matched: {result.matched_model}")

# Record successful matches to improve future matches
matcher.record_success("gpt4", result.matched_model)

# View learning data
history = matcher.get_match_history("gpt4")
popular = matcher.get_popular_models(limit=5)
```

## Common Patterns

### Pattern 1: Model Resolution with Fallback

```python
def resolve_model(query: str, registry: dict) -> str | None:
    """Resolve model with fuzzy matching and suggestions."""
    # Try exact match first
    if query in registry:
        return query

    # Try fuzzy match
    available = list(registry.keys())
    match, conf = fuzzy_match_model(query, available, threshold=0.7)

    if match:
        return match

    # Return suggestions for user
    suggestions = suggest_similar_models(query, available, limit=3)
    raise ValueError(f"Model not found. Did you mean: {[s[0] for s in suggestions]}")
```

### Pattern 2: Auto-Configuration

```python
def configure_model(model_id: str) -> dict:
    """Automatically configure model based on characteristics."""
    chars = infer_model_characteristics(model_id)

    return {
        "id": model_id,
        "capabilities": {
            "reasoning": chars.is_reasoning,
            "vision": chars.is_vision,
            "audio": chars.is_audio,
        },
        "architecture": "moe" if chars.is_moe else "standard",
        "provider": chars.provider,
        "size": chars.estimated_size,
    }
```

### Pattern 3: API Error Handling

```python
async def get_model_or_suggest(model_id: str, available: list[str]):
    """Get model with helpful error messages."""
    match, conf = fuzzy_match_model(model_id, available)

    if match and conf >= 0.9:
        return match

    if match and conf >= 0.6:
        # Suggest correction
        return {
            "warning": f"Using {match} (did you mean this?)",
            "model": match,
            "confidence": conf
        }

    # No good match
    suggestions = suggest_similar_models(model_id, available, limit=3)
    raise HTTPException(
        status_code=404,
        detail={
            "error": f"Model '{model_id}' not found",
            "suggestions": [s[0] for s in suggestions]
        }
    )
```

## Matching Strategies

| Strategy | Confidence | Example |
|----------|-----------|---------|
| Exact | 1.0 | `"gpt-4"` → `"gpt-4"` |
| Normalized | 0.95 | `"OpenAI/GPT-4"` → `"gpt-4"` |
| Substring | 0.80-0.95 | `"gpt-4"` → `"gpt-4-turbo"` |
| Edit Distance | 0.0-1.0 | `"gpt4"` → `"gpt-4"` |

## Detection Patterns

### Reasoning Models
- `gpt-oss`, `deepseek-r1`, `o1`, `o3`
- Example: `"openai/gpt-oss-120b"` → `is_reasoning=True`

### MoE Models
- `mixtral`, `gpt-oss`, `deepseek-v`
- Example: `"mixtral-8x7b"` → `is_moe=True`

### Vision Models
- `vision`, `gpt-4o`, `gpt-4-turbo`, `claude-3`, `gemini`
- Example: `"gpt-4o"` → `is_vision=True`

### Parameter Sizes
- Pattern: `\d+b` (e.g., `7b`, `120b`, `405b`)
- Example: `"llama-2-7b"` → `estimated_size="7b"`

### Providers
- Detected from prefixes: `openai/`, `meta/`, `anthropic/`, etc.
- Or from patterns: `gpt-*`, `claude-*`, `llama-*`
- Example: `"gpt-4"` → `provider="openai"`

## Configuration Options

### Threshold Values

```python
# Strict matching (exact or very close)
fuzzy_match_model(query, models, threshold=0.9)

# Balanced matching (recommended)
fuzzy_match_model(query, models, threshold=0.7)

# Permissive matching (user input)
fuzzy_match_model(query, models, threshold=0.5)
```

### Result Limits

```python
# Top 3 suggestions (quick)
suggest_similar_models(query, models, limit=3)

# Top 10 suggestions (comprehensive)
suggest_similar_models(query, models, limit=10)
```

## Testing

### Run Tests

```bash
# Standalone tests (no dependencies)
python test_discovery_standalone.py

# Full pytest suite
pytest tests/test_model_discovery.py -v

# Quick manual test
python -c "from fakeai.models_registry import fuzzy_match_model; \
print(fuzzy_match_model('gpt4', ['gpt-4', 'claude-3']))"
```

## Performance Tips

1. **Cache normalized IDs** for frequently queried models
2. **Use ModelMatcher** for repeated queries (learning improves speed)
3. **Lower threshold** for user input (more permissive)
4. **Higher threshold** for API validation (more strict)
5. **Limit suggestions** to 3-5 for best UX

## Error Handling

```python
# Always check for None
match, conf = fuzzy_match_model(query, available)
if match is None:
    # Handle no match case
    suggestions = suggest_similar_models(query, available)

# Check confidence
if conf < 0.8:
    # Low confidence - ask user to confirm

# Handle empty inputs
if not query or not available:
    # Return early
```

## Complete Example

```python
from fakeai.models_registry import (
    fuzzy_match_model,
    infer_model_characteristics,
    suggest_similar_models,
    ModelMatcher
)

class SmartModelRegistry:
    def __init__(self):
        self.models = {}
        self.matcher = ModelMatcher()

    def register(self, model_id: str):
        """Auto-register with characteristic detection."""
        chars = infer_model_characteristics(model_id)
        self.models[model_id] = {
            "id": model_id,
            "capabilities": chars,
            "config": self._create_config(chars)
        }

    def get(self, query: str):
        """Get model with fuzzy matching and learning."""
        # Try learned match first
        result = self.matcher.match(query, list(self.models.keys()))

        if result and result.confidence >= 0.7:
            model = self.models[result.matched_model]
            self.matcher.record_success(query, result.matched_model)
            return model

        # No match - suggest alternatives
        suggestions = suggest_similar_models(
            query,
            list(self.models.keys()),
            limit=3
        )
        raise ValueError(
            f"Model '{query}' not found. "
            f"Did you mean: {[s[0] for s in suggestions]}?"
        )

    def _create_config(self, chars):
        return {
            "reasoning": chars.is_reasoning,
            "vision": chars.is_vision,
            "moe": chars.is_moe,
            "provider": chars.provider
        }

# Usage
registry = SmartModelRegistry()
registry.register("openai/gpt-oss-120b")
registry.register("gpt-4o")
registry.register("claude-3-opus")

# Fuzzy match automatically
model = registry.get("gpt4o")  # Finds "gpt-4o"
print(f"Using: {model['id']}")
print(f"Vision: {model['config']['vision']}")
```

## Learn More

- Full examples: `DISCOVERY_EXAMPLES.md`
- Implementation details: `DISCOVERY_IMPLEMENTATION.md`
- API documentation: See docstrings in `discovery.py`
