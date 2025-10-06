#!/usr/bin/env python
"""
Model Registry Demo

Demonstrates core functionality of the FakeAI Model Registry.
"""

import os
import sys

# Add path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fakeai"))

from models_registry import (
    CAPABILITY_PRESETS,
    LATENCY_PRESETS,
    ModelCapabilities,
    ModelRegistry,
    MoEConfig,
    create_model_definition,
)


def demo_basic_usage():
    """Demonstrate basic registry operations."""
    print("=" * 60)
    print("Basic Registry Operations")
    print("=" * 60)

    registry = ModelRegistry()

    # Register models with different presets
    registry.register("gpt-4", preset="chat", owned_by="openai")
    registry.register("gpt-4-vision", preset="vision", owned_by="openai")
    registry.register("gpt-oss-120b", preset="reasoning", owned_by="openai")
    registry.register("text-embedding-3-large", preset="embeddings", owned_by="openai")

    print(f"Registered {len(registry)} models")
    print(f"Models: {', '.join(registry.keys())}")
    print()


def demo_capability_queries():
    """Demonstrate capability-based queries."""
    print("=" * 60)
    print("Capability Queries")
    print("=" * 60)

    registry = ModelRegistry()
    registry.register("gpt-4", preset="chat", owned_by="openai")
    registry.register("gpt-4-vision", preset="vision", owned_by="openai")
    registry.register("gpt-oss-120b", preset="reasoning", owned_by="openai")
    registry.register("deepseek-v3", preset="reasoning", owned_by="deepseek")

    # Query by capability
    vision_models = registry.list_by_capability("vision")
    print(f"Vision models: {[m.model_id for m in vision_models]}")

    reasoning_models = registry.list_by_capability("reasoning")
    print(f"Reasoning models: {[m.model_id for m in reasoning_models]}")

    chat_models = registry.list_by_capability("chat")
    print(f"Chat models: {[m.model_id for m in chat_models]}")
    print()


def demo_moe_models():
    """Demonstrate MoE configuration."""
    print("=" * 60)
    print("MoE Model Configuration")
    print("=" * 60)

    registry = ModelRegistry()

    # Create MoE model
    moe_config = MoEConfig(
        total_params=671_000_000_000,
        active_params=37_000_000_000,
        num_experts=256,
        experts_per_token=8,
    )

    moe_caps = CAPABILITY_PRESETS["reasoning"].clone(
        is_moe=True,
        moe_config=moe_config,
        parameter_count=671_000_000_000,
    )

    definition = create_model_definition(
        model_id="deepseek-v3",
        preset="reasoning",
        owned_by="deepseek",
    )
    definition.capabilities = moe_caps

    registry.register("deepseek-v3", definition=definition)

    model = registry.get("deepseek-v3")
    print(f"Model: {model.model_id}")
    print(f"MoE: {model.capabilities.is_moe}")
    print(f"Total params: {model.capabilities.parameter_count:,}")
    print(f"Active params: {model.capabilities.moe_config.active_params:,}")
    print(f"Num experts: {model.capabilities.moe_config.num_experts}")
    print()


def demo_fine_tuned_models():
    """Demonstrate fine-tuned model support."""
    print("=" * 60)
    print("Fine-Tuned Models")
    print("=" * 60)

    registry = ModelRegistry()

    # Register base model
    registry.register("gpt-4", preset="chat", owned_by="openai")

    # Register fine-tuned model
    ft_model = create_model_definition(
        model_id="ft:gpt-4:my-org::abc123",
        preset="chat",
        owned_by="my-org",
        parent="gpt-4",
        root="gpt-4",
        description="Fine-tuned for customer support",
    )
    registry.register("ft:gpt-4:my-org::abc123", definition=ft_model)

    model = registry.get("ft:gpt-4:my-org::abc123")
    print(f"Model: {model.model_id}")
    print(f"Fine-tuned: {model.is_fine_tuned()}")
    print(f"Base model: {model.get_base_model()}")
    print(f"Parent: {model.parent}")
    print(f"Root: {model.root}")
    print()


def demo_statistics():
    """Demonstrate registry statistics."""
    print("=" * 60)
    print("Registry Statistics")
    print("=" * 60)

    registry = ModelRegistry()

    # Register various models
    registry.register("gpt-4", preset="chat", owned_by="openai")
    registry.register("gpt-4-vision", preset="vision", owned_by="openai")
    registry.register("gpt-oss-120b", preset="reasoning", owned_by="openai")
    registry.register("deepseek-v3", preset="reasoning", owned_by="deepseek")
    registry.register("text-embedding-3-large", preset="embeddings", owned_by="openai")

    stats = registry.get_stats()

    print(f"Total models: {stats['total_models']}")
    print(f"Active models: {stats['active_models']}")
    print(f"Deprecated models: {stats['deprecated_models']}")
    print()
    print("By capability:")
    for cap, count in stats["capabilities"].items():
        if count > 0:
            print(f"  {cap}: {count}")
    print()
    print("By owner:")
    for owner, count in stats["by_owner"].items():
        print(f"  {owner}: {count}")
    print()


def demo_auto_creation():
    """Demonstrate auto-creation handler."""
    print("=" * 60)
    print("Auto-Creation Handler")
    print("=" * 60)

    registry = ModelRegistry()

    # Define custom handler
    def custom_handler(model_id: str):
        if model_id.startswith("custom-"):
            print(f"Auto-creating: {model_id}")
            return create_model_definition(
                model_id=model_id,
                preset="chat",
                owned_by="custom-org",
                description=f"Auto-created model: {model_id}",
            )
        return None

    registry.set_auto_creation_handler(custom_handler)

    # This will trigger auto-creation
    model1 = registry.get_or_create("custom-model-123")
    print(f"Created: {model1.model_id} (owned by {model1.owned_by})")

    # This won't trigger handler (falls back to default)
    model2 = registry.get_or_create("regular-model")
    print(f"Created: {model2.model_id} (owned by {model2.owned_by})")
    print()


def demo_dict_interface():
    """Demonstrate dict-like interface."""
    print("=" * 60)
    print("Dict-Like Interface")
    print("=" * 60)

    registry = ModelRegistry()
    registry.register("gpt-4", preset="chat", owned_by="openai")
    registry.register("claude-3", preset="chat", owned_by="anthropic")

    # Check existence
    print(f"'gpt-4' in registry: {'gpt-4' in registry}")
    print(f"'nonexistent' in registry: {'nonexistent' in registry}")

    # Access via []
    model = registry["gpt-4"]
    print(f"registry['gpt-4']: {model.model_id}")

    # Length
    print(f"len(registry): {len(registry)}")

    # Iteration
    print(f"Models: {list(registry)}")
    print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "FakeAI Model Registry Demo" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    try:
        demo_basic_usage()
        demo_capability_queries()
        demo_moe_models()
        demo_fine_tuned_models()
        demo_statistics()
        demo_auto_creation()
        demo_dict_interface()

        print("=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
