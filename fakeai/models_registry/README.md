# FakeAI Model Registry

Sophisticated model registry system for FakeAI with capabilities, pricing, latency profiles, and intelligent discovery.

## Overview

The Model Registry provides:

- **Centralized Model Management**: Single source of truth for all models
- **Capability System**: Query models by features (vision, reasoning, MoE, etc.)
- **Provider Organization**: Models organized by provider (OpenAI, Meta, Anthropic, etc.)
- **Fuzzy Matching**: Intelligent matching for model IDs with typos/variations
- **Auto-Creation**: Automatically create unknown models on-demand
- **Performance Profiles**: Realistic latency and pricing simulation
- **Type Safety**: Full Pydantic validation and type hints

## Architecture

```
fakeai/models_registry/
 __init__.py              # Public API
 capabilities.py          # Capability system
 definition.py            # Model definitions
 registry.py              # Registry implementation
 discovery.py             # Fuzzy matching & discovery
 catalog/                 # Pre-defined models by provider
     openai.py
     anthropic.py
     meta.py
     nvidia.py
     mistral.py
     deepseek.py
     registry_loader.py
```

## Quick Start

### Basic Usage

```python
from fakeai.models_registry import ModelRegistry
from fakeai.models_registry.catalog import create_default_registry

# Create registry with all models
registry = create_default_registry()

# Get a model
model = registry.get("openai/gpt-oss-120b")
print(model.id)  # openai/gpt-oss-120b
print(model.capabilities.reasoning)  # True
print(model.capabilities.vision)  # True

# Check capabilities
if model.capabilities.tool_calling:
    print("Model supports tool calling")

# Get pricing
print(f"${model.pricing.input_per_million} per 1M input tokens")
```

### Fuzzy Matching

```python
# Typo in model ID
model = registry.get("gpt-oss-120b")  # Missing "openai/" prefix
# Still finds: openai/gpt-oss-120b

# Different separator
model = registry.get("meta_llama/Llama_3.1_8B")
# Finds: meta-llama/Llama-3.1-8B-Instruct
```

### Capability Queries

```python
# Get all reasoning models
reasoning_models = registry.list_models(capability="reasoning")
for model in reasoning_models:
    print(f"{model.id}: {model.description}")

# Get all vision models from OpenAI
vision_models = registry.list_models(
    capability="vision",
    owned_by="openai"
)

# Get all MoE models
moe_models = registry.list_models(capability="moe")
for model in moe_models:
    if model.capabilities.moe_config:
        config = model.capabilities.moe_config
        print(f"{model.id}: {config.total_params:,} params, {config.num_experts} experts")
```

### Search

```python
# Search by query
results = registry.search("llama reasoning", limit=5)
for model in results:
    print(model.id)

# Tag-based filtering
models_with_tags = registry.list_models(tags=["reasoning", "latest"])
```

## Core Components

### ModelDefinition

Complete specification of a model:

```python
from fakeai.models_registry.definition import ModelDefinition, create_model_definition
from fakeai.models import ModelPricing

# Create a model definition
model = create_model_definition(
    model_id="my-custom-model",
    owned_by="myorg",
    preset="chat",  # base, chat, vision, multimodal, reasoning, embeddings
    latency_preset="medium",  # small, medium, large, xlarge, reasoning
    context_window=32768,
    max_output_tokens=8192,
    pricing=ModelPricing(input_per_million=1.0, output_per_million=2.0),
    training_cutoff="2024-01",
    description="My custom chat model",
    tags=["custom", "experimental"],
)

# Access properties
print(model.id)
print(model.capabilities.to_dict())
print(model.latency_profile.ttft_mean)

# Check endpoints
if model.supports_endpoint("chat"):
    print("Supports chat completions")

# Convert to API format
api_format = model.to_openai_model()
detailed = model.to_detailed_dict()
```

### ModelCapabilities

Defines what features a model supports:

```python
from fakeai.models_registry.capabilities import ModelCapabilities, MoEConfig

# Create capabilities
caps = ModelCapabilities(
    chat=True,
    completion=True,
    vision=True,
    tool_calling=True,
    reasoning=False,
    streaming=True,
    moe=True,
    moe_config=MoEConfig(
        total_params=46_700_000_000,
        active_params=12_900_000_000,
        num_experts=8,
        experts_per_token=2,
    ),
    supports_logprobs=True,
    supports_temperature=True,
)

# Check capabilities
if caps.supports_multimodal():
    print("Model supports images/audio/video")

if caps.supports_advanced_features():
    print("Model has advanced features")

# Get as dict
caps_dict = caps.to_dict()
```

### LatencyProfile

Realistic latency simulation:

```python
from fakeai.models_registry.capabilities import LatencyProfile

# Create profile
latency = LatencyProfile(
    ttft_mean=0.3,  # Time to first token (seconds)
    ttft_std=0.1,
    itl_mean=0.05,  # Inter-token latency (seconds)
    itl_std=0.02,
    vision_multiplier=1.5,
    reasoning_multiplier=2.5,
)

# Get latency with modifiers
ttft_mean, ttft_std = latency.get_ttft({"vision": True, "reasoning": True})
# Returns: (0.3 * 1.5 * 2.5, 0.1 * 1.5 * 2.5)

itl_mean, itl_std = latency.get_itl({"reasoning": True})
# Returns: (0.05 * 2.5, 0.02 * 2.5)
```

### ModelRegistry

Central registry with thread-safe operations:

```python
from fakeai.models_registry import ModelRegistry

# Create empty registry
registry = ModelRegistry(auto_create=True)

# Register a model
registry.register(model)

# Register multiple models
registry.register_bulk([model1, model2, model3])

# Get model (with fuzzy matching)
model = registry.get("gpt-oss-120b", fuzzy=True)

# Get or create (guaranteed to return model)
model = registry.get_or_create("custom-model-123")

# Check existence
if "openai/gpt-oss-120b" in registry:
    print("Model exists")

# List models
all_models = registry.list_models()
reasoning = registry.list_models(capability="reasoning")
openai_models = registry.list_models(owned_by="openai")

# List model IDs only
model_ids = registry.list_model_ids(capability="chat")

# Search
results = registry.search("mixtral moe")

# Get capabilities
caps = registry.get_capabilities("openai/gpt-oss-120b")

# Remove model
registry.remove("old-model")

# Get stats
stats = registry.stats()
print(stats)
# {
#     "total_models": 50,
#     "total_aliases": 15,
#     "auto_create": True,
#     "capabilities": {
#         "chat": 45,
#         "reasoning": 5,
#         "vision": 10,
#         ...
#     }
# }
```

## Provider Catalogs

Pre-defined models organized by provider:

### OpenAI

```python
from fakeai.models_registry.catalog.openai import OPENAI_MODELS

# Includes:
# - GPT-OSS models (120B, 20B) with reasoning and MoE
# - GPT-4 family (gpt-4, openai/gpt-oss-120b, openai/gpt-oss-120b)
# - GPT-3.5 family
# - O1 reasoning models
# - Embeddings (text-embedding-3-small/large, ada-002)
# - Moderation (text-moderation-stable/latest)
```

### Anthropic (Claude)

```python
from fakeai.models_registry.catalog.anthropic import ANTHROPIC_MODELS

# Includes:
# - Claude 3.5 Sonnet
# - Claude 3 Opus, Sonnet, Haiku
# - Claude 2.1
```

### Meta (Llama)

```python
from fakeai.models_registry.catalog.meta import META_MODELS

# Includes:
# - Llama 3.1 (405B, 70B, 8B)
# - Llama 3 (70B, 8B)
# - Llama 2 (70B, 13B, 7B)
```

### Mistral

```python
from fakeai.models_registry.catalog.mistral import MISTRAL_MODELS

# Includes:
# - Mixtral 8x22B, 8x7B (MoE)
# - Mistral 7B
# - Mistral Small/Medium/Large
```

### DeepSeek

```python
from fakeai.models_registry.catalog.deepseek import DEEPSEEK_MODELS

# Includes:
# - DeepSeek V3 (671B MoE)
# - DeepSeek-R1 (reasoning)
# - DeepSeek-R1-Distill
# - DeepSeek Coder
```

### NVIDIA

```python
from fakeai.models_registry.catalog.nvidia import NVIDIA_MODELS

# Includes:
# - Cosmos Vision (video support)
# - NeMo Megatron
# - Reranking models
```

## Loading Models

### Load All Models

```python
from fakeai.models_registry.catalog import create_default_registry

# Load everything
registry = create_default_registry(providers="all")
```

### Load Specific Providers

```python
from fakeai.models_registry import ModelRegistry
from fakeai.models_registry.catalog import load_provider_models

registry = ModelRegistry()

# Load only OpenAI models
load_provider_models(registry, "openai")

# Load multiple providers
load_provider_models(registry, ["openai", "meta", "anthropic"])
```

### Lazy Loading

```python
from fakeai.models_registry.catalog import get_provider_models

# Get models without loading into registry
openai_models = get_provider_models("openai")
for model in openai_models:
    print(model.id)
```

## Discovery & Fuzzy Matching

### Normalization

```python
from fakeai.models_registry.discovery import normalize_model_id

# Remove prefixes, standardize separators
normalized = normalize_model_id("openai/gpt-oss-120b")
# Returns: "gpt-oss-120b"

normalized = normalize_model_id("meta_llama/Llama_3.1_8B")
# Returns: "llama-3-1-8b"
```

### Fuzzy Matching

```python
from fakeai.models_registry.discovery import fuzzy_match_model

candidates = ["openai/gpt-oss-120b", "meta-llama/Llama-3.1-8B-Instruct"]

# Find matches
matches = fuzzy_match_model("gpt4o", candidates, threshold=0.6)
# Returns: ["openai/gpt-oss-120b"]

# Multiple strategies:
# 1. Exact match (case-insensitive)
# 2. Normalized match
# 3. Substring match
# 4. Edit distance (Levenshtein)
```

### Model Characteristics Inference

```python
from fakeai.models_registry.discovery import infer_model_characteristics

chars = infer_model_characteristics("mixtral-8x7b-instruct")
# Returns:
# {
#     "reasoning": False,
#     "vision": False,
#     "moe": True,
#     "fine_tuned": False,
#     "embedding": False,
#     "audio": False,
#     "small": False,
#     "large": False,
# }
```

### Suggestions

```python
from fakeai.models_registry.discovery import suggest_similar_models

suggestions = suggest_similar_models(
    "gpt-5-super",
    available_models=["openai/gpt-oss-120b", "openai/gpt-oss-120b"],
    max_suggestions=3,
)
# Returns similar models based on name and characteristics
```

### Categorization

```python
from fakeai.models_registry.discovery import categorize_model

category = categorize_model("text-embedding-3-small")
# Returns: "embedding"

category = categorize_model("openai/gpt-oss-120b")
# Returns: "chat"

category = categorize_model("deepseek-ai/DeepSeek-R1")
# Returns: "reasoning"
```

## Advanced Usage

### Custom Auto-Creation

```python
def custom_auto_create(model_id: str) -> ModelDefinition:
    """Custom logic for creating unknown models."""
    from fakeai.models_registry.definition import create_model_definition

    # Add custom logic
    if "experimental" in model_id:
        preset = "chat"
        pricing = ModelPricing(input_per_million=0.0, output_per_million=0.0)
    else:
        preset = "base"
        pricing = ModelPricing(input_per_million=1.0, output_per_million=2.0)

    return create_model_definition(
        model_id=model_id,
        preset=preset,
        pricing=pricing,
    )

# Register handler
registry.set_auto_create_handler(custom_auto_create)

# Now auto-created models use custom logic
model = registry.get_or_create("experimental-gpt-100b")
```

### Fine-Tuned Models

```python
# LoRA format: ft:base-model:org::unique-id
model = registry.get("ft:openai/gpt-oss-120b:myorg::abc123")

# Check if fine-tuned
if model.is_fine_tuned():
    base_id = model.get_base_model_id()
    print(f"Based on: {base_id}")

# Get base model
base_model = registry.get(model.base_model)
```

### Stateful Matcher

```python
from fakeai.models_registry.discovery import ModelMatcher

# Matcher with learning
matcher = ModelMatcher()

# Match queries (learns over time)
matched = matcher.match("gpt4", ["openai/gpt-oss-120b", "openai/gpt-oss-120b"])
# Future queries for "gpt4" will use historical match

# Get popular matches
popular = matcher.get_popular_matches(limit=10)
for query, model, count in popular:
    print(f"{query} -> {model} ({count} times)")
```

### Model Cloning

```python
# Clone with modifications
base_model = registry.get("openai/gpt-oss-120b")

custom_model = base_model.clone(
    id="openai/gpt-oss-120b-custom",
    description="Custom variant with lower pricing",
    pricing=ModelPricing(input_per_million=1.0, output_per_million=3.0),
)

registry.register(custom_model)
```

## Integration with FakeAIService

```python
from fakeai.config import AppConfig
from fakeai.models_registry.catalog import create_default_registry

class FakeAIService:
    def __init__(self, config: AppConfig):
        # Initialize registry
        self.model_registry = create_default_registry()
        self.model_registry.set_auto_create_handler(self._create_custom_model)

    async def create_chat_completion(self, request):
        # Get model definition
        model_def = self.model_registry.get_or_create(request.model)

        # Check capabilities
        if not model_def.capabilities.chat:
            raise ValueError(f"Model {request.model} does not support chat")

        # Use capabilities
        if model_def.capabilities.reasoning:
            # Generate reasoning content
            pass

        if model_def.capabilities.tool_calling and request.tools:
            # Handle tool calls
            pass

        # Use latency profile for realistic delays
        ttft_mean, ttft_std = model_def.latency_profile.get_ttft({
            "vision": has_vision_input,
            "reasoning": model_def.capabilities.reasoning,
        })

        # Track pricing
        cost = calculate_cost(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            pricing=model_def.pricing,
        )

        return response
```

## Best Practices

1. **Use Capability Queries**: Don't parse model IDs, query capabilities
2. **Leverage Fuzzy Matching**: Let users type variations, registry handles it
3. **Register Custom Handler**: Implement your own auto-creation logic
4. **Separate Concerns**: Keep model data in registry, service logic in service
5. **Use Presets**: Start with presets, override only what you need
6. **Cache Registry**: Create once, reuse across requests
7. **Test Capabilities**: Write tests that query capabilities, not IDs

## Performance

| Operation | Complexity | Typical Time |
|-----------|------------|--------------|
| Get by ID (exact) | O(1) | <0.01ms |
| Get by ID (fuzzy) | O(n) | ~0.1ms (100 models) |
| List all | O(n) | ~0.5ms (100 models) |
| Capability query | O(1) | <0.01ms (indexed) |
| Search | O(n) | ~1ms (100 models) |
| Register | O(1) | <0.01ms |
| Register bulk | O(n) | ~0.5ms (100 models) |

Memory: ~2KB per model (~200KB for 100 models)

## Examples

See `/fakeai/models_registry/EXAMPLES.md` for comprehensive examples.

## Migration

See `/fakeai/models_registry/MIGRATION.md` for migration from dict-based system.

## Contributing

To add a new model:

1. Edit appropriate catalog file (`catalog/openai.py`, etc.)
2. Create `ModelDefinition` with correct capabilities
3. Test with registry

To add a new provider:

1. Create `catalog/newprovider.py`
2. Define models list
3. Add to `catalog/__init__.py` and `registry_loader.py`

## License

Part of FakeAI project.
