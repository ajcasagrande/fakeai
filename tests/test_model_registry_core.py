"""
Test Model Registry Core

Comprehensive tests for ModelRegistry, ModelDefinition, and ModelCapabilities.
"""

import os
import sys
import threading
import time

import pytest

# Add direct path to avoid main package import issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fakeai"))

from models_registry import (
    CAPABILITY_PRESETS,
    LATENCY_PRESETS,
    LatencyProfile,
    ModelCapabilities,
    ModelDefinition,
    ModelRegistry,
    MoEConfig,
    create_model_definition,
)


class TestLatencyProfile:
    """Test LatencyProfile dataclass."""

    def test_valid_profile(self):
        """Test creating valid latency profile."""
        profile = LatencyProfile(
            time_to_first_token=0.1,
            tokens_per_second=50.0,
            min_delay=0.02,
            max_delay=0.05,
        )
        assert profile.time_to_first_token == 0.1
        assert profile.tokens_per_second == 50.0
        assert profile.min_delay == 0.02
        assert profile.max_delay == 0.05

    def test_invalid_ttft(self):
        """Test negative time_to_first_token raises error."""
        with pytest.raises(
            ValueError, match="time_to_first_token must be non-negative"
        ):
            LatencyProfile(
                time_to_first_token=-0.1,
                tokens_per_second=50.0,
                min_delay=0.02,
                max_delay=0.05,
            )

    def test_invalid_tps(self):
        """Test non-positive tokens_per_second raises error."""
        with pytest.raises(ValueError, match="tokens_per_second must be positive"):
            LatencyProfile(
                time_to_first_token=0.1,
                tokens_per_second=0.0,
                min_delay=0.02,
                max_delay=0.05,
            )

    def test_invalid_delays(self):
        """Test min_delay > max_delay raises error."""
        with pytest.raises(ValueError, match="min_delay cannot exceed max_delay"):
            LatencyProfile(
                time_to_first_token=0.1,
                tokens_per_second=50.0,
                min_delay=0.1,
                max_delay=0.05,
            )


class TestMoEConfig:
    """Test MoEConfig dataclass."""

    def test_valid_moe(self):
        """Test creating valid MoE config."""
        moe = MoEConfig(
            total_params=671_000_000_000,
            active_params=37_000_000_000,
            num_experts=256,
            experts_per_token=8,
        )
        assert moe.total_params == 671_000_000_000
        assert moe.active_params == 37_000_000_000
        assert moe.num_experts == 256
        assert moe.experts_per_token == 8

    def test_active_exceeds_total(self):
        """Test active_params > total_params raises error."""
        with pytest.raises(
            ValueError, match="active_params cannot exceed total_params"
        ):
            MoEConfig(
                total_params=1000,
                active_params=2000,
                num_experts=8,
                experts_per_token=2,
            )

    def test_experts_per_token_exceeds_num_experts(self):
        """Test experts_per_token > num_experts raises error."""
        with pytest.raises(
            ValueError, match="experts_per_token cannot exceed num_experts"
        ):
            MoEConfig(
                total_params=1000,
                active_params=500,
                num_experts=4,
                experts_per_token=8,
            )


class TestModelCapabilities:
    """Test ModelCapabilities dataclass."""

    def test_default_capabilities(self):
        """Test default capability values."""
        caps = ModelCapabilities()
        assert caps.supports_chat is True
        assert caps.supports_completion is False
        assert caps.supports_streaming is True
        assert caps.supports_vision is False
        assert caps.max_context_length == 4096
        assert caps.max_output_tokens == 4096

    def test_has_capability(self):
        """Test has_capability method."""
        caps = ModelCapabilities(
            supports_chat=True,
            supports_vision=True,
            supports_reasoning=True,
        )
        assert caps.has_capability("chat") is True
        assert caps.has_capability("vision") is True
        assert caps.has_capability("reasoning") is True
        assert caps.has_capability("embeddings") is False

    def test_get_supported_capabilities(self):
        """Test get_supported_capabilities method."""
        caps = ModelCapabilities(
            supports_chat=True,
            supports_streaming=True,
            supports_vision=True,
        )
        supported = caps.get_supported_capabilities()
        assert "chat" in supported
        assert "streaming" in supported
        assert "vision" in supported
        assert "kv_cache" in supported  # default True
        assert "embeddings" not in supported

    def test_moe_validation(self):
        """Test MoE configuration validation."""
        moe_config = MoEConfig(
            total_params=1000,
            active_params=500,
            num_experts=8,
            experts_per_token=2,
        )

        # Valid: is_moe=True with config
        caps = ModelCapabilities(is_moe=True, moe_config=moe_config)
        assert caps.is_moe is True

        # Invalid: is_moe=True without config
        with pytest.raises(ValueError, match="is_moe=True requires moe_config"):
            ModelCapabilities(is_moe=True, moe_config=None)

        # Invalid: moe_config without is_moe
        with pytest.raises(ValueError, match="moe_config requires is_moe=True"):
            ModelCapabilities(is_moe=False, moe_config=moe_config)

    def test_context_length_validation(self):
        """Test context length validation."""
        with pytest.raises(ValueError, match="max_context_length must be positive"):
            ModelCapabilities(max_context_length=0)

        with pytest.raises(ValueError, match="max_output_tokens must be positive"):
            ModelCapabilities(max_output_tokens=-1)

    def test_clone(self):
        """Test cloning capabilities with overrides."""
        original = ModelCapabilities(
            supports_chat=True,
            supports_vision=False,
            max_context_length=4096,
        )

        cloned = original.clone(supports_vision=True, max_context_length=8192)

        assert cloned.supports_chat is True
        assert cloned.supports_vision is True  # overridden
        assert cloned.max_context_length == 8192  # overridden

        # Original unchanged
        assert original.supports_vision is False
        assert original.max_context_length == 4096

    def test_capability_presets(self):
        """Test predefined capability presets."""
        assert "base" in CAPABILITY_PRESETS
        assert "chat" in CAPABILITY_PRESETS
        assert "vision" in CAPABILITY_PRESETS
        assert "reasoning" in CAPABILITY_PRESETS
        assert "embeddings" in CAPABILITY_PRESETS

        # Test chat preset
        chat_caps = CAPABILITY_PRESETS["chat"]
        assert chat_caps.supports_chat is True
        assert chat_caps.supports_function_calling is True
        assert chat_caps.supports_tool_use is True

        # Test vision preset
        vision_caps = CAPABILITY_PRESETS["vision"]
        assert vision_caps.supports_vision is True

        # Test reasoning preset
        reasoning_caps = CAPABILITY_PRESETS["reasoning"]
        assert reasoning_caps.supports_reasoning is True

    def test_latency_presets(self):
        """Test predefined latency presets."""
        assert "small" in LATENCY_PRESETS
        assert "medium" in LATENCY_PRESETS
        assert "large" in LATENCY_PRESETS
        assert "reasoning" in LATENCY_PRESETS

        small = LATENCY_PRESETS["small"]
        assert small.tokens_per_second > 50.0

        reasoning = LATENCY_PRESETS["reasoning"]
        assert reasoning.tokens_per_second < 20.0


class TestModelDefinition:
    """Test ModelDefinition dataclass."""

    def test_basic_definition(self):
        """Test creating basic model definition."""
        definition = ModelDefinition(
            model_id="test-model",
            created=int(time.time()),
            owned_by="test-org",
        )
        assert definition.model_id == "test-model"
        assert definition.owned_by == "test-org"
        assert definition.is_active is True
        assert definition.display_name == "test-model"

    def test_validation(self):
        """Test definition validation."""
        # Missing model_id
        with pytest.raises(ValueError, match="model_id is required"):
            ModelDefinition(model_id="", created=123, owned_by="test")

        # Missing owned_by
        with pytest.raises(ValueError, match="owned_by is required"):
            ModelDefinition(model_id="test", created=123, owned_by="")

        # Invalid created
        with pytest.raises(ValueError, match="created must be positive"):
            ModelDefinition(model_id="test", created=0, owned_by="test")

    def test_to_openai_model(self):
        """Test conversion to OpenAI format."""
        definition = ModelDefinition(
            model_id="test-model",
            created=1234567890,
            owned_by="test-org",
        )
        openai_model = definition.to_openai_model()

        assert openai_model["id"] == "test-model"
        assert openai_model["object"] == "model"
        assert openai_model["created"] == 1234567890
        assert openai_model["owned_by"] == "test-org"
        assert "permission" in openai_model
        assert openai_model["root"] == "test-model"

    def test_to_dict(self):
        """Test conversion to dict with full details."""
        caps = ModelCapabilities(
            supports_chat=True,
            supports_vision=True,
            max_context_length=8192,
        )
        definition = ModelDefinition(
            model_id="test-model",
            created=1234567890,
            owned_by="test-org",
            capabilities=caps,
            description="Test model",
        )
        result = definition.to_dict()

        assert result["model_id"] == "test-model"
        assert result["description"] == "Test model"
        assert result["capabilities"]["supports_chat"] is True
        assert result["capabilities"]["supports_vision"] is True
        assert result["capabilities"]["max_context_length"] == 8192

    def test_clone(self):
        """Test cloning definition."""
        original = ModelDefinition(
            model_id="original-model",
            created=1234567890,
            owned_by="test-org",
        )

        cloned = original.clone(new_model_id="cloned-model", owned_by="new-org")

        assert cloned.model_id == "cloned-model"
        assert cloned.owned_by == "new-org"
        assert cloned.created == 1234567890  # preserved

    def test_is_fine_tuned(self):
        """Test fine-tuned model detection."""
        # Fine-tuned (ft: format)
        ft_model = ModelDefinition(
            model_id="ft:gpt-4:org::abc123",
            created=123,
            owned_by="org",
        )
        assert ft_model.is_fine_tuned() is True

        # Fine-tuned (has parent)
        child_model = ModelDefinition(
            model_id="custom-model",
            created=123,
            owned_by="org",
            parent="base-model",
        )
        assert child_model.is_fine_tuned() is True

        # Not fine-tuned
        base_model = ModelDefinition(
            model_id="base-model",
            created=123,
            owned_by="org",
        )
        assert base_model.is_fine_tuned() is False

    def test_get_base_model(self):
        """Test extracting base model ID."""
        # Fine-tuned model
        ft_model = ModelDefinition(
            model_id="ft:gpt-4:org::abc123",
            created=123,
            owned_by="org",
        )
        assert ft_model.get_base_model() == "gpt-4"

        # Regular model
        base_model = ModelDefinition(
            model_id="base-model",
            created=123,
            owned_by="org",
        )
        assert base_model.get_base_model() == "base-model"

    def test_supports_endpoint(self):
        """Test endpoint support checking."""
        caps = ModelCapabilities(
            supports_chat=True,
            supports_embeddings=True,
        )
        definition = ModelDefinition(
            model_id="test-model",
            created=123,
            owned_by="test",
            capabilities=caps,
        )

        assert definition.supports_endpoint("chat") is True
        assert definition.supports_endpoint("embeddings") is True
        assert definition.supports_endpoint("completion") is False


class TestCreateModelDefinition:
    """Test create_model_definition factory function."""

    def test_create_with_preset(self):
        """Test creating model with preset."""
        definition = create_model_definition(
            model_id="test-model",
            preset="chat",
            owned_by="test-org",
        )

        assert definition.model_id == "test-model"
        assert definition.owned_by == "test-org"
        assert definition.capabilities.supports_chat is True
        assert definition.capabilities.supports_function_calling is True

    def test_invalid_preset(self):
        """Test invalid preset raises error."""
        with pytest.raises(ValueError, match="Invalid preset"):
            create_model_definition(
                model_id="test-model",
                preset="nonexistent",
            )

    def test_create_with_overrides(self):
        """Test creating with field overrides."""
        definition = create_model_definition(
            model_id="test-model",
            preset="base",
            description="Custom description",
            version="1.0.0",
        )

        assert definition.description == "Custom description"
        assert definition.version == "1.0.0"


class TestModelRegistry:
    """Test ModelRegistry class."""

    def test_initialization(self):
        """Test registry initialization."""
        registry = ModelRegistry()
        assert len(registry) == 0

    def test_register_model(self):
        """Test registering a model."""
        registry = ModelRegistry()
        definition = registry.register("test-model", preset="base")

        assert definition.model_id == "test-model"
        assert len(registry) == 1
        assert "test-model" in registry

    def test_register_duplicate(self):
        """Test registering duplicate raises error."""
        registry = ModelRegistry()
        registry.register("test-model", preset="base")

        with pytest.raises(ValueError, match="already registered"):
            registry.register("test-model", preset="base")

    def test_get_model(self):
        """Test getting model by ID."""
        registry = ModelRegistry()
        registry.register("test-model", preset="chat")

        definition = registry.get("test-model")
        assert definition is not None
        assert definition.model_id == "test-model"

        # Non-existent model
        assert registry.get("nonexistent") is None

    def test_get_or_create(self):
        """Test get_or_create functionality."""
        registry = ModelRegistry()

        # Create new model
        definition1 = registry.get_or_create("new-model", preset="chat")
        assert definition1.model_id == "new-model"
        assert len(registry) == 1

        # Get existing model
        definition2 = registry.get_or_create("new-model")
        assert definition2.model_id == "new-model"
        assert len(registry) == 1

        # Same instance
        assert definition1 is definition2

    def test_exists(self):
        """Test checking model existence."""
        registry = ModelRegistry()
        registry.register("test-model", preset="base")

        assert registry.exists("test-model") is True
        assert registry.exists("nonexistent") is False

    def test_unregister(self):
        """Test removing model."""
        registry = ModelRegistry()
        registry.register("test-model", preset="base")

        assert registry.unregister("test-model") is True
        assert len(registry) == 0
        assert registry.unregister("test-model") is False

    def test_list_models(self):
        """Test listing models."""
        registry = ModelRegistry()
        registry.register("model-1", preset="base", owned_by="org-1")
        registry.register("model-2", preset="chat", owned_by="org-2")

        # Create inactive model
        inactive_def = create_model_definition(
            model_id="model-3",
            preset="base",
            owned_by="org-1",
            is_active=False,
        )
        registry.register("model-3", definition=inactive_def)

        # List all active
        active = registry.list_models(active_only=True)
        assert len(active) == 2

        # List all including inactive
        all_models = registry.list_models(active_only=False)
        assert len(all_models) == 3

        # Filter by owner
        org1_models = registry.list_models(owned_by="org-1")
        assert len(org1_models) == 1

    def test_get_capabilities(self):
        """Test getting model capabilities."""
        registry = ModelRegistry()
        registry.register("test-model", preset="vision")

        caps = registry.get_capabilities("test-model")
        assert caps is not None
        assert caps["supports_chat"] is True
        assert caps["supports_vision"] is True

        # Non-existent model
        assert registry.get_capabilities("nonexistent") is None

    def test_list_by_capability(self):
        """Test listing models by capability."""
        registry = ModelRegistry()
        registry.register("chat-model", preset="chat")
        registry.register("vision-model", preset="vision")
        registry.register("reasoning-model", preset="reasoning")

        # List vision models
        vision_models = registry.list_by_capability("vision")
        assert len(vision_models) == 1
        assert vision_models[0].model_id == "vision-model"

        # List reasoning models
        reasoning_models = registry.list_by_capability("reasoning")
        assert len(reasoning_models) == 1

        # List chat models (multiple)
        chat_models = registry.list_by_capability("chat")
        assert len(chat_models) == 3  # chat, vision, and reasoning all support chat

    def test_auto_creation_handler(self):
        """Test auto-creation handler."""
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

        # Auto-create with handler
        definition = registry.get_or_create("custom-model-123")
        assert definition.owned_by == "custom-org"
        assert definition.capabilities.supports_chat is True

        # Non-matching model falls back to default
        definition2 = registry.get_or_create("regular-model")
        assert definition2.owned_by == "system"

    def test_clear(self):
        """Test clearing registry."""
        registry = ModelRegistry()
        registry.register("model-1", preset="base")
        registry.register("model-2", preset="chat")

        assert len(registry) == 2

        registry.clear()
        assert len(registry) == 0

    def test_get_stats(self):
        """Test registry statistics."""
        registry = ModelRegistry()
        registry.register("chat-model", preset="chat", owned_by="org-1")
        registry.register("vision-model", preset="vision", owned_by="org-1")
        registry.register("reasoning-model", preset="reasoning", owned_by="org-2")

        # Add deprecated model
        deprecated_def = create_model_definition(
            model_id="old-model",
            preset="base",
            owned_by="org-1",
            deprecated=True,
        )
        registry.register("old-model", definition=deprecated_def)

        stats = registry.get_stats()

        assert stats["total_models"] == 4
        assert stats["active_models"] == 4
        assert stats["deprecated_models"] == 1
        assert (
            stats["capabilities"]["chat"] == 4
        )  # base, chat, vision, reasoning all support chat
        assert stats["capabilities"]["vision"] == 1
        assert stats["capabilities"]["reasoning"] == 1
        assert stats["by_owner"]["org-1"] == 3
        assert stats["by_owner"]["org-2"] == 1

    def test_dict_interface_contains(self):
        """Test __contains__ (in operator)."""
        registry = ModelRegistry()
        registry.register("test-model", preset="base")

        assert "test-model" in registry
        assert "nonexistent" not in registry

    def test_dict_interface_getitem(self):
        """Test __getitem__ ([] operator)."""
        registry = ModelRegistry()
        registry.register("test-model", preset="base")

        definition = registry["test-model"]
        assert definition.model_id == "test-model"

        with pytest.raises(KeyError):
            _ = registry["nonexistent"]

    def test_dict_interface_setitem(self):
        """Test __setitem__ ([] assignment)."""
        registry = ModelRegistry()
        definition = create_model_definition("test-model", preset="chat")

        registry["test-model"] = definition
        assert "test-model" in registry

        # Mismatched ID
        wrong_def = create_model_definition("other-model", preset="base")
        with pytest.raises(ValueError, match="does not match"):
            registry["test-model"] = wrong_def

    def test_dict_interface_delitem(self):
        """Test __delitem__ (del operator)."""
        registry = ModelRegistry()
        registry.register("test-model", preset="base")

        del registry["test-model"]
        assert "test-model" not in registry

        with pytest.raises(KeyError):
            del registry["nonexistent"]

    def test_dict_interface_len(self):
        """Test __len__ (len() function)."""
        registry = ModelRegistry()
        assert len(registry) == 0

        registry.register("model-1", preset="base")
        assert len(registry) == 1

        registry.register("model-2", preset="chat")
        assert len(registry) == 2

    def test_dict_interface_iter(self):
        """Test __iter__ (for loop)."""
        registry = ModelRegistry()
        registry.register("model-1", preset="base")
        registry.register("model-2", preset="chat")

        model_ids = list(registry)
        assert "model-1" in model_ids
        assert "model-2" in model_ids

    def test_dict_interface_keys_values_items(self):
        """Test keys(), values(), items() methods."""
        registry = ModelRegistry()
        registry.register("model-1", preset="base")
        registry.register("model-2", preset="chat")

        # Keys
        keys = registry.keys()
        assert len(keys) == 2
        assert "model-1" in keys

        # Values
        values = registry.values()
        assert len(values) == 2
        assert all(isinstance(v, ModelDefinition) for v in values)

        # Items
        items = registry.items()
        assert len(items) == 2
        assert all(
            isinstance(k, str) and isinstance(v, ModelDefinition) for k, v in items
        )

    def test_thread_safety(self):
        """Test thread-safe operations."""
        registry = ModelRegistry()
        errors = []

        def register_models(start_idx: int, count: int):
            try:
                for i in range(start_idx, start_idx + count):
                    registry.get_or_create(f"model-{i}", preset="base")
            except Exception as e:
                errors.append(e)

        # Create 10 threads registering 10 models each
        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_models, args=(i * 10, 10))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check no errors occurred
        assert len(errors) == 0

        # Check all models were registered
        assert len(registry) == 100

    def test_concurrent_access(self):
        """Test concurrent read/write operations."""
        registry = ModelRegistry()
        registry.register("base-model", preset="base")

        results = []

        def read_and_create():
            # Read existing
            definition = registry.get("base-model")
            results.append(definition is not None)

            # Create new
            registry.get_or_create(f"model-{threading.current_thread().name}")

        threads = []
        for i in range(5):
            thread = threading.Thread(target=read_and_create, name=f"t{i}")
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All reads should succeed
        assert all(results)

        # All models should be created
        assert len(registry) >= 6  # base + 5 new


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
