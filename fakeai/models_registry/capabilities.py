"""
Model Capabilities System

Defines model capabilities, features, and performance characteristics.
Provides preset configurations for common model types.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MoEConfig:
    """
    Mixture of Experts configuration.

    Attributes:
        total_params: Total parameter count (all experts)
        active_params: Active parameters per forward pass
        num_experts: Number of expert modules
        experts_per_token: Experts activated per token
    """

    total_params: int
    active_params: int
    num_experts: int
    experts_per_token: int

    def __post_init__(self):
        """Validate MoE configuration."""
        if self.active_params > self.total_params:
            raise ValueError("active_params cannot exceed total_params")
        if self.experts_per_token > self.num_experts:
            raise ValueError("experts_per_token cannot exceed num_experts")


@dataclass
class LatencyProfile:
    """
    Model latency characteristics for simulation.

    Attributes:
        time_to_first_token: TTFT in seconds
        tokens_per_second: Generation speed
        min_delay: Minimum inter-token delay
        max_delay: Maximum inter-token delay
    """

    time_to_first_token: float
    tokens_per_second: float
    min_delay: float
    max_delay: float

    def __post_init__(self):
        """Validate latency profile."""
        if self.time_to_first_token < 0:
            raise ValueError("time_to_first_token must be non-negative")
        if self.tokens_per_second <= 0:
            raise ValueError("tokens_per_second must be positive")
        if self.min_delay < 0 or self.max_delay < 0:
            raise ValueError("delays must be non-negative")
        if self.min_delay > self.max_delay:
            raise ValueError("min_delay cannot exceed max_delay")


@dataclass
class ModelCapabilities:
    """
    Complete model capabilities and feature flags.

    Defines what a model can do, its supported features, performance
    characteristics, and constraints.
    """

    # Core capabilities
    supports_chat: bool = True
    supports_completion: bool = False
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_tool_use: bool = False
    supports_json_mode: bool = False

    # Multi-modal capabilities
    supports_vision: bool = False
    supports_audio_input: bool = False
    supports_audio_output: bool = False
    supports_video: bool = False

    # Advanced features
    supports_reasoning: bool = False
    supports_predicted_outputs: bool = False
    supports_embeddings: bool = False
    supports_moderation: bool = False
    supports_fine_tuning: bool = False

    # Context and limits
    max_context_length: int = 4096
    max_output_tokens: int = 4096
    max_batch_size: Optional[int] = None
    supports_parallel_tool_calls: bool = False

    # Performance characteristics
    latency_profile: Optional[LatencyProfile] = None
    supports_kv_cache: bool = True

    # Architecture details
    is_moe: bool = False
    moe_config: Optional[MoEConfig] = None
    parameter_count: Optional[int] = None

    # Provider information
    provider: str = "openai"
    model_family: Optional[str] = None

    # Metadata
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate capabilities configuration."""
        # Validate MoE consistency
        if self.is_moe and not self.moe_config:
            raise ValueError("is_moe=True requires moe_config")
        if not self.is_moe and self.moe_config:
            raise ValueError("moe_config requires is_moe=True")

        # Validate context limits
        if self.max_context_length <= 0:
            raise ValueError("max_context_length must be positive")
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")

        # Validate batch size
        if self.max_batch_size is not None and self.max_batch_size <= 0:
            raise ValueError("max_batch_size must be positive if specified")

    def has_capability(self, capability: str) -> bool:
        """
        Check if model has a specific capability.

        Args:
            capability: Capability name (e.g., 'chat', 'vision', 'reasoning')

        Returns:
            True if capability is supported
        """
        capability_map = {
            "chat": self.supports_chat,
            "completion": self.supports_completion,
            "streaming": self.supports_streaming,
            "function_calling": self.supports_function_calling,
            "tool_use": self.supports_tool_use,
            "json_mode": self.supports_json_mode,
            "vision": self.supports_vision,
            "audio_input": self.supports_audio_input,
            "audio_output": self.supports_audio_output,
            "video": self.supports_video,
            "reasoning": self.supports_reasoning,
            "predicted_outputs": self.supports_predicted_outputs,
            "embeddings": self.supports_embeddings,
            "moderation": self.supports_moderation,
            "fine_tuning": self.supports_fine_tuning,
            "kv_cache": self.supports_kv_cache,
        }
        return capability_map.get(capability, False)

    def get_supported_capabilities(self) -> list[str]:
        """
        Get list of all supported capabilities.

        Returns:
            List of capability names
        """
        capabilities = []
        if self.supports_chat:
            capabilities.append("chat")
        if self.supports_completion:
            capabilities.append("completion")
        if self.supports_streaming:
            capabilities.append("streaming")
        if self.supports_function_calling:
            capabilities.append("function_calling")
        if self.supports_tool_use:
            capabilities.append("tool_use")
        if self.supports_json_mode:
            capabilities.append("json_mode")
        if self.supports_vision:
            capabilities.append("vision")
        if self.supports_audio_input:
            capabilities.append("audio_input")
        if self.supports_audio_output:
            capabilities.append("audio_output")
        if self.supports_video:
            capabilities.append("video")
        if self.supports_reasoning:
            capabilities.append("reasoning")
        if self.supports_predicted_outputs:
            capabilities.append("predicted_outputs")
        if self.supports_embeddings:
            capabilities.append("embeddings")
        if self.supports_moderation:
            capabilities.append("moderation")
        if self.supports_fine_tuning:
            capabilities.append("fine_tuning")
        if self.supports_kv_cache:
            capabilities.append("kv_cache")
        return capabilities

    def clone(self, **overrides) -> "ModelCapabilities":
        """
        Create a copy with optional overrides.

        Args:
            **overrides: Fields to override in the copy

        Returns:
            New ModelCapabilities instance
        """
        # Get all current values
        values = {
            "supports_chat": self.supports_chat,
            "supports_completion": self.supports_completion,
            "supports_streaming": self.supports_streaming,
            "supports_function_calling": self.supports_function_calling,
            "supports_tool_use": self.supports_tool_use,
            "supports_json_mode": self.supports_json_mode,
            "supports_vision": self.supports_vision,
            "supports_audio_input": self.supports_audio_input,
            "supports_audio_output": self.supports_audio_output,
            "supports_video": self.supports_video,
            "supports_reasoning": self.supports_reasoning,
            "supports_predicted_outputs": self.supports_predicted_outputs,
            "supports_embeddings": self.supports_embeddings,
            "supports_moderation": self.supports_moderation,
            "supports_fine_tuning": self.supports_fine_tuning,
            "max_context_length": self.max_context_length,
            "max_output_tokens": self.max_output_tokens,
            "max_batch_size": self.max_batch_size,
            "supports_parallel_tool_calls": self.supports_parallel_tool_calls,
            "latency_profile": self.latency_profile,
            "supports_kv_cache": self.supports_kv_cache,
            "is_moe": self.is_moe,
            "moe_config": self.moe_config,
            "parameter_count": self.parameter_count,
            "provider": self.provider,
            "model_family": self.model_family,
            "description": self.description,
            "tags": self.tags.copy(),
            "custom_metadata": self.custom_metadata.copy(),
        }

        # Apply overrides
        values.update(overrides)

        return ModelCapabilities(**values)


# Latency Presets
LATENCY_PRESETS: dict[str, LatencyProfile] = {
    "small": LatencyProfile(
        time_to_first_token=0.05,
        tokens_per_second=100.0,
        min_delay=0.01,
        max_delay=0.02,
    ),
    "medium": LatencyProfile(
        time_to_first_token=0.1,
        tokens_per_second=50.0,
        min_delay=0.02,
        max_delay=0.05,
    ),
    "large": LatencyProfile(
        time_to_first_token=0.2,
        tokens_per_second=25.0,
        min_delay=0.04,
        max_delay=0.08,
    ),
    "xlarge": LatencyProfile(
        time_to_first_token=0.3,
        tokens_per_second=15.0,
        min_delay=0.06,
        max_delay=0.12,
    ),
    "reasoning": LatencyProfile(
        time_to_first_token=0.5,
        tokens_per_second=10.0,
        min_delay=0.1,
        max_delay=0.2,
    ),
}


# Capability Presets
CAPABILITY_PRESETS: dict[str, ModelCapabilities] = {
    "base": ModelCapabilities(
        supports_chat=True,
        supports_completion=False,
        supports_streaming=True,
        max_context_length=4096,
        max_output_tokens=4096,
        latency_profile=LATENCY_PRESETS["medium"],
    ),
    "chat": ModelCapabilities(
        supports_chat=True,
        supports_completion=False,
        supports_streaming=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        max_context_length=8192,
        max_output_tokens=4096,
        latency_profile=LATENCY_PRESETS["medium"],
    ),
    "vision": ModelCapabilities(
        supports_chat=True,
        supports_completion=False,
        supports_streaming=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=16384,
        max_output_tokens=4096,
        latency_profile=LATENCY_PRESETS["large"],
    ),
    "multimodal": ModelCapabilities(
        supports_chat=True,
        supports_completion=False,
        supports_streaming=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_vision=True,
        supports_audio_input=True,
        supports_audio_output=True,
        max_context_length=32768,
        max_output_tokens=4096,
        latency_profile=LATENCY_PRESETS["xlarge"],
    ),
    "reasoning": ModelCapabilities(
        supports_chat=True,
        supports_completion=False,
        supports_streaming=True,
        supports_reasoning=True,
        supports_predicted_outputs=True,
        max_context_length=65536,
        max_output_tokens=8192,
        latency_profile=LATENCY_PRESETS["reasoning"],
    ),
    "embeddings": ModelCapabilities(
        supports_chat=False,
        supports_completion=False,
        supports_streaming=False,
        supports_embeddings=True,
        max_context_length=8192,
        max_output_tokens=1,
        # Embeddings don't output tokens, but validation requires positive
        # value
        latency_profile=LATENCY_PRESETS["small"],
    ),
    "moderation": ModelCapabilities(
        supports_chat=False,
        supports_completion=False,
        supports_streaming=False,
        supports_moderation=True,
        max_context_length=32768,
        max_output_tokens=1,
        # Moderation doesn't output tokens, but validation requires positive
        # value
        latency_profile=LATENCY_PRESETS["small"],
    ),
}
