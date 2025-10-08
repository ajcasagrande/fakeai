"""
Modular configuration system for FakeAI.

This module provides a composable configuration system.
"""

#  SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Any

from pydantic import Field
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

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


class BackwardCompatEnvSource(PydanticBaseSettingsSource):
    """
    Custom settings source for backward-compatible flat environment variables.

    This source reads environment variables like FAKEAI_HOST and maps them to
    the nested structure (e.g., server.host).
    """

    # Mapping of flat env var names to nested paths
    _ENV_VAR_MAP = {
        # Server config
        "FAKEAI_HOST": ("server", "host"),
        "FAKEAI_PORT": ("server", "port"),
        "FAKEAI_DEBUG": ("server", "debug"),
        "FAKEAI_WORKERS": ("server", "workers"),
        "FAKEAI_RELOAD": ("server", "reload"),
        "FAKEAI_LOG_LEVEL": ("server", "log_level"),
        # Auth config
        "FAKEAI_REQUIRE_API_KEY": ("auth", "require_api_key"),
        "FAKEAI_API_KEYS": ("auth", "api_keys"),
        "FAKEAI_HASH_API_KEYS": ("auth", "hash_api_keys"),
        # Rate limits
        "FAKEAI_RATE_LIMIT_ENABLED": ("rate_limits", "enabled"),
        # KV cache
        "FAKEAI_KV_CACHE_ENABLED": ("kv_cache", "enabled"),
        "FAKEAI_KV_CACHE_BLOCK_SIZE": ("kv_cache", "block_size"),
        "FAKEAI_KV_CACHE_NUM_WORKERS": ("kv_cache", "num_workers"),
        "FAKEAI_KV_OVERLAP_WEIGHT": ("kv_cache", "overlap_weight"),
        # Generation
        "FAKEAI_RESPONSE_DELAY": ("generation", "response_delay"),
        "FAKEAI_RANDOM_DELAY": ("generation", "random_delay"),
        "FAKEAI_MAX_VARIANCE": ("generation", "max_variance"),
        "FAKEAI_TTFT_MS": ("generation", "ttft_ms"),
        "FAKEAI_TTFT_VARIANCE_PERCENT": ("generation", "ttft_variance_percent"),
        "FAKEAI_ITL_MS": ("generation", "itl_ms"),
        "FAKEAI_ITL_VARIANCE_PERCENT": ("generation", "itl_variance_percent"),
        "FAKEAI_USE_LLM_GENERATION": ("generation", "use_llm_generation"),
        "FAKEAI_LLM_MODEL_NAME": ("generation", "llm_model_name"),
        "FAKEAI_LLM_USE_GPU": ("generation", "llm_use_gpu"),
        "FAKEAI_USE_SEMANTIC_EMBEDDINGS": ("generation", "use_semantic_embeddings"),
        "FAKEAI_EMBEDDING_MODEL": ("generation", "embedding_model"),
        "FAKEAI_EMBEDDING_USE_GPU": ("generation", "embedding_use_gpu"),
        "FAKEAI_GENERATE_ACTUAL_IMAGES": ("generation", "generate_actual_images"),
        # Security
        "FAKEAI_ENABLE_INPUT_VALIDATION": ("security", "enable_input_validation"),
        "FAKEAI_ENABLE_INJECTION_DETECTION": ("security", "enable_injection_detection"),
        "FAKEAI_ENABLE_ABUSE_DETECTION": ("security", "enable_abuse_detection"),
        # Storage
        "FAKEAI_IMAGE_STORAGE_BACKEND": ("storage", "image_storage_backend"),
        # Features
        "FAKEAI_ENABLE_MODERATION": ("features", "enable_moderation"),
        "FAKEAI_ENABLE_REFUSALS": ("features", "enable_refusals"),
        "FAKEAI_ENABLE_AUDIO": ("features", "enable_audio"),
        "FAKEAI_ENABLE_JAILBREAK_DETECTION": ("features", "enable_jailbreak_detection"),
        "FAKEAI_ENABLE_SAFETY_FEATURES": ("features", "enable_safety_features"),
        "FAKEAI_MODERATION_THRESHOLD": ("features", "moderation_threshold"),
        "FAKEAI_DEFAULT_VOICE": ("features", "default_voice"),
        "FAKEAI_DEFAULT_AUDIO_FORMAT": ("features", "default_audio_format"),
        "FAKEAI_ENABLE_CONTEXT_VALIDATION": ("features", "enable_context_validation"),
        "FAKEAI_STRICT_TOKEN_COUNTING": ("features", "strict_token_counting"),
        "FAKEAI_ENABLE_PROMPT_CACHING": ("features", "enable_prompt_caching"),
        "FAKEAI_CACHE_TTL_SECONDS": ("features", "cache_ttl_seconds"),
        "FAKEAI_MIN_TOKENS_FOR_CACHE": ("features", "min_tokens_for_cache"),
        "FAKEAI_STREAM_TIMEOUT_SECONDS": ("features", "stream_timeout_seconds"),
        "FAKEAI_STREAM_TOKEN_TIMEOUT_SECONDS": ("features", "stream_token_timeout_seconds"),
        "FAKEAI_STREAM_KEEPALIVE_ENABLED": ("features", "stream_keepalive_enabled"),
        "FAKEAI_STREAM_KEEPALIVE_INTERVAL_SECONDS": ("features", "stream_keepalive_interval_seconds"),
    }

    def get_field_value(self, field: FieldInfo,
                        field_name: str) -> tuple[Any, str, bool]:
        """Not used for this source."""
        return None, "", False

    def __call__(self) -> dict[str, Any]:
        """
        Read flat environment variables and structure them into nested dicts.

        Returns:
            Dictionary with nested structure for AppConfig.
        """
        result: dict[str, dict[str, Any]] = {}

        for env_var, (module_name, field_name) in self._ENV_VAR_MAP.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Initialize nested dict if needed
                if module_name not in result:
                    result[module_name] = {}

                # Try to parse JSON for list/dict types (e.g., api_keys)
                # If it's a valid JSON, use the parsed value, otherwise use raw
                # string
                parsed_value = value
                if value.startswith(('[', '{')) and value.endswith((']', '}')):
                    try:
                        parsed_value = json.loads(value)
                    except json.JSONDecodeError:
                        # Not valid JSON, use raw value and let pydantic handle
                        # it
                        pass

                result[module_name][field_name] = parsed_value

        return result


# Mapping of flat kwargs to their nested config locations
# This is defined outside the class to avoid Pydantic treating it as a field
# Format: {flat_key: (nested_module, nested_key)}
_BACKWARD_COMPAT_MAP: dict[str, tuple[str, str]] = {
    # Server config
    "host": ("server", "host"),
    "port": ("server", "port"),
    "debug": ("server", "debug"),
    "workers": ("server", "workers"),
    "reload": ("server", "reload"),
    "log_level": ("server", "log_level"),
    # Auth config
    "require_api_key": ("auth", "require_api_key"),
    "api_keys": ("auth", "api_keys"),
    "hash_api_keys": ("auth", "hash_api_keys"),
    # Rate limits config
    "rate_limit_enabled": ("rate_limits", "enabled"),
    # KV cache config
    "kv_cache_enabled": ("kv_cache", "enabled"),
    "kv_cache_block_size": ("kv_cache", "block_size"),
    "kv_cache_num_workers": ("kv_cache", "num_workers"),
    "kv_overlap_weight": ("kv_cache", "overlap_weight"),
    # Generation config
    "response_delay": ("generation", "response_delay"),
    "random_delay": ("generation", "random_delay"),
    "max_variance": ("generation", "max_variance"),
    "ttft_ms": ("generation", "ttft_ms"),
    "ttft_variance_percent": ("generation", "ttft_variance_percent"),
    "itl_ms": ("generation", "itl_ms"),
    "itl_variance_percent": ("generation", "itl_variance_percent"),
    "use_llm_generation": ("generation", "use_llm_generation"),
    "llm_model_name": ("generation", "llm_model_name"),
    "llm_use_gpu": ("generation", "llm_use_gpu"),
    "use_semantic_embeddings": ("generation", "use_semantic_embeddings"),
    "embedding_model": ("generation", "embedding_model"),
    "embedding_use_gpu": ("generation", "embedding_use_gpu"),
    "generate_actual_images": ("generation", "generate_actual_images"),
    # Security config
    "enable_input_validation": ("security", "enable_input_validation"),
    "enable_injection_detection": ("security", "enable_injection_detection"),
    "enable_abuse_detection": ("security", "enable_abuse_detection"),
    # Storage config
    "image_storage_backend": ("storage", "image_storage_backend"),
    # Feature flags
    "enable_moderation": ("features", "enable_moderation"),
    "enable_refusals": ("features", "enable_refusals"),
    "enable_audio": ("features", "enable_audio"),
    "enable_jailbreak_detection": ("features", "enable_jailbreak_detection"),
    "enable_safety_features": ("features", "enable_safety_features"),
    "moderation_threshold": ("features", "moderation_threshold"),
    "default_voice": ("features", "default_voice"),
    "default_audio_format": ("features", "default_audio_format"),
    "enable_context_validation": ("features", "enable_context_validation"),
    "strict_token_counting": ("features", "strict_token_counting"),
    "enable_prompt_caching": ("features", "enable_prompt_caching"),
    "cache_ttl_seconds": ("features", "cache_ttl_seconds"),
    "min_tokens_for_cache": ("features", "min_tokens_for_cache"),
    "stream_timeout_seconds": ("features", "stream_timeout_seconds"),
    "stream_token_timeout_seconds": ("features", "stream_token_timeout_seconds"),
    "stream_keepalive_enabled": ("features", "stream_keepalive_enabled"),
    "stream_keepalive_interval_seconds": ("features", "stream_keepalive_interval_seconds"),
}


class AppConfig(BaseSettings):
    """
    Composed application configuration.

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
    """

    model_config = SettingsConfigDict(
        env_prefix="FAKEAI_",
        case_sensitive=False,
        env_nested_delimiter="__",  # Support FAKEAI_SERVER__PORT style
        extra="allow",  # Allow backward compatibility fields
    )

    def __init__(
            self,
            _env_file: Any = None,
            _env_file_encoding: Any = None,
            **kwargs: Any) -> None:
        """
        Initialize AppConfig with backward compatibility for flat kwargs.

        This method intercepts flat kwargs (e.g., port=8000) and routes them
        to the appropriate nested config objects (e.g., server={'port': 8000}).

        Validation is preserved - invalid values will still raise ValidationError.

        Args:
            **kwargs: Configuration values, either flat (backward compat) or nested.

        Examples:
            # Backward compatible flat kwargs
            config = AppConfig(port=8000, host='0.0.0.0')
            config = AppConfig(response_delay=1.5, random_delay=False)

            # New nested structure (also supported)
            config = AppConfig(server={'port': 8000, 'host': '0.0.0.0'})

            # Validation is preserved
            AppConfig(port=99999)  # Raises ValidationError
        """
        # Separate flat backward-compat kwargs from nested kwargs
        nested_kwargs: dict[str, dict[str, Any]] = {}
        remaining_kwargs: dict[str, Any] = {}

        for key, value in kwargs.items():
            if key in _BACKWARD_COMPAT_MAP:
                # This is a flat backward-compat kwarg - route to nested config
                module_name, nested_key = _BACKWARD_COMPAT_MAP[key]

                # Initialize the nested dict if needed
                if module_name not in nested_kwargs:
                    nested_kwargs[module_name] = {}

                # Add the value to the appropriate nested config
                nested_kwargs[module_name][nested_key] = value
            else:
                # Not a backward-compat key - pass through directly
                remaining_kwargs[key] = value

        # Merge nested_kwargs with any explicitly provided nested configs
        # If user provides both flat and nested for same module, nested wins
        for module_name, module_values in nested_kwargs.items():
            if module_name in remaining_kwargs:
                # User provided both flat kwargs and nested dict for this module
                # Merge them, with explicitly provided nested dict taking
                # precedence
                if isinstance(remaining_kwargs[module_name], dict):
                    merged = {**module_values, **remaining_kwargs[module_name]}
                    remaining_kwargs[module_name] = merged
                else:
                    # User provided non-dict value for nested config name
                    # Let pydantic handle the validation error
                    pass
            else:
                # No conflict - add our nested config
                remaining_kwargs[module_name] = module_values

        # Call parent __init__ with the properly structured kwargs
        # This will trigger all pydantic validation
        super().__init__(
            _env_file=_env_file,
            _env_file_encoding=_env_file_encoding,
            **remaining_kwargs)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Customize the settings sources to include backward-compatible env vars.

        Priority order (highest to lowest):
        1. init_settings (explicit kwargs passed to __init__)
        2. env_settings (nested env vars like FAKEAI_SERVER__PORT)
        3. BackwardCompatEnvSource (flat env vars like FAKEAI_PORT)
        4. dotenv_settings (.env file)
        5. file_secret_settings (Docker secrets)
        """
        return (
            init_settings,
            env_settings,
            BackwardCompatEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
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

    # Additional live-configurable fields (not in nested configs)
    dynamo_num_workers: int = Field(default=4, ge=1, le=32)
    dynamo_worker_timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    queue_depth_limit: int = Field(default=1000, ge=1, le=10000)
    load_balance_weight: float = Field(default=0.5, ge=0.0, le=2.0)
    dcgm_num_gpus: int = Field(default=4, ge=1, le=8)
    dcgm_gpu_model: str = Field(default="H100-80GB")
    simulate_dcgm: bool = Field(default=True)

    # Security helper methods
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
        return self.security.enable_security or self.features.enable_moderation

    def is_refusals_enabled(self) -> bool:
        """Check if refusals are enabled (respects master security flag)."""
        return self.security.enable_security or self.features.enable_refusals

    def is_safety_features_enabled(self) -> bool:
        """Check if safety features are enabled (respects master security flag)."""
        return self.security.enable_security or self.features.enable_safety_features

    def is_jailbreak_detection_enabled(self) -> bool:
        """Check if jailbreak detection is enabled (respects master security flag)."""
        return self.security.enable_security or self.features.enable_jailbreak_detection

    def is_api_key_hashing_enabled(self) -> bool:
        """Check if API key hashing is enabled (respects master security flag)."""
        return self.security.enable_security or self.auth.hash_api_keys

    # Backward compatibility properties for generation config
    @property
    def response_delay(self) -> float:
        """Backward compatibility: access generation.response_delay."""
        return self.generation.response_delay

    @response_delay.setter
    def response_delay(self, value: float) -> None:
        """Backward compatibility: set generation.response_delay."""
        self.generation.response_delay = value

    @property
    def random_delay(self) -> bool:
        """Backward compatibility: access generation.random_delay."""
        return self.generation.random_delay

    @random_delay.setter
    def random_delay(self, value: bool) -> None:
        """Backward compatibility: set generation.random_delay."""
        self.generation.random_delay = value

    @property
    def max_variance(self) -> float:
        """Backward compatibility: access generation.max_variance."""
        return self.generation.max_variance

    @max_variance.setter
    def max_variance(self, value: float) -> None:
        """Backward compatibility: set generation.max_variance."""
        self.generation.max_variance = value

    @property
    def ttft_ms(self) -> float:
        """Backward compatibility: access generation.ttft_ms."""
        return self.generation.ttft_ms

    @ttft_ms.setter
    def ttft_ms(self, value: float) -> None:
        """Backward compatibility: set generation.ttft_ms."""
        self.generation.ttft_ms = value

    @property
    def ttft_variance_percent(self) -> float:
        """Backward compatibility: access generation.ttft_variance_percent."""
        return self.generation.ttft_variance_percent

    @ttft_variance_percent.setter
    def ttft_variance_percent(self, value: float) -> None:
        """Backward compatibility: set generation.ttft_variance_percent."""
        self.generation.ttft_variance_percent = value

    @property
    def itl_ms(self) -> float:
        """Backward compatibility: access generation.itl_ms."""
        return self.generation.itl_ms

    @itl_ms.setter
    def itl_ms(self, value: float) -> None:
        """Backward compatibility: set generation.itl_ms."""
        self.generation.itl_ms = value

    @property
    def itl_variance_percent(self) -> float:
        """Backward compatibility: access generation.itl_variance_percent."""
        return self.generation.itl_variance_percent

    @itl_variance_percent.setter
    def itl_variance_percent(self, value: float) -> None:
        """Backward compatibility: set generation.itl_variance_percent."""
        self.generation.itl_variance_percent = value

    @property
    def use_llm_generation(self) -> bool:
        """Backward compatibility: access generation.use_llm_generation."""
        return self.generation.use_llm_generation

    @use_llm_generation.setter
    def use_llm_generation(self, value: bool) -> None:
        """Backward compatibility: set generation.use_llm_generation."""
        self.generation.use_llm_generation = value

    @property
    def llm_model_name(self) -> str:
        """Backward compatibility: access generation.llm_model_name."""
        return self.generation.llm_model_name

    @llm_model_name.setter
    def llm_model_name(self, value: str) -> None:
        """Backward compatibility: set generation.llm_model_name."""
        self.generation.llm_model_name = value

    @property
    def llm_use_gpu(self) -> bool:
        """Backward compatibility: access generation.llm_use_gpu."""
        return self.generation.llm_use_gpu

    @llm_use_gpu.setter
    def llm_use_gpu(self, value: bool) -> None:
        """Backward compatibility: set generation.llm_use_gpu."""
        self.generation.llm_use_gpu = value

    @property
    def use_semantic_embeddings(self) -> bool:
        """Backward compatibility: access generation.use_semantic_embeddings."""
        return self.generation.use_semantic_embeddings

    @use_semantic_embeddings.setter
    def use_semantic_embeddings(self, value: bool) -> None:
        """Backward compatibility: set generation.use_semantic_embeddings."""
        self.generation.use_semantic_embeddings = value

    @property
    def embedding_model(self) -> str:
        """Backward compatibility: access generation.embedding_model."""
        return self.generation.embedding_model

    @embedding_model.setter
    def embedding_model(self, value: str) -> None:
        """Backward compatibility: set generation.embedding_model."""
        self.generation.embedding_model = value

    @property
    def embedding_use_gpu(self) -> bool:
        """Backward compatibility: access generation.embedding_use_gpu."""
        return self.generation.embedding_use_gpu

    @embedding_use_gpu.setter
    def embedding_use_gpu(self, value: bool) -> None:
        """Backward compatibility: set generation.embedding_use_gpu."""
        self.generation.embedding_use_gpu = value

    @property
    def generate_actual_images(self) -> bool:
        """Backward compatibility: access generation.generate_actual_images."""
        return self.generation.generate_actual_images

    @generate_actual_images.setter
    def generate_actual_images(self, value: bool) -> None:
        """Backward compatibility: set generation.generate_actual_images."""
        self.generation.generate_actual_images = value

    # Backward compatibility properties for server config
    @property
    def host(self) -> str:
        """Backward compatibility: access server.host."""
        return self.server.host

    @host.setter
    def host(self, value: str) -> None:
        """Backward compatibility: set server.host."""
        self.server.host = value

    @property
    def port(self) -> int:
        """Backward compatibility: access server.port."""
        return self.server.port

    @port.setter
    def port(self, value: int) -> None:
        """Backward compatibility: set server.port."""
        self.server.port = value

    @property
    def debug(self) -> bool:
        """Backward compatibility: access server.debug."""
        return self.server.debug

    @debug.setter
    def debug(self, value: bool) -> None:
        """Backward compatibility: set server.debug."""
        self.server.debug = value

    # Backward compatibility properties for auth config
    @property
    def require_api_key(self) -> bool:
        """Backward compatibility: access auth.require_api_key."""
        return self.auth.require_api_key

    @require_api_key.setter
    def require_api_key(self, value: bool) -> None:
        """Backward compatibility: set auth.require_api_key."""
        self.auth.require_api_key = value

    @property
    def api_keys(self) -> list[str]:
        """Backward compatibility: access auth.api_keys."""
        return self.auth.api_keys

    @api_keys.setter
    def api_keys(self, value: list[str]) -> None:
        """Backward compatibility: set auth.api_keys."""
        self.auth.api_keys = value

    # Backward compatibility properties for security config
    @property
    def enable_security(self) -> bool:
        """Backward compatibility: access security.enable_security."""
        return self.security.enable_security

    @enable_security.setter
    def enable_security(self, value: bool) -> None:
        """Backward compatibility: set security.enable_security."""
        self.security.enable_security = value

    @property
    def enable_input_validation(self) -> bool:
        """Backward compatibility: access security.enable_input_validation."""
        return self.security.enable_input_validation

    @enable_input_validation.setter
    def enable_input_validation(self, value: bool) -> None:
        """Backward compatibility: set security.enable_input_validation."""
        self.security.enable_input_validation = value

    @property
    def enable_injection_detection(self) -> bool:
        """Backward compatibility: access security.enable_injection_detection."""
        return self.security.enable_injection_detection

    @enable_injection_detection.setter
    def enable_injection_detection(self, value: bool) -> None:
        """Backward compatibility: set security.enable_injection_detection."""
        self.security.enable_injection_detection = value

    @property
    def enable_abuse_detection(self) -> bool:
        """Backward compatibility: access security.enable_abuse_detection."""
        return self.security.enable_abuse_detection

    @enable_abuse_detection.setter
    def enable_abuse_detection(self, value: bool) -> None:
        """Backward compatibility: set security.enable_abuse_detection."""
        self.security.enable_abuse_detection = value

    # Backward compatibility properties for KV cache config
    @property
    def kv_cache_enabled(self) -> bool:
        """Backward compatibility: access kv_cache.enabled."""
        return self.kv_cache.enabled

    @kv_cache_enabled.setter
    def kv_cache_enabled(self, value: bool) -> None:
        """Backward compatibility: set kv_cache.enabled."""
        self.kv_cache.enabled = value

    @property
    def kv_cache_block_size(self) -> int:
        """Backward compatibility: access kv_cache.block_size."""
        return self.kv_cache.block_size

    @kv_cache_block_size.setter
    def kv_cache_block_size(self, value: int) -> None:
        """Backward compatibility: set kv_cache.block_size."""
        self.kv_cache.block_size = value

    @property
    def kv_cache_num_workers(self) -> int:
        """Backward compatibility: access kv_cache.num_workers."""
        return self.kv_cache.num_workers

    @kv_cache_num_workers.setter
    def kv_cache_num_workers(self, value: int) -> None:
        """Backward compatibility: set kv_cache.num_workers."""
        self.kv_cache.num_workers = value

    @property
    def kv_overlap_weight(self) -> float:
        """Backward compatibility: access kv_cache.overlap_weight."""
        return self.kv_cache.overlap_weight

    @kv_overlap_weight.setter
    def kv_overlap_weight(self, value: float) -> None:
        """Backward compatibility: set kv_cache.overlap_weight."""
        self.kv_cache.overlap_weight = value

    # Backward compatibility properties for feature flags
    @property
    def enable_moderation(self) -> bool:
        """Backward compatibility: access features.enable_moderation."""
        return self.features.enable_moderation

    @enable_moderation.setter
    def enable_moderation(self, value: bool) -> None:
        """Backward compatibility: set features.enable_moderation."""
        self.features.enable_moderation = value

    @property
    def enable_refusals(self) -> bool:
        """Backward compatibility: access features.enable_refusals."""
        return self.features.enable_refusals

    @enable_refusals.setter
    def enable_refusals(self, value: bool) -> None:
        """Backward compatibility: set features.enable_refusals."""
        self.features.enable_refusals = value

    @property
    def enable_audio(self) -> bool:
        """Backward compatibility: access features.enable_audio."""
        return self.features.enable_audio

    @enable_audio.setter
    def enable_audio(self, value: bool) -> None:
        """Backward compatibility: set features.enable_audio."""
        self.features.enable_audio = value

    @property
    def enable_jailbreak_detection(self) -> bool:
        """Backward compatibility: access features.enable_jailbreak_detection."""
        return self.features.enable_jailbreak_detection

    @enable_jailbreak_detection.setter
    def enable_jailbreak_detection(self, value: bool) -> None:
        """Backward compatibility: set features.enable_jailbreak_detection."""
        self.features.enable_jailbreak_detection = value

    @property
    def enable_safety_features(self) -> bool:
        """Backward compatibility: access features.enable_safety_features."""
        return self.features.enable_safety_features

    @enable_safety_features.setter
    def enable_safety_features(self, value: bool) -> None:
        """Backward compatibility: set features.enable_safety_features."""
        self.features.enable_safety_features = value

    @property
    def moderation_threshold(self) -> float:
        """Backward compatibility: access features.moderation_threshold."""
        return self.features.moderation_threshold

    @moderation_threshold.setter
    def moderation_threshold(self, value: float) -> None:
        """Backward compatibility: set features.moderation_threshold."""
        self.features.moderation_threshold = value

    @property
    def default_voice(self) -> str:
        """Backward compatibility: access features.default_voice."""
        return self.features.default_voice

    @default_voice.setter
    def default_voice(self, value: str) -> None:
        """Backward compatibility: set features.default_voice."""
        self.features.default_voice = value

    @property
    def default_audio_format(self) -> str:
        """Backward compatibility: access features.default_audio_format."""
        return self.features.default_audio_format

    @default_audio_format.setter
    def default_audio_format(self, value: str) -> None:
        """Backward compatibility: set features.default_audio_format."""
        self.features.default_audio_format = value

    @property
    def enable_context_validation(self) -> bool:
        """Backward compatibility: access features.enable_context_validation."""
        return self.features.enable_context_validation

    @enable_context_validation.setter
    def enable_context_validation(self, value: bool) -> None:
        """Backward compatibility: set features.enable_context_validation."""
        self.features.enable_context_validation = value

    @property
    def strict_token_counting(self) -> bool:
        """Backward compatibility: access features.strict_token_counting."""
        return self.features.strict_token_counting

    @strict_token_counting.setter
    def strict_token_counting(self, value: bool) -> None:
        """Backward compatibility: set features.strict_token_counting."""
        self.features.strict_token_counting = value

    @property
    def enable_prompt_caching(self) -> bool:
        """Backward compatibility: access features.enable_prompt_caching."""
        return self.features.enable_prompt_caching

    @enable_prompt_caching.setter
    def enable_prompt_caching(self, value: bool) -> None:
        """Backward compatibility: set features.enable_prompt_caching."""
        self.features.enable_prompt_caching = value

    @property
    def cache_ttl_seconds(self) -> int:
        """Backward compatibility: access features.cache_ttl_seconds."""
        return self.features.cache_ttl_seconds

    @cache_ttl_seconds.setter
    def cache_ttl_seconds(self, value: int) -> None:
        """Backward compatibility: set features.cache_ttl_seconds."""
        self.features.cache_ttl_seconds = value

    @property
    def min_tokens_for_cache(self) -> int:
        """Backward compatibility: access features.min_tokens_for_cache."""
        return self.features.min_tokens_for_cache

    @min_tokens_for_cache.setter
    def min_tokens_for_cache(self, value: int) -> None:
        """Backward compatibility: set features.min_tokens_for_cache."""
        self.features.min_tokens_for_cache = value

    # Backward compatibility properties for storage config
    @property
    def image_storage_backend(self) -> str:
        """Backward compatibility: access storage.image_storage_backend."""
        return self.storage.image_storage_backend.value

    @image_storage_backend.setter
    def image_storage_backend(self, value: str) -> None:
        """Backward compatibility: set storage.image_storage_backend."""
        from .storage import StorageBackend
        self.storage.image_storage_backend = StorageBackend(value)

    # Backward compatibility properties for rate limiting config
    @property
    def rate_limit_enabled(self) -> bool:
        """Backward compatibility: access rate_limits.enabled."""
        return self.rate_limits.enabled

    @rate_limit_enabled.setter
    def rate_limit_enabled(self, value: bool) -> None:
        """Backward compatibility: set rate_limits.enabled."""
        self.rate_limits.enabled = value

    # Backward compatibility properties for streaming settings (in features)
    @property
    def stream_timeout_seconds(self) -> float:
        """Backward compatibility: access features.stream_timeout_seconds."""
        return self.features.stream_timeout_seconds

    @stream_timeout_seconds.setter
    def stream_timeout_seconds(self, value: float) -> None:
        """Backward compatibility: set features.stream_timeout_seconds."""
        self.features.stream_timeout_seconds = value

    @property
    def stream_token_timeout_seconds(self) -> float:
        """Backward compatibility: access features.stream_token_timeout_seconds."""
        return self.features.stream_token_timeout_seconds

    @stream_token_timeout_seconds.setter
    def stream_token_timeout_seconds(self, value: float) -> None:
        """Backward compatibility: set features.stream_token_timeout_seconds."""
        self.features.stream_token_timeout_seconds = value

    @property
    def stream_keepalive_enabled(self) -> bool:
        """Backward compatibility: access features.stream_keepalive_enabled."""
        return self.features.stream_keepalive_enabled

    @stream_keepalive_enabled.setter
    def stream_keepalive_enabled(self, value: bool) -> None:
        """Backward compatibility: set features.stream_keepalive_enabled."""
        self.features.stream_keepalive_enabled = value

    @property
    def stream_keepalive_interval_seconds(self) -> float:
        """Backward compatibility: access features.stream_keepalive_interval_seconds."""
        return self.features.stream_keepalive_interval_seconds

    @stream_keepalive_interval_seconds.setter
    def stream_keepalive_interval_seconds(self, value: float) -> None:
        """Backward compatibility: set features.stream_keepalive_interval_seconds."""
        self.features.stream_keepalive_interval_seconds = value
