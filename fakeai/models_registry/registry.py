"""
Model Registry

Thread-safe model registry with capability queries, auto-creation,
and dict-like interface.
"""

import threading
from typing import Any, Callable, Iterator, Optional

from .definition import ModelDefinition, create_model_definition


class ModelRegistry:
    """
    Thread-safe model registry with capability-based queries.

    Manages model definitions with support for registration, lookup,
    capability queries, and automatic model creation.
    """

    def __init__(self):
        """Initialize empty registry with thread safety."""
        self._models: dict[str, ModelDefinition] = {}
        self._lock = threading.RLock()
        self._auto_creation_handler: Optional[Callable[[
            str], ModelDefinition]] = None

    def register(
        self,
        model_id: str,
        definition: Optional[ModelDefinition] = None,
        preset: str = "base",
        **kwargs,
    ) -> ModelDefinition:
        """
        Register a model in the registry.

        Args:
            model_id: Model identifier
            definition: Complete ModelDefinition (if provided, other args ignored)
            preset: Capability preset if creating new definition
            **kwargs: Additional fields for create_model_definition

        Returns:
            The registered ModelDefinition

        Raises:
            ValueError: If model_id already exists
        """
        with self._lock:
            if model_id in self._models:
                raise ValueError(f"Model '{model_id}' already registered")

            # Use provided definition or create new one
            if definition is None:
                definition = create_model_definition(
                    model_id=model_id, preset=preset, **kwargs
                )
            elif definition.model_id != model_id:
                raise ValueError(
                    f"Definition model_id '{definition.model_id}' "
                    f"does not match '{model_id}'"
                )

            self._models[model_id] = definition
            return definition

    def get(self, model_id: str) -> Optional[ModelDefinition]:
        """
        Get model definition by ID.

        Args:
            model_id: Model identifier

        Returns:
            ModelDefinition if found, None otherwise
        """
        with self._lock:
            return self._models.get(model_id)

    def get_or_create(
        self, model_id: str, preset: str = "base", **kwargs
    ) -> ModelDefinition:
        """
        Get existing model or create if not found.

        Args:
            model_id: Model identifier
            preset: Capability preset for auto-creation
            **kwargs: Additional fields for auto-creation

        Returns:
            ModelDefinition (existing or newly created)
        """
        with self._lock:
            # Try to get existing
            definition = self._models.get(model_id)
            if definition is not None:
                return definition

            # Try auto-creation handler
            if self._auto_creation_handler:
                definition = self._auto_creation_handler(model_id)
                if definition:
                    self._models[model_id] = definition
                    return definition

            # Create with preset
            definition = create_model_definition(
                model_id=model_id, preset=preset, **kwargs
            )
            self._models[model_id] = definition
            return definition

    def exists(self, model_id: str) -> bool:
        """
        Check if model exists in registry.

        Args:
            model_id: Model identifier

        Returns:
            True if model is registered
        """
        with self._lock:
            return model_id in self._models

    def unregister(self, model_id: str) -> bool:
        """
        Remove model from registry.

        Args:
            model_id: Model identifier

        Returns:
            True if model was removed, False if not found
        """
        with self._lock:
            if model_id in self._models:
                del self._models[model_id]
                return True
            return False

    def list_models(
        self, active_only: bool = True, owned_by: Optional[str] = None
    ) -> list[ModelDefinition]:
        """
        List all registered models.

        Args:
            active_only: Only return active models
            owned_by: Filter by owner

        Returns:
            List of ModelDefinition objects
        """
        with self._lock:
            models = list(self._models.values())

            if active_only:
                models = [m for m in models if m.is_active]

            if owned_by:
                models = [m for m in models if m.owned_by == owned_by]

            return models

    def get_capabilities(self, model_id: str) -> Optional[dict]:
        """
        Get model capabilities as dictionary.

        Args:
            model_id: Model identifier

        Returns:
            Capabilities dict or None if model not found
        """
        definition = self.get(model_id)
        if definition is None:
            return None

        caps = definition.capabilities
        return {
            "supports_chat": caps.supports_chat,
            "supports_completion": caps.supports_completion,
            "supports_streaming": caps.supports_streaming,
            "supports_function_calling": caps.supports_function_calling,
            "supports_tool_use": caps.supports_tool_use,
            "supports_json_mode": caps.supports_json_mode,
            "supports_vision": caps.supports_vision,
            "supports_audio_input": caps.supports_audio_input,
            "supports_audio_output": caps.supports_audio_output,
            "supports_video": caps.supports_video,
            "supports_reasoning": caps.supports_reasoning,
            "supports_predicted_outputs": caps.supports_predicted_outputs,
            "supports_embeddings": caps.supports_embeddings,
            "supports_moderation": caps.supports_moderation,
            "supports_fine_tuning": caps.supports_fine_tuning,
            "max_context_length": caps.max_context_length,
            "max_output_tokens": caps.max_output_tokens,
            "supports_kv_cache": caps.supports_kv_cache,
            "is_moe": caps.is_moe,
            "parameter_count": caps.parameter_count,
        }

    def list_by_capability(
        self, capability: str, active_only: bool = True
    ) -> list[ModelDefinition]:
        """
        List models that support a specific capability.

        Args:
            capability: Capability name (e.g., 'vision', 'reasoning')
            active_only: Only return active models

        Returns:
            List of matching ModelDefinition objects
        """
        with self._lock:
            models = list(self._models.values())

            if active_only:
                models = [m for m in models if m.is_active]

            # Filter by capability
            matching = [
                m for m in models if m.capabilities.has_capability(capability)]

            return matching

    def set_auto_creation_handler(
        self, handler: Optional[Callable[[str], ModelDefinition]]
    ) -> None:
        """
        Set handler for automatic model creation.

        Args:
            handler: Function that takes model_id and returns ModelDefinition,
                    or None to disable auto-creation
        """
        with self._lock:
            self._auto_creation_handler = handler

    def clear(self) -> None:
        """Clear all models from registry."""
        with self._lock:
            self._models.clear()

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dict with counts and breakdowns
        """
        with self._lock:
            models = list(self._models.values())

            # Count by status
            active = sum(1 for m in models if m.is_active)
            deprecated = sum(1 for m in models if m.deprecated)

            # Count by capabilities
            chat_models = sum(
                1 for m in models if m.capabilities.supports_chat)
            vision_models = sum(
                1 for m in models if m.capabilities.supports_vision)
            reasoning_models = sum(
                1 for m in models if m.capabilities.supports_reasoning
            )
            embedding_models = sum(
                1 for m in models if m.capabilities.supports_embeddings
            )

            # Count by owner
            owners = {}
            for model in models:
                owners[model.owned_by] = owners.get(model.owned_by, 0) + 1

            # Count fine-tuned models
            fine_tuned = sum(1 for m in models if m.is_fine_tuned())

            return {
                "total_models": len(models),
                "active_models": active,
                "deprecated_models": deprecated,
                "fine_tuned_models": fine_tuned,
                "capabilities": {
                    "chat": chat_models,
                    "vision": vision_models,
                    "reasoning": reasoning_models,
                    "embeddings": embedding_models,
                },
                "by_owner": owners,
            }

    # Dict-like interface

    def __contains__(self, model_id: str) -> bool:
        """Check if model exists (supports 'in' operator)."""
        return self.exists(model_id)

    def __getitem__(self, model_id: str) -> ModelDefinition:
        """Get model by ID (supports [] operator)."""
        definition = self.get(model_id)
        if definition is None:
            raise KeyError(f"Model '{model_id}' not found")
        return definition

    def __setitem__(self, model_id: str, definition: ModelDefinition) -> None:
        """Register model (supports [] assignment)."""
        with self._lock:
            if definition.model_id != model_id:
                raise ValueError(
                    f"Definition model_id '{definition.model_id}' "
                    f"does not match key '{model_id}'"
                )
            self._models[model_id] = definition

    def __delitem__(self, model_id: str) -> None:
        """Unregister model (supports del operator)."""
        with self._lock:
            if model_id not in self._models:
                raise KeyError(f"Model '{model_id}' not found")
            del self._models[model_id]

    def __len__(self) -> int:
        """Get number of registered models."""
        with self._lock:
            return len(self._models)

    def __iter__(self) -> Iterator[str]:
        """Iterate over model IDs."""
        with self._lock:
            return iter(list(self._models.keys()))

    def keys(self) -> list[str]:
        """Get all model IDs."""
        with self._lock:
            return list(self._models.keys())

    def values(self) -> list[ModelDefinition]:
        """Get all model definitions."""
        with self._lock:
            return list(self._models.values())

    def items(self) -> list[tuple[str, ModelDefinition]]:
        """Get all (model_id, definition) pairs."""
        with self._lock:
            return list(self._models.items())
