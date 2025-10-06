#!/usr/bin/env python
"""
Standalone test script for model registry core functionality.
Bypasses fakeai package __init__ to avoid import errors.
"""

import sys
import os

# Add the fakeai directory to path directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fakeai'))

# Import registry modules directly
from models_registry import (
    ModelCapabilities,
    LatencyProfile,
    MoEConfig,
    CAPABILITY_PRESETS,
    LATENCY_PRESETS,
    ModelDefinition,
    create_model_definition,
    ModelRegistry,
)

def test_basic_functionality():
    """Test basic registry functionality."""
    print("Testing basic registry functionality...")

    # Create registry
    registry = ModelRegistry()
    assert len(registry) == 0, "Empty registry should have length 0"

    # Register model
    definition = registry.register("test-model", preset="chat")
    assert definition.model_id == "test-model"
    assert len(registry) == 1

    # Get model
    retrieved = registry.get("test-model")
    assert retrieved is not None
    assert retrieved.model_id == "test-model"

    # Check capabilities
    assert retrieved.capabilities.supports_chat is True
    assert retrieved.capabilities.supports_function_calling is True

    print("✓ Basic functionality works")

def test_capabilities():
    """Test capability system."""
    print("Testing capability system...")

    # Test presets
    assert 'chat' in CAPABILITY_PRESETS
    assert 'vision' in CAPABILITY_PRESETS
    assert 'reasoning' in CAPABILITY_PRESETS

    # Test capability queries
    caps = CAPABILITY_PRESETS['vision']
    assert caps.supports_vision is True
    assert caps.has_capability('vision') is True
    assert caps.has_capability('embeddings') is False

    # Test supported capabilities
    supported = caps.get_supported_capabilities()
    assert 'vision' in supported
    assert 'chat' in supported

    print("✓ Capability system works")

def test_moe_config():
    """Test MoE configuration."""
    print("Testing MoE configuration...")

    moe = MoEConfig(
        total_params=671_000_000_000,
        active_params=37_000_000_000,
        num_experts=256,
        experts_per_token=8,
    )

    caps = ModelCapabilities(
        is_moe=True,
        moe_config=moe,
    )

    assert caps.is_moe is True
    assert caps.moe_config.num_experts == 256

    print("✓ MoE configuration works")

def test_latency_profiles():
    """Test latency profiles."""
    print("Testing latency profiles...")

    assert 'small' in LATENCY_PRESETS
    assert 'reasoning' in LATENCY_PRESETS

    small = LATENCY_PRESETS['small']
    assert small.tokens_per_second > 50.0

    reasoning = LATENCY_PRESETS['reasoning']
    assert reasoning.tokens_per_second < 20.0

    print("✓ Latency profiles work")

def test_model_definition():
    """Test model definition."""
    print("Testing model definition...")

    definition = create_model_definition(
        model_id="test-model",
        preset="vision",
        owned_by="test-org",
        description="Test vision model",
    )

    assert definition.model_id == "test-model"
    assert definition.owned_by == "test-org"
    assert definition.capabilities.supports_vision is True

    # Test conversion to OpenAI format
    openai_model = definition.to_openai_model()
    assert openai_model["id"] == "test-model"
    assert openai_model["object"] == "model"
    assert openai_model["owned_by"] == "test-org"

    # Test to_dict
    data = definition.to_dict()
    assert data["model_id"] == "test-model"
    assert data["capabilities"]["supports_vision"] is True

    print("✓ Model definition works")

def test_registry_queries():
    """Test registry query features."""
    print("Testing registry queries...")

    registry = ModelRegistry()

    # Register multiple models
    registry.register("chat-model", preset="chat")
    registry.register("vision-model", preset="vision")
    registry.register("reasoning-model", preset="reasoning")
    registry.register("embeddings-model", preset="embeddings")

    # Test list_models
    all_models = registry.list_models()
    assert len(all_models) == 4

    # Test capability queries
    vision_models = registry.list_by_capability("vision")
    assert len(vision_models) == 1
    assert vision_models[0].model_id == "vision-model"

    reasoning_models = registry.list_by_capability("reasoning")
    assert len(reasoning_models) == 1

    # Test stats
    stats = registry.get_stats()
    assert stats["total_models"] == 4
    assert stats["capabilities"]["vision"] == 1
    assert stats["capabilities"]["reasoning"] == 1

    print("✓ Registry queries work")

def test_dict_interface():
    """Test dict-like interface."""
    print("Testing dict-like interface...")

    registry = ModelRegistry()
    registry.register("model-1", preset="base")
    registry.register("model-2", preset="chat")

    # Test __contains__
    assert "model-1" in registry
    assert "nonexistent" not in registry

    # Test __getitem__
    definition = registry["model-1"]
    assert definition.model_id == "model-1"

    # Test __len__
    assert len(registry) == 2

    # Test __iter__
    model_ids = list(registry)
    assert "model-1" in model_ids
    assert "model-2" in model_ids

    # Test keys, values, items
    keys = registry.keys()
    assert len(keys) == 2

    values = registry.values()
    assert len(values) == 2

    items = registry.items()
    assert len(items) == 2

    print("✓ Dict interface works")

def test_auto_creation():
    """Test auto-creation handler."""
    print("Testing auto-creation handler...")

    registry = ModelRegistry()

    # Define custom handler
    def custom_handler(model_id: str):
        if model_id.startswith("custom-"):
            return create_model_definition(
                model_id=model_id,
                preset="chat",
                owned_by="custom-org",
            )
        return None

    registry.set_auto_creation_handler(custom_handler)

    # Test auto-creation
    definition = registry.get_or_create("custom-model-123")
    assert definition.owned_by == "custom-org"

    # Test fallback
    definition2 = registry.get_or_create("regular-model")
    assert definition2.owned_by == "system"

    print("✓ Auto-creation works")

def test_fine_tuned_models():
    """Test fine-tuned model support."""
    print("Testing fine-tuned models...")

    # Create fine-tuned model
    ft_model = create_model_definition(
        model_id="ft:gpt-4:org::abc123",
        preset="chat",
    )

    assert ft_model.is_fine_tuned() is True
    assert ft_model.get_base_model() == "gpt-4"

    # Create regular model
    base_model = create_model_definition(
        model_id="gpt-4",
        preset="chat",
    )

    assert base_model.is_fine_tuned() is False
    assert base_model.get_base_model() == "gpt-4"

    print("✓ Fine-tuned models work")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Model Registry Core Tests")
    print("=" * 60)
    print()

    try:
        test_basic_functionality()
        test_capabilities()
        test_moe_config()
        test_latency_profiles()
        test_model_definition()
        test_registry_queries()
        test_dict_interface()
        test_auto_creation()
        test_fine_tuned_models()

        print()
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
