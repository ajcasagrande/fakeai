# Model Registry Migration Guide

## Overview

This guide covers migration from the dict-based model system to the new sophisticated Model Registry.

## Architecture Changes

### Before (Dict-Based)

```python
# In FakeAIService.__init__
self.models = {
    "openai/gpt-oss-120b": new_model(...),
    "meta-llama/Llama-3.1-8B-Instruct": new_model(...),
    # ... hundreds of lines
}

# Auto-creation in _ensure_model_exists
if model_id in self.models:
    return
base_permission = next(iter(self.models.values())).permission[0]
self.models[model_id] = Model(...)
```

**Problems:**
- Monolithic initialization code (200+ lines)
- Hard to extend or maintain
- No capability queries
- Mixed concerns (service + model data)
- No provider organization

### After (Registry-Based)

```python
# In FakeAIService.__init__
from fakeai.models_registry.catalog import create_default_registry

self.model_registry = create_default_registry(providers="all", auto_create=True)

# Usage in service methods
model_def = self.model_registry.get_or_create(model_id)
if model_def.capabilities.reasoning:
    # Generate reasoning content
```

**Benefits:**
- Separation of concerns
- Extensible and testable
- Capability-based queries
- Provider organization
- Fuzzy matching built-in

## Migration Steps

### Step 1: Install New Registry System

The registry is already implemented in `fakeai/models_registry/`:

```
fakeai/models_registry/
 __init__.py                  # Public API
 capabilities.py              # ModelCapabilities, LatencyProfile, MoEConfig
 definition.py                # ModelDefinition
 registry.py                  # ModelRegistry
 discovery.py                 # Fuzzy matching, normalization
 catalog/
     __init__.py
     openai.py               # OpenAI models
     anthropic.py            # Claude models
     meta.py                 # Llama models
     nvidia.py               # NVIDIA models
     mistral.py              # Mixtral models
     deepseek.py             # DeepSeek models
     registry_loader.py      # Loading utilities
```

### Step 2: Update FakeAIService Initialization

**Old code** (`fakeai_service.py` lines ~650-950):

```python
def __init__(self, config: AppConfig):
    # ... existing code ...

    # Define helper for creating models
    def new_model(...):
        # ... model creation logic ...

    # Initialize with comprehensive metadata for all models
    self.models = {
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0": new_model(...),
        "meta-llama/Llama-3.1-8B-Instruct": new_model(...),
        # ... 50+ more models ...
    }
```

**New code:**

```python
def __init__(self, config: AppConfig):
    # ... existing code ...

    # Initialize model registry with all providers
    from fakeai.models_registry.catalog import create_default_registry

    self.model_registry = create_default_registry(
        providers="all",  # or ["openai", "meta", "anthropic"]
        auto_create=True  # Still auto-create unknown models
    )

    # Optional: Set custom auto-creation handler
    self.model_registry.set_auto_create_handler(self._create_custom_model)

    # Keep backward compatibility: expose as dict-like interface
    self.models = ModelRegistryAdapter(self.model_registry)
```

### Step 3: Create Backward Compatibility Adapter

To minimize changes to existing code, create an adapter:

```python
class ModelRegistryAdapter:
    """
    Dict-like adapter for ModelRegistry to maintain backward compatibility.

    Allows existing code like `self.models[model_id]` to work unchanged.
    """

    def __init__(self, registry: ModelRegistry):
        self._registry = registry

    def __getitem__(self, model_id: str) -> Model:
        """Get model by ID (dict-like access)."""
        model_def = self._registry.get_or_create(model_id)
        return self._definition_to_model(model_def)

    def __setitem__(self, model_id: str, model: Model):
        """Set model (for backward compatibility)."""
        # Convert Model to ModelDefinition and register
        model_def = self._model_to_definition(model)
        self._registry.register(model_def)

    def __contains__(self, model_id: str) -> bool:
        """Check if model exists."""
        return self._registry.exists(model_id)

    def get(self, model_id: str, default=None):
        """Get model with default."""
        try:
            return self[model_id]
        except KeyError:
            return default

    def values(self):
        """Get all models."""
        models = self._registry.list_models()
        return [self._definition_to_model(m) for m in models]

    def _definition_to_model(self, model_def: ModelDefinition) -> Model:
        """Convert ModelDefinition to legacy Model."""
        from fakeai.models import Model, ModelPermission

        return Model(
            id=model_def.id,
            created=model_def.created,
            owned_by=model_def.owned_by,
            permission=[ModelPermission(
                id=f"modelperm-{model_def.id}",
                created=model_def.created,
                allow_create_engine=False,
                allow_sampling=True,
                allow_logprobs=model_def.capabilities.supports_logprobs,
                allow_search_indices=False,
                allow_view=True,
                allow_fine_tuning=model_def.capabilities.fine_tunable,
                organization="*",
                group=None,
                is_blocking=False,
            )],
            root=model_def.root,
            parent=model_def.parent,
        )

    def _model_to_definition(self, model: Model) -> ModelDefinition:
        """Convert legacy Model to ModelDefinition."""
        from fakeai.models_registry.definition import create_model_definition

        return create_model_definition(
            model_id=model.id,
            owned_by=model.owned_by,
        )
```

### Step 4: Update _ensure_model_exists

**Old code:**

```python
def _ensure_model_exists(self, model_id: str) -> None:
    """Ensure a model exists, creating it if necessary."""
    if model_id in self.models:
        return

    creation_time = int(time.time()) - 10000
    base_permission = next(iter(self.models.values())).permission[0]

    # Determine ownership and lineage based on model ID
    if model_id.startswith("ft:"):
        # LoRA fine-tuned model: ft:base-model:org::unique-id
        parts = model_id.split(":")
        base_model = parts[1] if len(parts) > 1 else None
        org = parts[2] if len(parts) > 2 else "custom"
        owned_by = org if org else "custom"
        root = base_model
        parent = base_model
    else:
        owned_by = "custom"
        root = None
        parent = None

    self.models[model_id] = Model(
        id=model_id,
        created=creation_time,
        owned_by=owned_by,
        permission=[base_permission],
        root=root,
        parent=parent,
    )
```

**New code:**

```python
def _ensure_model_exists(self, model_id: str) -> None:
    """Ensure a model exists, creating it if necessary."""
    # Registry handles this automatically with get_or_create
    self.model_registry.get_or_create(model_id)
```

Or simply remove `_ensure_model_exists` calls and use registry directly:

```python
# Old: Call _ensure_model_exists first, then access
self._ensure_model_exists(request.model)
model = self.models[request.model]

# New: Direct registry access
model_def = self.model_registry.get_or_create(request.model)
```

### Step 5: Update Capability Checks

**Old code:**

```python
def _is_reasoning_model(self, model_id: str) -> bool:
    """Check if model supports reasoning content."""
    return (
        model_id.startswith("gpt-oss") or
        model_id.startswith("deepseek-ai/DeepSeek-R1") or
        "reasoning" in model_id.lower()
    )

def _is_moe_model(self, model_id: str) -> bool:
    """Check if model uses Mixture of Experts architecture."""
    moe_patterns = ["mixtral", "gpt-oss", "deepseek-v3", "deepseek-v", "grok"]
    return any(pattern in model_id.lower() for pattern in moe_patterns)

def _supports_predicted_outputs(self, model_id: str) -> bool:
    """Check if model supports Predicted Outputs / speculative decoding."""
    return model_id.startswith("openai/gpt-oss-120b")
```

**New code:**

```python
def _is_reasoning_model(self, model_id: str) -> bool:
    """Check if model supports reasoning content."""
    model_def = self.model_registry.get(model_id)
    return model_def.capabilities.reasoning if model_def else False

def _is_moe_model(self, model_id: str) -> bool:
    """Check if model uses Mixture of Experts architecture."""
    model_def = self.model_registry.get(model_id)
    return model_def.capabilities.moe if model_def else False

def _supports_predicted_outputs(self, model_id: str) -> bool:
    """Check if model supports Predicted Outputs."""
    model_def = self.model_registry.get(model_id)
    return model_def.capabilities.predicted_outputs if model_def else False
```

### Step 6: Update Models List Endpoint

**Old code** (`app.py`):

```python
@router.get("/v1/models")
async def list_models(api_key: str = Depends(verify_api_key)):
    """List available models."""
    models = [
        {
            "id": model_id,
            "object": "model",
            "created": model.created,
            "owned_by": model.owned_by,
        }
        for model_id, model in fakeai_service.models.items()
    ]
    return {"object": "list", "data": models}
```

**New code:**

```python
@router.get("/v1/models")
async def list_models(
    api_key: str = Depends(verify_api_key),
    capability: str | None = None,
    owned_by: str | None = None,
):
    """List available models with optional filters."""
    model_defs = fakeai_service.model_registry.list_models(
        capability=capability,
        owned_by=owned_by,
    )

    models = [model_def.to_openai_model() for model_def in model_defs]
    return {"object": "list", "data": models}
```

### Step 7: Add New Capability Endpoints

```python
@router.get("/v1/models/{model_id}")
async def get_model(
    model_id: str,
    detailed: bool = False,
    api_key: str = Depends(verify_api_key),
):
    """Get model details with optional detailed view."""
    model_def = fakeai_service.model_registry.get(model_id)

    if not model_def:
        raise HTTPException(status_code=404, detail="Model not found")

    if detailed:
        return model_def.to_detailed_dict()
    else:
        return model_def.to_openai_model()

@router.get("/v1/models/{model_id}/capabilities")
async def get_model_capabilities(
    model_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get model capabilities."""
    capabilities = fakeai_service.model_registry.get_capabilities(model_id)

    if not capabilities:
        raise HTTPException(status_code=404, detail="Model not found")

    return capabilities
```

## Custom Auto-Creation Handler

To maintain custom auto-creation logic:

```python
def _create_custom_model(self, model_id: str) -> ModelDefinition:
    """
    Custom auto-creation handler for unknown models.

    Maintains backward compatibility with existing logic.
    """
    from fakeai.models_registry.definition import create_model_definition
    from fakeai.models_registry.discovery import (
        extract_base_model_from_ft,
        infer_model_characteristics,
    )

    # Handle fine-tuned models
    if model_id.startswith("ft:"):
        base_model = extract_base_model_from_ft(model_id)
        parts = model_id.split(":")
        org = parts[2] if len(parts) > 2 else "custom"

        # Try to get base model capabilities
        base_def = self.model_registry.get(base_model, fuzzy=False)
        if base_def:
            # Clone base model with fine-tuned ID
            return base_def.clone(
                id=model_id,
                base_model=base_model,
                root=base_model,
                parent=base_model,
                owned_by=org,
            )

    # Infer characteristics from model ID
    characteristics = infer_model_characteristics(model_id)

    # Choose preset based on characteristics
    if characteristics["reasoning"]:
        preset = "reasoning"
        latency = "reasoning"
    elif characteristics["embedding"]:
        preset = "embeddings"
        latency = "small"
    elif characteristics["large"]:
        preset = "chat"
        latency = "large"
    else:
        preset = "chat"
        latency = "medium"

    return create_model_definition(
        model_id=model_id,
        owned_by="custom",
        preset=preset,
        latency_preset=latency,
    )

# Register handler in __init__
self.model_registry.set_auto_create_handler(self._create_custom_model)
```

## Testing Migration

### Unit Tests

```python
import pytest
from fakeai.models_registry import ModelRegistry
from fakeai.models_registry.catalog import create_default_registry

def test_registry_initialization():
    """Test registry initializes with all models."""
    registry = create_default_registry()
    assert registry.count() > 0
    assert "openai/gpt-oss-120b" in registry

def test_model_capabilities():
    """Test capability queries."""
    registry = create_default_registry()

    # Get reasoning models
    reasoning_models = registry.list_models(capability="reasoning")
    assert len(reasoning_models) > 0
    assert all(m.capabilities.reasoning for m in reasoning_models)

def test_fuzzy_matching():
    """Test fuzzy model matching."""
    registry = create_default_registry()

    # Try variations
    model = registry.get("gpt-oss-120b")  # Without prefix
    assert model is not None
    assert "openai/gpt-oss-120b" in model.id

def test_auto_creation():
    """Test auto-creation of unknown models."""
    registry = create_default_registry(auto_create=True)

    model = registry.get_or_create("custom-model-xyz")
    assert model is not None
    assert model.id == "custom-model-xyz"

def test_backward_compatibility():
    """Test adapter maintains backward compatibility."""
    registry = create_default_registry()
    adapter = ModelRegistryAdapter(registry)

    # Dict-like access
    model = adapter["openai/gpt-oss-120b"]
    assert model.id == "openai/gpt-oss-120b"

    # Contains check
    assert "openai/gpt-oss-120b" in adapter
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_service_with_registry():
    """Test FakeAIService with new registry."""
    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Test registry is initialized
    assert service.model_registry.count() > 0

    # Test chat completion with registry
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Hello"}],
    )

    response = await service.create_chat_completion(request)
    assert response.model == "openai/gpt-oss-120b"
    assert len(response.choices) > 0
```

## Rollback Plan

If issues arise, rollback is simple:

1. Revert `fakeai_service.py` changes
2. Remove registry imports
3. Keep old dict-based initialization

The registry is isolated in `fakeai/models_registry/` so removal is clean.

## Performance Considerations

### Memory Usage

**Before:** Models stored as dict (~100 models × ~1KB = 100KB)

**After:** ModelRegistry with same models (~100 models × ~2KB = 200KB)

Increase is negligible (<1MB even with 500+ models).

### Lookup Performance

| Operation | Before (Dict) | After (Registry) |
|-----------|---------------|------------------|
| Exact match | O(1) | O(1) |
| Fuzzy match | N/A | O(n) |
| Capability query | O(n) | O(1) with index |
| List all | O(n) | O(n) |

Registry adds ~0.01ms overhead per lookup (negligible).

## Benefits Summary

1. **Separation of Concerns**
   - Model data → `models_registry/catalog/`
   - Service logic → `fakeai_service.py`
   - Clear boundaries

2. **Extensibility**
   - Add new providers: Create new catalog file
   - Add capabilities: Extend `ModelCapabilities`
   - Add features: Extend `ModelDefinition`

3. **Testability**
   - Registry can be tested independently
   - Mock different model configurations
   - Test capability queries

4. **Maintainability**
   - Provider-specific files (50-100 lines each)
   - vs. monolithic dict (300+ lines)
   - Easy to find and update models

5. **Features**
   - Fuzzy matching
   - Capability-based filtering
   - Detailed model metadata
   - Pricing information
   - Latency profiles

## Migration Checklist

- [ ] Add `models_registry/` module
- [ ] Update `FakeAIService.__init__` to use registry
- [ ] Create `ModelRegistryAdapter` for backward compatibility
- [ ] Update `_ensure_model_exists` to use registry
- [ ] Update capability check methods to query registry
- [ ] Update `/v1/models` endpoint to use registry
- [ ] Add new capability endpoints
- [ ] Write unit tests for registry
- [ ] Write integration tests for service
- [ ] Update CLAUDE.md with new patterns
- [ ] Document custom auto-creation handlers

## Timeline

- **Phase 1 (Week 1):** Core registry implementation
- **Phase 2 (Week 2):** Catalog population + adapter
- **Phase 3 (Week 3):** FakeAIService integration
- **Phase 4 (Week 4):** Testing + documentation
- **Phase 5 (Week 5):** Production deployment

## Questions?

See:
- `/fakeai/models_registry/README.md` - Architecture details
- `/fakeai/models_registry/EXAMPLES.md` - Usage examples
- CLAUDE.md - Updated patterns
