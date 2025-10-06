"""
Model Definition

Defines complete model specifications including capabilities,
metadata, and conversion to OpenAI format.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .capabilities import CAPABILITY_PRESETS, ModelCapabilities


@dataclass
class ModelDefinition:
    """
    Complete model definition with capabilities and metadata.

    Represents a registered model with all its characteristics,
    capabilities, and metadata. Can be converted to OpenAI API format.
    """

    # Identity
    model_id: str
    created: int
    owned_by: str = "system"

    # Capabilities
    capabilities: ModelCapabilities = field(
        default_factory=lambda: CAPABILITY_PRESETS["base"]
    )

    # Metadata
    display_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None

    # Hierarchy (for fine-tuned models)
    parent: Optional[str] = None
    root: Optional[str] = None

    # Status
    is_active: bool = True
    deprecated: bool = False
    deprecation_message: Optional[str] = None

    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate model definition."""
        if not self.model_id:
            raise ValueError("model_id is required")
        if not self.owned_by:
            raise ValueError("owned_by is required")
        if self.created <= 0:
            raise ValueError("created must be positive")

        # Set display name if not provided
        if not self.display_name:
            self.display_name = self.model_id

    def to_openai_model(self) -> Dict[str, Any]:
        """
        Convert to OpenAI Model format.

        Returns:
            Dict matching OpenAI API Model schema
        """
        return {
            "id": self.model_id,
            "object": "model",
            "created": self.created,
            "owned_by": self.owned_by,
            "permission": [
                {
                    "id": f"modelperm-{self.model_id}",
                    "object": "model_permission",
                    "created": self.created,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": self.capabilities.supports_fine_tuning,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False,
                }
            ],
            "root": self.root or self.model_id,
            "parent": self.parent,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary with full details.

        Returns:
            Complete model definition as dict
        """
        result = {
            "model_id": self.model_id,
            "created": self.created,
            "owned_by": self.owned_by,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "parent": self.parent,
            "root": self.root,
            "is_active": self.is_active,
            "deprecated": self.deprecated,
            "deprecation_message": self.deprecation_message,
            "capabilities": {
                "supports_chat": self.capabilities.supports_chat,
                "supports_completion": self.capabilities.supports_completion,
                "supports_streaming": self.capabilities.supports_streaming,
                "supports_function_calling": self.capabilities.supports_function_calling,
                "supports_tool_use": self.capabilities.supports_tool_use,
                "supports_json_mode": self.capabilities.supports_json_mode,
                "supports_vision": self.capabilities.supports_vision,
                "supports_audio_input": self.capabilities.supports_audio_input,
                "supports_audio_output": self.capabilities.supports_audio_output,
                "supports_video": self.capabilities.supports_video,
                "supports_reasoning": self.capabilities.supports_reasoning,
                "supports_predicted_outputs": self.capabilities.supports_predicted_outputs,
                "supports_embeddings": self.capabilities.supports_embeddings,
                "supports_moderation": self.capabilities.supports_moderation,
                "supports_fine_tuning": self.capabilities.supports_fine_tuning,
                "max_context_length": self.capabilities.max_context_length,
                "max_output_tokens": self.capabilities.max_output_tokens,
                "max_batch_size": self.capabilities.max_batch_size,
                "supports_parallel_tool_calls": self.capabilities.supports_parallel_tool_calls,
                "supports_kv_cache": self.capabilities.supports_kv_cache,
                "is_moe": self.capabilities.is_moe,
                "parameter_count": self.capabilities.parameter_count,
                "provider": self.capabilities.provider,
                "model_family": self.capabilities.model_family,
                "tags": self.capabilities.tags,
            },
        }

        # Add MoE config if present
        if self.capabilities.moe_config:
            result["capabilities"]["moe_config"] = {
                "total_params": self.capabilities.moe_config.total_params,
                "active_params": self.capabilities.moe_config.active_params,
                "num_experts": self.capabilities.moe_config.num_experts,
                "experts_per_token": self.capabilities.moe_config.experts_per_token,
            }

        # Add latency profile if present
        if self.capabilities.latency_profile:
            result["capabilities"]["latency_profile"] = {
                "time_to_first_token": self.capabilities.latency_profile.time_to_first_token,
                "tokens_per_second": self.capabilities.latency_profile.tokens_per_second,
                "min_delay": self.capabilities.latency_profile.min_delay,
                "max_delay": self.capabilities.latency_profile.max_delay,
            }

        # Add custom metadata
        if self.capabilities.custom_metadata:
            result["capabilities"][
                "custom_metadata"
            ] = self.capabilities.custom_metadata

        # Add custom fields
        if self.custom_fields:
            result["custom_fields"] = self.custom_fields

        return result

    def clone(
        self, new_model_id: Optional[str] = None, **overrides
    ) -> "ModelDefinition":
        """
        Create a copy with optional overrides.

        Args:
            new_model_id: New model ID (optional)
            **overrides: Fields to override

        Returns:
            New ModelDefinition instance
        """
        values = {
            "model_id": new_model_id or self.model_id,
            "created": self.created,
            "owned_by": self.owned_by,
            "capabilities": self.capabilities,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "parent": self.parent,
            "root": self.root,
            "is_active": self.is_active,
            "deprecated": self.deprecated,
            "deprecation_message": self.deprecation_message,
            "custom_fields": self.custom_fields.copy(),
        }

        # Apply overrides
        values.update(overrides)

        return ModelDefinition(**values)

    def is_fine_tuned(self) -> bool:
        """
        Check if this is a fine-tuned model.

        Returns:
            True if model follows ft: format or has parent
        """
        return self.model_id.startswith("ft:") or self.parent is not None

    def get_base_model(self) -> str:
        """
        Get base model ID (for fine-tuned models).

        Returns:
            Base model ID or self if not fine-tuned
        """
        if self.model_id.startswith("ft:"):
            # Parse ft:base:org::id format
            parts = self.model_id.split(":")
            if len(parts) >= 2:
                return parts[1]
        return self.root or self.model_id

    def supports_endpoint(self, endpoint: str) -> bool:
        """
        Check if model supports a specific endpoint.

        Args:
            endpoint: Endpoint name (chat, completion, embeddings, etc.)

        Returns:
            True if endpoint is supported
        """
        endpoint_map = {
            "chat": self.capabilities.supports_chat,
            "completion": self.capabilities.supports_completion,
            "embeddings": self.capabilities.supports_embeddings,
            "moderation": self.capabilities.supports_moderation,
        }
        return endpoint_map.get(endpoint, False)


def create_model_definition(
    model_id: str,
    preset: str = "base",
    owned_by: str = "system",
    created: Optional[int] = None,
    **overrides,
) -> ModelDefinition:
    """
    Factory function to create a model definition from preset.

    Args:
        model_id: Model identifier
        preset: Capability preset name (base, chat, vision, etc.)
        owned_by: Model owner
        created: Creation timestamp (defaults to current time - 10000s)
        **overrides: Additional fields to override

    Returns:
        ModelDefinition instance

    Raises:
        ValueError: If preset is invalid
    """
    if preset not in CAPABILITY_PRESETS:
        available = ", ".join(CAPABILITY_PRESETS.keys())
        raise ValueError(f"Invalid preset '{preset}'. Available: {available}")

    # Get capability preset
    capabilities = CAPABILITY_PRESETS[preset]

    # Use default created time if not provided
    if created is None:
        created = int(time.time()) - 10000

    # Create definition
    definition = ModelDefinition(
        model_id=model_id,
        created=created,
        owned_by=owned_by,
        capabilities=capabilities,
        **overrides,
    )

    return definition
