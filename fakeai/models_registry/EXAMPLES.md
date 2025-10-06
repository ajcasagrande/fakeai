# Model Registry Examples

Comprehensive examples demonstrating Model Registry usage.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Capability Queries](#capability-queries)
3. [Provider Management](#provider-management)
4. [Fuzzy Matching](#fuzzy-matching)
5. [Custom Models](#custom-models)
6. [Fine-Tuned Models](#fine-tuned-models)
7. [MoE Models](#moe-models)
8. [Integration Examples](#integration-examples)

## Basic Usage

### Create and Initialize Registry

```python
from fakeai.models_registry.catalog import create_default_registry

# Create with all providers
registry = create_default_registry()
print(f"Loaded {registry.count()} models")

# Create with specific providers
registry = create_default_registry(providers=["openai", "meta"])

# Create without auto-creation
registry = create_default_registry(auto_create=False)
```

### Get Models

```python
# Get by exact ID
model = registry.get("openai/gpt-oss-120b")
print(model.id)
print(model.description)

# Get with fuzzy matching
model = registry.get("gpt-oss-120b")  # Missing prefix
print(model.id)  # Still finds: openai/gpt-oss-120b

# Get or create (guaranteed to return)
model = registry.get_or_create("my-custom-model")
```

### List Models

```python
# List all models
all_models = registry.list_models()
for model in all_models:
    print(f"{model.id} ({model.owned_by})")

# List model IDs only
model_ids = registry.list_model_ids()
print(f"Available models: {', '.join(model_ids[:5])}...")

# Get registry stats
stats = registry.stats()
print(f"Total models: {stats['total_models']}")
print(f"Capabilities: {stats['capabilities']}")
```

## Capability Queries

### Filter by Single Capability

```python
# Get reasoning models
reasoning_models = registry.list_models(capability="reasoning")
print(f"Found {len(reasoning_models)} reasoning models:")
for model in reasoning_models:
    print(f"  - {model.id}")

# Get vision models
vision_models = registry.list_models(capability="vision")

# Get MoE models
moe_models = registry.list_models(capability="moe")

# Get embeddings models
embedding_models = registry.list_models(capability="embeddings")
```

### Filter by Multiple Criteria

```python
# Vision models from OpenAI
openai_vision = registry.list_models(
    capability="vision",
    owned_by="openai"
)

# Reasoning models with tags
latest_reasoning = registry.list_models(
    capability="reasoning",
    tags=["latest"]
)
```

### Check Model Capabilities

```python
model = registry.get("openai/gpt-oss-120b")

# Check individual capabilities
if model.capabilities.reasoning:
    print("Model supports reasoning")

if model.capabilities.vision:
    print("Model supports vision")

if model.capabilities.tool_calling:
    print("Model supports tool calling")

# Check multimodal
if model.capabilities.supports_multimodal():
    print("Model supports images/audio/video")

# Check advanced features
if model.capabilities.supports_advanced_features():
    print("Model has advanced features")

# Get capabilities as dict
caps_dict = model.capabilities.to_dict()
print(caps_dict)
```

### Get Capabilities Without Model

```python
# Get capabilities by ID
caps = registry.get_capabilities("meta-llama/Llama-3.1-70B-Instruct")
print(f"Chat: {caps['chat']}")
print(f"Tool calling: {caps['tool_calling']}")
```

## Provider Management

### Load Specific Providers

```python
from fakeai.models_registry import ModelRegistry
from fakeai.models_registry.catalog import load_provider_models

# Create empty registry
registry = ModelRegistry()

# Load OpenAI models
count = load_provider_models(registry, "openai")
print(f"Loaded {count} OpenAI models")

# Load multiple providers
count = load_provider_models(registry, ["meta", "anthropic"])
print(f"Loaded {count} models from Meta and Anthropic")

# Load all providers
count = load_provider_models(registry, "all")
```

### Get Provider Models

```python
from fakeai.models_registry.catalog import get_provider_models

# Get without loading into registry
openai_models = get_provider_models("openai")
for model in openai_models:
    print(f"{model.id}: ${model.pricing.input_per_million}/M input tokens")

# Get all models
all_models = get_provider_models("all")
```

### List Models by Owner

```python
# Get all Meta models
meta_models = registry.list_models(owned_by="meta")
print(f"Meta has {len(meta_models)} models")

# Get all Anthropic models
anthropic_models = registry.list_models(owned_by="anthropic")
```

## Fuzzy Matching

### Basic Fuzzy Matching

```python
# Missing prefix
model = registry.get("gpt-oss-120b")
print(model.id)  # openai/gpt-oss-120b

# Different separator
model = registry.get("meta_llama/Llama_3.1_8B")
print(model.id)  # meta-llama/Llama-3.1-8B-Instruct

# Case insensitive
model = registry.get("GPT-OSS-120B")
print(model.id)  # openai/gpt-oss-120b

# Partial match
model = registry.get("llama 8b")
print(model.id)  # meta-llama/Llama-3.1-8B-Instruct
```

### Search

```python
# Search by query
results = registry.search("mixtral moe", limit=5)
for model in results:
    print(f"{model.id}: {model.description}")

# Search with different queries
results = registry.search("reasoning large context")
results = registry.search("vision image")
results = registry.search("embedding small")
```

### Suggestions

```python
from fakeai.models_registry.discovery import suggest_similar_models

# User typed unknown model
user_input = "gpt-5-turbo-super"

suggestions = suggest_similar_models(
    user_input,
    available_models=registry.list_model_ids(),
    max_suggestions=3,
)

print(f"Did you mean:")
for model_id in suggestions:
    print(f"  - {model_id}")
```

### Stateful Matcher

```python
from fakeai.models_registry.discovery import ModelMatcher

# Create matcher (learns from usage)
matcher = ModelMatcher()

# Match queries
candidates = registry.list_model_ids()

model = matcher.match("gpt4", candidates)
print(f"Matched: {model}")

# Same query later uses historical match
model = matcher.match("gpt4", candidates)  # Faster, uses history

# Get popular matches
popular = matcher.get_popular_matches(limit=10)
for query, model, count in popular:
    print(f"{query} -> {model} ({count} times)")

# Clear history
matcher.clear_history()
```

## Custom Models

### Create Custom Model

```python
from fakeai.models_registry.definition import create_model_definition
from fakeai.models import ModelPricing

# Create with preset
model = create_model_definition(
    model_id="myorg/custom-chat-model-v1",
    owned_by="myorg",
    preset="chat",  # Use chat preset
    latency_preset="medium",
    context_window=32768,
    max_output_tokens=4096,
    pricing=ModelPricing(
        input_per_million=0.50,
        output_per_million=1.50
    ),
    training_cutoff="2024-10",
    description="Custom chat model for production",
    tags=["custom", "production", "v1"],
)

# Register in registry
registry.register(model)
```

### Create with Custom Capabilities

```python
from fakeai.models_registry.capabilities import ModelCapabilities, LatencyProfile
from fakeai.models_registry.definition import ModelDefinition

# Custom capabilities
capabilities = ModelCapabilities(
    chat=True,
    vision=True,
    audio=True,
    tool_calling=True,
    structured_outputs=True,
    streaming=True,
    prompt_caching=True,
    supports_logprobs=True,
    supports_temperature=True,
)

# Custom latency profile
latency = LatencyProfile(
    ttft_mean=0.2,
    ttft_std=0.05,
    itl_mean=0.04,
    itl_std=0.01,
    vision_multiplier=1.3,
    audio_multiplier=1.2,
)

# Create model with custom everything
model = ModelDefinition(
    id="myorg/advanced-model",
    name="Advanced Multimodal Model",
    owned_by="myorg",
    capabilities=capabilities,
    latency_profile=latency,
    pricing=ModelPricing(
        input_per_million=2.0,
        output_per_million=6.0,
        cached_input_per_million=0.5,
    ),
    context_window=128000,
    max_output_tokens=16384,
    description="Advanced model with all features",
    tags=["advanced", "multimodal"],
)

registry.register(model)
```

### Custom Auto-Creation Handler

```python
def my_auto_create(model_id: str) -> ModelDefinition:
    """Custom logic for auto-creating models."""
    from fakeai.models_registry.definition import create_model_definition
    from fakeai.models_registry.discovery import infer_model_characteristics

    # Infer from model ID
    chars = infer_model_characteristics(model_id)

    # Choose preset
    if chars["reasoning"]:
        preset, latency = "reasoning", "reasoning"
    elif chars["embedding"]:
        preset, latency = "embeddings", "small"
    elif chars["large"]:
        preset, latency = "chat", "large"
    else:
        preset, latency = "chat", "medium"

    # Free for experimental models
    if "experimental" in model_id.lower():
        pricing = ModelPricing(input_per_million=0.0, output_per_million=0.0)
    else:
        pricing = ModelPricing(input_per_million=1.0, output_per_million=2.0)

    return create_model_definition(
        model_id=model_id,
        owned_by="custom",
        preset=preset,
        latency_preset=latency,
        pricing=pricing,
        description=f"Auto-created {preset} model",
        tags=["auto-created"],
    )

# Register handler
registry.set_auto_create_handler(my_auto_create)

# Now unknown models use custom logic
model = registry.get_or_create("experimental-reasoning-v2")
print(model.description)  # "Auto-created reasoning model"
print(model.pricing.input_per_million)  # 0.0 (free)
```

### Clone and Modify

```python
# Get existing model
base = registry.get("openai/gpt-oss-120b")

# Clone with modifications
variant = base.clone(
    id="openai/gpt-oss-120b-discounted",
    description="Discounted variant for testing",
    pricing=ModelPricing(
        input_per_million=1.0,
        output_per_million=4.0,
    ),
    tags=["discounted", "testing"],
)

registry.register(variant)
```

## Fine-Tuned Models

### Auto-Creation of Fine-Tuned Models

```python
# LoRA format: ft:base-model:org::unique-id
ft_model = registry.get_or_create("ft:openai/gpt-oss-120b:myorg::abc123")

print(ft_model.id)  # ft:openai/gpt-oss-120b:myorg::abc123
print(ft_model.base_model)  # openai/gpt-oss-120b
print(ft_model.owned_by)  # myorg

# Check if fine-tuned
if ft_model.is_fine_tuned():
    print("This is a fine-tuned model")
    base_id = ft_model.get_base_model_id()
    print(f"Based on: {base_id}")
```

### Create Fine-Tuned Model Explicitly

```python
# Get base model
base = registry.get("meta-llama/Llama-3.1-70B-Instruct")

# Create fine-tuned variant
ft_model = base.clone(
    id="ft:meta-llama/Llama-3.1-70B-Instruct:myorg::xyz789",
    base_model=base.id,
    root=base.id,
    parent=base.id,
    owned_by="myorg",
    description="Fine-tuned for customer support",
    tags=["fine-tuned", "customer-support"],
)

registry.register(ft_model)
```

### Parse Fine-Tuned Model ID

```python
from fakeai.models_registry.discovery import parse_lora_model_id

model_id = "ft:openai/gpt-oss-120b:myorg::abc123"
parsed = parse_lora_model_id(model_id)

print(parsed)
# {
#     "base": "openai/gpt-oss-120b",
#     "org": "myorg",
#     "unique_id": "abc123"
# }
```

## MoE Models

### List MoE Models

```python
# Get all MoE models
moe_models = registry.list_models(capability="moe")

for model in moe_models:
    if model.capabilities.moe_config:
        config = model.capabilities.moe_config
        print(f"\n{model.id}:")
        print(f"  Total params: {config.total_params:,}")
        print(f"  Active params: {config.active_params:,}")
        print(f"  Activation ratio: {config.activation_ratio:.1%}")
        print(f"  Experts: {config.num_experts}")
        print(f"  Experts per token: {config.experts_per_token}")
```

### Create MoE Model

```python
from fakeai.models_registry.capabilities import MoEConfig, ModelCapabilities
from fakeai.models_registry.definition import ModelDefinition

# Create MoE configuration
moe_config = MoEConfig(
    total_params=46_700_000_000,  # 46.7B total
    active_params=12_900_000_000,  # 12.9B active
    num_experts=8,
    experts_per_token=2,
    architecture="sparse",
)

# Create capabilities with MoE
capabilities = ModelCapabilities(
    chat=True,
    completion=True,
    tool_calling=True,
    streaming=True,
    moe=True,
    moe_config=moe_config,
)

# Create model
model = ModelDefinition(
    id="myorg/custom-moe-8x6b",
    owned_by="myorg",
    capabilities=capabilities,
    context_window=32768,
    max_output_tokens=4096,
    description="Custom 8-expert MoE model",
    tags=["moe", "efficient"],
)

registry.register(model)

# Access MoE properties
print(f"Expert size: {model.capabilities.moe_config.expert_size_params:,} params")
```

## Integration Examples

### Service Integration

```python
from fakeai.models_registry.catalog import create_default_registry

class FakeAIService:
    def __init__(self, config):
        # Initialize registry
        self.model_registry = create_default_registry()
        self.model_registry.set_auto_create_handler(self._custom_auto_create)

    def _custom_auto_create(self, model_id: str):
        """Custom auto-creation logic."""
        # Your logic here
        pass

    async def create_chat_completion(self, request):
        # Get model
        model = self.model_registry.get_or_create(request.model)

        # Validate endpoint support
        if not model.supports_endpoint("chat"):
            raise ValueError(f"Model {request.model} does not support chat")

        # Check capabilities
        supports_vision = model.capabilities.vision
        supports_tools = model.capabilities.tool_calling
        is_reasoning = model.capabilities.reasoning

        # Generate response based on capabilities
        if is_reasoning:
            response = self._generate_reasoning_response(model, request)
        elif supports_tools and request.tools:
            response = self._generate_tool_response(model, request)
        else:
            response = self._generate_standard_response(model, request)

        return response
```

### API Endpoint Integration

```python
from fastapi import APIRouter, Depends, HTTPException
from fakeai.authentication import verify_api_key

router = APIRouter()

@router.get("/v1/models")
async def list_models(
    capability: str | None = None,
    owned_by: str | None = None,
    api_key: str = Depends(verify_api_key),
):
    """List models with optional filters."""
    models = fakeai_service.model_registry.list_models(
        capability=capability,
        owned_by=owned_by,
    )

    return {
        "object": "list",
        "data": [m.to_openai_model() for m in models]
    }

@router.get("/v1/models/{model_id}")
async def get_model(
    model_id: str,
    detailed: bool = False,
    api_key: str = Depends(verify_api_key),
):
    """Get model details."""
    model = fakeai_service.model_registry.get(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if detailed:
        return model.to_detailed_dict()
    else:
        return model.to_openai_model()

@router.get("/v1/models/{model_id}/capabilities")
async def get_capabilities(
    model_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get model capabilities."""
    caps = fakeai_service.model_registry.get_capabilities(model_id)

    if not caps:
        raise HTTPException(status_code=404, detail="Model not found")

    return caps

@router.get("/v1/models/search")
async def search_models(
    query: str,
    limit: int = 10,
    api_key: str = Depends(verify_api_key),
):
    """Search for models."""
    results = fakeai_service.model_registry.search(query, limit=limit)

    return {
        "object": "list",
        "data": [m.to_openai_model() for m in results]
    }
```

### Pricing Calculation

```python
def calculate_cost(request, response, model):
    """Calculate cost based on model pricing."""
    pricing = model.pricing

    # Input tokens
    input_cost = (response.usage.prompt_tokens / 1_000_000) * pricing.input_per_million

    # Output tokens
    output_cost = (response.usage.completion_tokens / 1_000_000) * pricing.output_per_million

    # Cached input tokens (if supported)
    cached_cost = 0
    if pricing.cached_input_per_million and hasattr(response.usage, "prompt_tokens_details"):
        cached_tokens = response.usage.prompt_tokens_details.get("cached_tokens", 0)
        cached_cost = (cached_tokens / 1_000_000) * pricing.cached_input_per_million

    total_cost = input_cost + output_cost + cached_cost

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "cached_cost": cached_cost,
        "total_cost": total_cost,
        "currency": "USD",
    }
```

### Latency Simulation

```python
import asyncio
import random

async def simulate_latency(model, request):
    """Simulate realistic latency based on model profile."""
    profile = model.latency_profile

    # Determine modifiers
    has_vision = any(
        isinstance(msg.content, list) and
        any(p.get("type") == "image_url" for p in msg.content)
        for msg in request.messages
    )

    modifiers = {
        "vision": has_vision,
        "reasoning": model.capabilities.reasoning,
        "tool_calling": bool(request.tools),
    }

    # Get TTFT
    ttft_mean, ttft_std = profile.get_ttft(modifiers)
    ttft = random.gauss(ttft_mean, ttft_std)
    ttft = max(0.01, ttft)  # Minimum 10ms

    # Wait for TTFT
    await asyncio.sleep(ttft)

    # Get ITL for streaming
    itl_mean, itl_std = profile.get_itl(modifiers)

    return ttft, itl_mean, itl_std
```

## Best Practices

### 1. Always Query Capabilities

```python
# BAD: Parse model ID
if "gpt-oss" in model_id or "o1" in model_id:
    # Generate reasoning

# GOOD: Query capabilities
model = registry.get(model_id)
if model.capabilities.reasoning:
    # Generate reasoning
```

### 2. Use Fuzzy Matching

```python
# Let users type variations
user_input = "gpt4o"  # Missing prefix, different format

# Registry handles it
model = registry.get(user_input, fuzzy=True)
```

### 3. Separate Model Data from Logic

```python
# BAD: Model data in service class
class FakeAIService:
    def __init__(self):
        self.models = {
            "model1": {...},
            "model2": {...},
        }

# GOOD: Registry handles models
class FakeAIService:
    def __init__(self):
        self.model_registry = create_default_registry()
```

### 4. Use Presets

```python
# Don't recreate common configurations
model = create_model_definition(
    model_id="my-model",
    preset="chat",  # Pre-configured chat capabilities
    latency_preset="medium",  # Pre-configured latency
)
```

### 5. Cache Registry

```python
# Create once, reuse
_registry = None

def get_registry():
    global _registry
    if _registry is None:
        _registry = create_default_registry()
    return _registry
```

## Testing Examples

### Unit Tests

```python
import pytest
from fakeai.models_registry.catalog import create_default_registry

def test_registry_initialization():
    registry = create_default_registry()
    assert registry.count() > 0

def test_capability_filtering():
    registry = create_default_registry()
    reasoning = registry.list_models(capability="reasoning")
    assert all(m.capabilities.reasoning for m in reasoning)

def test_fuzzy_matching():
    registry = create_default_registry()
    model = registry.get("gpt-oss-120b")  # No prefix
    assert model is not None
    assert "openai/gpt-oss-120b" in model.id

@pytest.mark.parametrize("model_id,expected_capability", [
    ("openai/gpt-oss-120b", "reasoning"),
    ("text-embedding-3-small", "embeddings"),
    ("anthropic/claude-3-opus-20240229", "vision"),
])
def test_model_capabilities(model_id, expected_capability):
    registry = create_default_registry()
    model = registry.get(model_id)
    caps = model.capabilities.to_dict()
    assert caps[expected_capability] is True
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_service_with_registry():
    service = FakeAIService(AppConfig())

    # Test chat with reasoning model
    request = ChatCompletionRequest(
        model="deepseek-ai/DeepSeek-R1",
        messages=[{"role": "user", "content": "Solve: 2+2"}]
    )

    response = await service.create_chat_completion(request)
    assert response.choices[0].message.content
```

## More Examples

See:
- `/fakeai/models_registry/README.md` - Full API documentation
- `/fakeai/models_registry/MIGRATION.md` - Migration guide
- CLAUDE.md - Updated patterns
