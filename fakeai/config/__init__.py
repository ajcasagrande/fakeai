"""
Modular configuration system for FakeAI.

This module provides a composable configuration system with backward compatibility.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .auth import AuthConfig
from .base import BaseConfig, ModuleConfig
from .features import FeatureFlags
from .generation import GenerationConfig
from .kv_cache import KVCacheConfig
from .metrics import MetricsConfig
from .rate_limits import TIER_LIMITS, RateLimitConfig, RateLimitTier
from .security import SecurityConfig
from .server import LogLevel, ServerConfig
from .storage import StorageBackend, StorageConfig

__all__ = [
    "AppConfig",
    "AuthConfig",
    "BaseConfig",
    "FeatureFlags",
    "GenerationConfig",
    "KVCacheConfig",
    "LogLevel",
    "MetricsConfig",
    "ModuleConfig",
    "RateLimitConfig",
    "RateLimitTier",
    "SecurityConfig",
    "ServerConfig",
    "StorageBackend",
    "StorageConfig",
    "TIER_LIMITS",
]

# Mapping of flat field names to (module, field_name) for backward compatibility
_FLAT_TO_NESTED_MAPPING = {
    # Server fields
    "host": ("server", "host"),
    "port": ("server", "port"),
    "debug": ("server", "debug"),
    # Auth fields
    "require_api_key": ("auth", "require_api_key"),
    "api_keys": ("auth", "api_keys"),
    "hash_api_keys": ("auth", "hash_api_keys"),
    # Rate limit fields
    "rate_limit_enabled": ("rate_limits", "enabled"),
    "rate_limit_tier": ("rate_limits", "tier"),
    "rate_limit_rpm": ("rate_limits", "rpm_override"),
    "rate_limit_tpm": ("rate_limits", "tpm_override"),
    # KV cache fields
    "kv_cache_enabled": ("kv_cache", "enabled"),
    "kv_cache_block_size": ("kv_cache", "block_size"),
    "kv_cache_num_workers": ("kv_cache", "num_workers"),
    "kv_overlap_weight": ("kv_cache", "overlap_weight"),
    # Generation fields
    "use_llm_generation": ("generation", "use_llm_generation"),
    "llm_model_name": ("generation", "llm_model_name"),
    "llm_use_gpu": ("generation", "llm_use_gpu"),
    "use_semantic_embeddings": ("generation", "use_semantic_embeddings"),
    "embedding_model": ("generation", "embedding_model"),
    "embedding_use_gpu": ("generation", "embedding_use_gpu"),
    "generate_actual_images": ("generation", "generate_actual_images"),
    "response_delay": ("generation", "response_delay"),
    "random_delay": ("generation", "random_delay"),
    "max_variance": ("generation", "max_variance"),
    "ttft_ms": ("generation", "ttft_ms"),
    "ttft_variance_percent": ("generation", "ttft_variance_percent"),
    "itl_ms": ("generation", "itl_ms"),
    "itl_variance_percent": ("generation", "itl_variance_percent"),
    # Storage fields
    "file_storage_backend": ("storage", "file_storage_backend"),
    "file_storage_path": ("storage", "file_storage_path"),
    "file_cleanup_enabled": ("storage", "file_cleanup_enabled"),
    "image_storage_backend": ("storage", "image_storage_backend"),
    "image_retention_hours": ("storage", "image_retention_hours"),
    # Security fields
    "enable_security": ("security", "enable_security"),
    "enable_input_validation": ("security", "enable_input_validation"),
    "enable_injection_detection": ("security", "enable_injection_detection"),
    "max_request_size": ("security", "max_request_size"),
    "enable_abuse_detection": ("security", "enable_abuse_detection"),
    "abuse_cleanup_interval": ("security", "abuse_cleanup_interval"),
    "cors_allowed_origins": ("security", "cors_allowed_origins"),
    "cors_allow_credentials": ("security", "cors_allow_credentials"),
    # Feature fields
    "enable_prompt_caching": ("features", "enable_prompt_caching"),
    "cache_ttl_seconds": ("features", "cache_ttl_seconds"),
    "min_tokens_for_cache": ("features", "min_tokens_for_cache"),
    "enable_moderation": ("features", "enable_moderation"),
    "moderation_threshold": ("features", "moderation_threshold"),
    "enable_refusals": ("features", "enable_refusals"),
    "enable_safety_features": ("features", "enable_safety_features"),
    "enable_jailbreak_detection": ("features", "enable_jailbreak_detection"),
    "prepend_safety_message": ("features", "prepend_safety_message"),
    "enable_audio": ("features", "enable_audio"),
    "default_voice": ("features", "default_voice"),
    "default_audio_format": ("features", "default_audio_format"),
    "enable_context_validation": ("features", "enable_context_validation"),
    "strict_token_counting": ("features", "strict_token_counting"),
    "stream_timeout_seconds": ("features", "stream_timeout_seconds"),
    "stream_token_timeout_seconds": ("features", "stream_token_timeout_seconds"),
    "stream_keepalive_enabled": ("features", "stream_keepalive_enabled"),
    "stream_keepalive_interval_seconds": (
        "features",
        "stream_keepalive_interval_seconds",
    ),
    # Metrics fields
    "error_injection_enabled": ("metrics", "error_injection_enabled"),
    "error_injection_rate": ("metrics", "error_injection_rate"),
    "error_injection_types": ("metrics", "error_injection_types"),
}


class AppConfig(BaseSettings):
    """
    Composed application configuration with backward compatibility.

    This configuration system is modular, with separate configs for:
    - server: Server settings (host, port, workers, etc.)
    - auth: Authentication settings (API keys, etc.)
    - rate_limits: Rate limiting configuration
    - kv_cache: KV cache and smart routing
    - generation: Response generation settings
    - metrics: Metrics and monitoring
    - storage: File and image storage backends
    - security: Security features (CORS, abuse detection, etc.)
    - features: Feature flags for optional functionality

    Access nested configs via dot notation:
        config.server.port
        config.auth.require_api_key
        config.rate_limits.enabled

    For backward compatibility, top-level property accessors are provided.
    """

    model_config = SettingsConfigDict(
        env_prefix="FAKEAI_",
        case_sensitive=False,
        env_nested_delimiter="__",  # Support FAKEAI_SERVER__PORT style
        extra="allow",  # Allow extra fields for backward compatibility
    )

    # Modular configuration sections
    server: ServerConfig = Field(default_factory=ServerConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    rate_limits: RateLimitConfig = Field(default_factory=RateLimitConfig)
    kv_cache: KVCacheConfig = Field(default_factory=KVCacheConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    @model_validator(mode="before")
    @classmethod
    def map_flat_to_nested(cls, data: Any) -> Any:
        """Map flat configuration parameters to nested structure for backward compatibility."""
        if not isinstance(data, dict):
            return data

        # Use the module-level mapping
        mapping = _FLAT_TO_NESTED_MAPPING

        # Create nested structure from flat parameters
        nested_data = {}
        extra_fields = {}

        for key, value in data.items():
            if key in mapping:
                module_name, field_name = mapping[key]
                if module_name not in nested_data:
                    nested_data[module_name] = {}
                nested_data[module_name][field_name] = value
            else:
                # Keep non-mapped fields as-is (for nested access or extra fields)
                extra_fields[key] = value

        # Merge nested data with extra fields
        result = {**extra_fields}
        for module_name, module_data in nested_data.items():
            if module_name in result:
                # Merge with existing module data
                if isinstance(result[module_name], dict):
                    result[module_name] = {**result[module_name], **module_data}
            else:
                result[module_name] = module_data

        return result

    # Backward compatibility properties - Server
    @property
    def host(self) -> str:
        """Backward compatibility: access server.host."""
        return self.server.host

    @property
    def port(self) -> int:
        """Backward compatibility: access server.port."""
        return self.server.port

    @property
    def debug(self) -> bool:
        """Backward compatibility: access server.debug."""
        return self.server.debug

    # Backward compatibility properties - Auth
    @property
    def require_api_key(self) -> bool:
        """Backward compatibility: access auth.require_api_key."""
        return self.auth.require_api_key

    @property
    def api_keys(self) -> list[str]:
        """Backward compatibility: access auth.api_keys."""
        return self.auth.api_keys

    @property
    def hash_api_keys(self) -> bool:
        """Backward compatibility: access auth.hash_api_keys."""
        return self.auth.hash_api_keys

    # Backward compatibility properties - Rate Limits
    @property
    def rate_limit_enabled(self) -> bool:
        """Backward compatibility: access rate_limits.enabled."""
        return self.rate_limits.enabled

    @property
    def rate_limit_tier(self) -> str:
        """Backward compatibility: access rate_limits.tier."""
        return self.rate_limits.tier.value

    @property
    def rate_limit_rpm(self) -> int | None:
        """Backward compatibility: access rate_limits.rpm_override."""
        return self.rate_limits.rpm_override

    @property
    def rate_limit_tpm(self) -> int | None:
        """Backward compatibility: access rate_limits.tpm_override."""
        return self.rate_limits.tpm_override

    # Backward compatibility properties - KV Cache
    @property
    def kv_cache_enabled(self) -> bool:
        """Backward compatibility: access kv_cache.enabled."""
        return self.kv_cache.enabled

    @property
    def kv_cache_block_size(self) -> int:
        """Backward compatibility: access kv_cache.block_size."""
        return self.kv_cache.block_size

    @property
    def kv_cache_num_workers(self) -> int:
        """Backward compatibility: access kv_cache.num_workers."""
        return self.kv_cache.num_workers

    @property
    def kv_overlap_weight(self) -> float:
        """Backward compatibility: access kv_cache.overlap_weight."""
        return self.kv_cache.overlap_weight

    # Backward compatibility properties - Generation
    @property
    def use_llm_generation(self) -> bool:
        """Backward compatibility: access generation.use_llm_generation."""
        return self.generation.use_llm_generation

    @property
    def llm_model_name(self) -> str:
        """Backward compatibility: access generation.llm_model_name."""
        return self.generation.llm_model_name

    @property
    def llm_use_gpu(self) -> bool:
        """Backward compatibility: access generation.llm_use_gpu."""
        return self.generation.llm_use_gpu

    @property
    def use_semantic_embeddings(self) -> bool:
        """Backward compatibility: access generation.use_semantic_embeddings."""
        return self.generation.use_semantic_embeddings

    @property
    def embedding_model(self) -> str:
        """Backward compatibility: access generation.embedding_model."""
        return self.generation.embedding_model

    @property
    def embedding_use_gpu(self) -> bool:
        """Backward compatibility: access generation.embedding_use_gpu."""
        return self.generation.embedding_use_gpu

    @property
    def generate_actual_images(self) -> bool:
        """Backward compatibility: access generation.generate_actual_images."""
        return self.generation.generate_actual_images

    @property
    def response_delay(self) -> float:
        """Backward compatibility: access generation.response_delay."""
        return self.generation.response_delay

    @property
    def random_delay(self) -> bool:
        """Backward compatibility: access generation.random_delay."""
        return self.generation.random_delay

    @property
    def max_variance(self) -> float:
        """Backward compatibility: access generation.max_variance."""
        return self.generation.max_variance

    @property
    def ttft_ms(self) -> float:
        """Backward compatibility: access generation.ttft_ms."""
        return self.generation.ttft_ms

    @property
    def ttft_variance_percent(self) -> float:
        """Backward compatibility: access generation.ttft_variance_percent."""
        return self.generation.ttft_variance_percent

    @property
    def itl_ms(self) -> float:
        """Backward compatibility: access generation.itl_ms."""
        return self.generation.itl_ms

    @property
    def itl_variance_percent(self) -> float:
        """Backward compatibility: access generation.itl_variance_percent."""
        return self.generation.itl_variance_percent

    # Backward compatibility properties - Storage
    @property
    def file_storage_backend(self) -> str:
        """Backward compatibility: access storage.file_storage_backend."""
        return self.storage.file_storage_backend.value

    @property
    def file_storage_path(self) -> str | None:
        """Backward compatibility: access storage.file_storage_path."""
        return self.storage.file_storage_path

    @property
    def file_cleanup_enabled(self) -> bool:
        """Backward compatibility: access storage.file_cleanup_enabled."""
        return self.storage.file_cleanup_enabled

    @property
    def image_storage_backend(self) -> str:
        """Backward compatibility: access storage.image_storage_backend."""
        return self.storage.image_storage_backend.value

    @property
    def image_retention_hours(self) -> int:
        """Backward compatibility: access storage.image_retention_hours."""
        return self.storage.image_retention_hours

    # Backward compatibility properties - Security
    @property
    def enable_security(self) -> bool:
        """Backward compatibility: access security.enable_security."""
        return self.security.enable_security

    @property
    def enable_input_validation(self) -> bool:
        """Backward compatibility: access security.enable_input_validation."""
        return self.security.enable_input_validation

    @property
    def enable_injection_detection(self) -> bool:
        """Backward compatibility: access security.enable_injection_detection."""
        return self.security.enable_injection_detection

    @property
    def max_request_size(self) -> int:
        """Backward compatibility: access security.max_request_size."""
        return self.security.max_request_size

    @property
    def enable_abuse_detection(self) -> bool:
        """Backward compatibility: access security.enable_abuse_detection."""
        return self.security.enable_abuse_detection

    @property
    def abuse_cleanup_interval(self) -> int:
        """Backward compatibility: access security.abuse_cleanup_interval."""
        return self.security.abuse_cleanup_interval

    @property
    def cors_allowed_origins(self) -> list[str]:
        """Backward compatibility: access security.cors_allowed_origins."""
        return self.security.cors_allowed_origins

    @property
    def cors_allow_credentials(self) -> bool:
        """Backward compatibility: access security.cors_allow_credentials."""
        return self.security.cors_allow_credentials

    # Backward compatibility properties - Features
    @property
    def enable_prompt_caching(self) -> bool:
        """Backward compatibility: access features.enable_prompt_caching."""
        return self.features.enable_prompt_caching

    @property
    def cache_ttl_seconds(self) -> int:
        """Backward compatibility: access features.cache_ttl_seconds."""
        return self.features.cache_ttl_seconds

    @property
    def min_tokens_for_cache(self) -> int:
        """Backward compatibility: access features.min_tokens_for_cache."""
        return self.features.min_tokens_for_cache

    @property
    def enable_moderation(self) -> bool:
        """Backward compatibility: access features.enable_moderation."""
        return self.features.enable_moderation

    @property
    def moderation_threshold(self) -> float:
        """Backward compatibility: access features.moderation_threshold."""
        return self.features.moderation_threshold

    @property
    def enable_refusals(self) -> bool:
        """Backward compatibility: access features.enable_refusals."""
        return self.features.enable_refusals

    @property
    def enable_safety_features(self) -> bool:
        """Backward compatibility: access features.enable_safety_features."""
        return self.features.enable_safety_features

    @property
    def enable_jailbreak_detection(self) -> bool:
        """Backward compatibility: access features.enable_jailbreak_detection."""
        return self.features.enable_jailbreak_detection

    @property
    def prepend_safety_message(self) -> bool:
        """Backward compatibility: access features.prepend_safety_message."""
        return self.features.prepend_safety_message

    @property
    def enable_audio(self) -> bool:
        """Backward compatibility: access features.enable_audio."""
        return self.features.enable_audio

    @property
    def default_voice(self) -> str:
        """Backward compatibility: access features.default_voice."""
        return self.features.default_voice

    @property
    def default_audio_format(self) -> str:
        """Backward compatibility: access features.default_audio_format."""
        return self.features.default_audio_format

    @property
    def enable_context_validation(self) -> bool:
        """Backward compatibility: access features.enable_context_validation."""
        return self.features.enable_context_validation

    @property
    def strict_token_counting(self) -> bool:
        """Backward compatibility: access features.strict_token_counting."""
        return self.features.strict_token_counting

    @property
    def stream_timeout_seconds(self) -> float:
        """Backward compatibility: access features.stream_timeout_seconds."""
        return self.features.stream_timeout_seconds

    @property
    def stream_token_timeout_seconds(self) -> float:
        """Backward compatibility: access features.stream_token_timeout_seconds."""
        return self.features.stream_token_timeout_seconds

    @property
    def stream_keepalive_enabled(self) -> bool:
        """Backward compatibility: access features.stream_keepalive_enabled."""
        return self.features.stream_keepalive_enabled

    @property
    def stream_keepalive_interval_seconds(self) -> float:
        """Backward compatibility: access features.stream_keepalive_interval_seconds."""
        return self.features.stream_keepalive_interval_seconds

    # Backward compatibility properties - Metrics
    @property
    def error_injection_enabled(self) -> bool:
        """Backward compatibility: access metrics.error_injection_enabled."""
        return self.metrics.error_injection_enabled

    @property
    def error_injection_rate(self) -> float:
        """Backward compatibility: access metrics.error_injection_rate."""
        return self.metrics.error_injection_rate

    @property
    def error_injection_types(self) -> list[str]:
        """Backward compatibility: access metrics.error_injection_types."""
        return self.metrics.error_injection_types

    # Backward compatibility methods - Security
    def is_input_validation_enabled(self) -> bool:
        """Check if input validation is enabled (respects master security flag)."""
        return self.security.is_input_validation_enabled()

    def is_injection_detection_enabled(self) -> bool:
        """Check if injection detection is enabled (respects master security flag)."""
        return self.security.is_injection_detection_enabled()

    def is_abuse_detection_enabled(self) -> bool:
        """Check if abuse detection is enabled (respects master security flag)."""
        return self.security.is_abuse_detection_enabled()

    def is_moderation_enabled(self) -> bool:
        """Check if content moderation is enabled (respects master security flag)."""
        return self.enable_security or self.enable_moderation

    def is_refusals_enabled(self) -> bool:
        """Check if refusals are enabled (respects master security flag)."""
        return self.enable_security or self.enable_refusals

    def is_safety_features_enabled(self) -> bool:
        """Check if safety features are enabled (respects master security flag)."""
        return self.enable_security or self.enable_safety_features

    def is_jailbreak_detection_enabled(self) -> bool:
        """Check if jailbreak detection is enabled (respects master security flag)."""
        return self.enable_security or self.enable_jailbreak_detection

    def is_api_key_hashing_enabled(self) -> bool:
        """Check if API key hashing is enabled (respects master security flag)."""
        return self.enable_security or self.hash_api_keys
