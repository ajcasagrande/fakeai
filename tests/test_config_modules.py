"""
Modular configuration system tests.

Tests the new modular configuration structure with comprehensive coverage.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.config import (
    TIER_LIMITS,
    AppConfig,
    AuthConfig,
    FeatureFlags,
    GenerationConfig,
    KVCacheConfig,
    LogLevel,
    MetricsConfig,
    RateLimitConfig,
    RateLimitTier,
    SecurityConfig,
    ServerConfig,
    StorageBackend,
    StorageConfig,
)


@pytest.mark.unit
class TestServerConfig:
    """Test ServerConfig module."""

    def test_default_values(self):
        """Test default server configuration values."""
        config = ServerConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.debug is False
        assert config.workers == 1
        assert config.reload is False
        assert config.log_level == LogLevel.INFO

    def test_port_validation_minimum(self):
        """Test port validation rejects values below 1."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ServerConfig(port=0)

    def test_port_validation_maximum(self):
        """Test port validation rejects values above 65535."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ServerConfig(port=65536)

    def test_port_validation_valid_range(self):
        """Test port validation accepts valid values."""
        config_low = ServerConfig(port=1)
        config_high = ServerConfig(port=65535)
        config_mid = ServerConfig(port=8080)
        assert config_low.port == 1
        assert config_high.port == 65535
        assert config_mid.port == 8080

    def test_workers_validation_minimum(self):
        """Test workers validation rejects values below 1."""
        with pytest.raises(ValueError, match="Number of workers must be at least 1"):
            ServerConfig(workers=0)

    def test_workers_validation_maximum(self):
        """Test workers validation rejects values above 128."""
        with pytest.raises(ValueError, match="Number of workers cannot exceed 128"):
            ServerConfig(workers=129)

    def test_log_level_validation_string(self):
        """Test log level accepts string values."""
        config = ServerConfig(log_level="debug")
        assert config.log_level == LogLevel.DEBUG

    def test_log_level_validation_enum(self):
        """Test log level accepts enum values."""
        config = ServerConfig(log_level=LogLevel.ERROR)
        assert config.log_level == LogLevel.ERROR

    def test_log_level_validation_invalid(self):
        """Test log level rejects invalid values."""
        with pytest.raises(ValueError, match="Log level must be one of"):
            ServerConfig(log_level="invalid")


@pytest.mark.unit
class TestAuthConfig:
    """Test AuthConfig module."""

    def test_default_values(self):
        """Test default authentication configuration values."""
        config = AuthConfig()
        assert config.require_api_key is False
        assert config.api_keys == []
        assert config.hash_api_keys is False

    def test_api_key_validation_empty_string(self):
        """Test API key validation rejects empty strings."""
        with pytest.raises(ValueError, match="API keys must be non-empty strings"):
            AuthConfig(api_keys=[""])

    def test_api_key_validation_short_keys(self):
        """Test API key validation rejects keys shorter than 8 characters."""
        with pytest.raises(ValueError, match="API keys must be at least 8 characters"):
            AuthConfig(api_keys=["short"])

    def test_api_key_validation_weak_keys_warning(self, caplog):
        """Test API key validation warns about weak test keys."""
        import logging

        caplog.set_level(logging.WARNING, logger="fakeai.config.auth")
        config = AuthConfig(api_keys=["password"])
        assert "weak test key" in caplog.text.lower()

    def test_api_key_validation_valid_keys(self):
        """Test API key validation accepts valid keys."""
        config = AuthConfig(api_keys=["validkey123", "anotherkey456"])
        assert len(config.api_keys) == 2


@pytest.mark.unit
class TestRateLimitConfig:
    """Test RateLimitConfig module."""

    def test_default_values(self):
        """Test default rate limit configuration values."""
        config = RateLimitConfig()
        assert config.enabled is False
        assert config.tier == RateLimitTier.TIER_1
        assert config.rpm_override is None
        assert config.tpm_override is None

    def test_tier_validation_string(self):
        """Test tier accepts string values."""
        config = RateLimitConfig(tier="tier-2")
        assert config.tier == RateLimitTier.TIER_2

    def test_tier_validation_enum(self):
        """Test tier accepts enum values."""
        config = RateLimitConfig(tier=RateLimitTier.TIER_3)
        assert config.tier == RateLimitTier.TIER_3

    def test_tier_validation_underscore_format(self):
        """Test tier accepts underscore format."""
        config = RateLimitConfig(tier="tier_4")
        assert config.tier == RateLimitTier.TIER_4

    def test_tier_validation_invalid(self):
        """Test tier rejects invalid values."""
        with pytest.raises(ValueError, match="Rate limit tier must be one of"):
            RateLimitConfig(tier="invalid-tier")

    def test_rpm_override_validation_negative(self):
        """Test RPM override rejects negative values."""
        with pytest.raises(ValueError, match="RPM override must be at least 1"):
            RateLimitConfig(rpm_override=0)

    def test_tpm_override_validation_negative(self):
        """Test TPM override rejects negative values."""
        with pytest.raises(ValueError, match="TPM override must be at least 1"):
            RateLimitConfig(tpm_override=0)

    def test_get_rpm_limit_from_tier(self):
        """Test get_rpm_limit returns tier limit when no override."""
        config = RateLimitConfig(tier=RateLimitTier.TIER_2)
        assert config.get_rpm_limit() == TIER_LIMITS[RateLimitTier.TIER_2][0]

    def test_get_rpm_limit_from_override(self):
        """Test get_rpm_limit returns override when set."""
        config = RateLimitConfig(rpm_override=1000)
        assert config.get_rpm_limit() == 1000

    def test_get_tpm_limit_from_tier(self):
        """Test get_tpm_limit returns tier limit when no override."""
        config = RateLimitConfig(tier=RateLimitTier.TIER_3)
        assert config.get_tpm_limit() == TIER_LIMITS[RateLimitTier.TIER_3][1]

    def test_get_tpm_limit_from_override(self):
        """Test get_tpm_limit returns override when set."""
        config = RateLimitConfig(tpm_override=5000000)
        assert config.get_tpm_limit() == 5000000


@pytest.mark.unit
class TestKVCacheConfig:
    """Test KVCacheConfig module."""

    def test_default_values(self):
        """Test default KV cache configuration values."""
        config = KVCacheConfig()
        assert config.enabled is True
        assert config.block_size == 16
        assert config.num_workers == 4
        assert config.overlap_weight == 1.0
        assert config.load_balance_weight == 0.5

    def test_block_size_validation_minimum(self):
        """Test block size rejects values below 1."""
        with pytest.raises(ValueError, match="KV cache block size must be at least 1"):
            KVCacheConfig(block_size=0)

    def test_block_size_validation_maximum(self):
        """Test block size rejects values above 128."""
        with pytest.raises(ValueError, match="KV cache block size cannot exceed 128"):
            KVCacheConfig(block_size=129)

    def test_num_workers_validation_minimum(self):
        """Test num workers rejects values below 1."""
        with pytest.raises(
            ValueError, match="KV cache number of workers must be at least 1"
        ):
            KVCacheConfig(num_workers=0)

    def test_num_workers_validation_maximum(self):
        """Test num workers rejects values above 64."""
        with pytest.raises(
            ValueError, match="KV cache number of workers cannot exceed 64"
        ):
            KVCacheConfig(num_workers=65)

    def test_overlap_weight_validation_minimum(self):
        """Test overlap weight rejects values below 0.0."""
        with pytest.raises(
            ValueError, match="KV overlap weight must be between 0.0 and 2.0"
        ):
            KVCacheConfig(overlap_weight=-0.1)

    def test_overlap_weight_validation_maximum(self):
        """Test overlap weight rejects values above 2.0."""
        with pytest.raises(
            ValueError, match="KV overlap weight must be between 0.0 and 2.0"
        ):
            KVCacheConfig(overlap_weight=2.1)

    def test_load_balance_weight_validation_minimum(self):
        """Test load balance weight rejects values below 0.0."""
        with pytest.raises(
            ValueError, match="Load balance weight must be between 0.0 and 2.0"
        ):
            KVCacheConfig(load_balance_weight=-0.1)

    def test_load_balance_weight_validation_maximum(self):
        """Test load balance weight rejects values above 2.0."""
        with pytest.raises(
            ValueError, match="Load balance weight must be between 0.0 and 2.0"
        ):
            KVCacheConfig(load_balance_weight=2.1)


@pytest.mark.unit
class TestGenerationConfig:
    """Test GenerationConfig module."""

    def test_default_values(self):
        """Test default generation configuration values."""
        config = GenerationConfig()
        assert config.use_llm_generation is False
        assert config.llm_model_name == "distilgpt2"
        assert config.llm_use_gpu is True
        assert config.use_semantic_embeddings is False
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.embedding_use_gpu is True
        assert config.generate_actual_images is True
        assert config.response_delay == 0.5
        assert config.random_delay is True
        assert config.max_variance == 0.3
        assert config.ttft_ms == 20.0
        assert config.ttft_variance_percent == 10.0
        assert config.itl_ms == 5.0
        assert config.itl_variance_percent == 10.0

    def test_response_delay_validation_negative(self):
        """Test response delay rejects negative values."""
        with pytest.raises(ValueError, match="Response delay cannot be negative"):
            GenerationConfig(response_delay=-1.0)

    def test_max_variance_validation_negative(self):
        """Test max variance rejects negative values."""
        with pytest.raises(ValueError, match="Max variance cannot be negative"):
            GenerationConfig(max_variance=-0.1)

    def test_embedding_model_validation_custom_warning(self, caplog):
        """Test embedding model validation warns about custom models."""
        config = GenerationConfig(embedding_model="custom-model")
        assert "custom embedding model" in caplog.text.lower()


@pytest.mark.unit
class TestStorageConfig:
    """Test StorageConfig module."""

    def test_default_values(self):
        """Test default storage configuration values."""
        config = StorageConfig()
        assert config.file_storage_backend == StorageBackend.MEMORY
        assert config.file_storage_path is None
        assert config.file_cleanup_enabled is True
        assert config.file_retention_hours == 24
        assert config.image_storage_backend == StorageBackend.MEMORY
        assert config.image_storage_path is None
        assert config.image_retention_hours == 1

    def test_storage_backend_validation_string(self):
        """Test storage backend accepts string values."""
        config = StorageConfig(file_storage_backend="disk")
        assert config.file_storage_backend == StorageBackend.DISK

    def test_storage_backend_validation_enum(self):
        """Test storage backend accepts enum values."""
        config = StorageConfig(image_storage_backend=StorageBackend.DISK)
        assert config.image_storage_backend == StorageBackend.DISK

    def test_storage_backend_validation_invalid(self):
        """Test storage backend rejects invalid values."""
        with pytest.raises(ValueError, match="Storage backend must be one of"):
            StorageConfig(file_storage_backend="invalid")

    def test_file_retention_hours_validation_negative(self):
        """Test file retention hours rejects negative values."""
        with pytest.raises(ValueError, match="File retention hours cannot be negative"):
            StorageConfig(file_retention_hours=-1)

    def test_file_retention_hours_validation_maximum(self):
        """Test file retention hours rejects values above 168."""
        with pytest.raises(ValueError, match="File retention hours cannot exceed 168"):
            StorageConfig(file_retention_hours=169)

    def test_image_retention_hours_validation_negative(self):
        """Test image retention hours rejects negative values."""
        with pytest.raises(
            ValueError, match="Image retention hours cannot be negative"
        ):
            StorageConfig(image_retention_hours=-1)

    def test_image_retention_hours_validation_maximum(self):
        """Test image retention hours rejects values above 168."""
        with pytest.raises(ValueError, match="Image retention hours cannot exceed 168"):
            StorageConfig(image_retention_hours=169)


@pytest.mark.unit
class TestSecurityConfig:
    """Test SecurityConfig module."""

    def test_default_values(self):
        """Test default security configuration values."""
        config = SecurityConfig()
        assert config.enable_security is False
        assert config.enable_input_validation is False
        assert config.enable_injection_detection is False
        assert config.max_request_size == 100 * 1024 * 1024
        assert config.enable_abuse_detection is False
        assert config.abuse_cleanup_interval == 3600
        assert config.cors_allowed_origins == ["*"]
        assert config.cors_allow_credentials is True

    def test_max_request_size_validation_minimum(self):
        """Test max request size rejects values below 1KB."""
        with pytest.raises(
            ValueError, match="Maximum request size must be at least 1024 bytes"
        ):
            SecurityConfig(max_request_size=1023)

    def test_max_request_size_validation_maximum(self):
        """Test max request size rejects values above 100MB."""
        with pytest.raises(
            ValueError, match="Maximum request size cannot exceed 100 MB"
        ):
            SecurityConfig(max_request_size=101 * 1024 * 1024)

    def test_abuse_cleanup_interval_validation_minimum(self):
        """Test abuse cleanup interval rejects values below 60."""
        with pytest.raises(
            ValueError, match="Abuse cleanup interval must be at least 60 seconds"
        ):
            SecurityConfig(abuse_cleanup_interval=59)

    def test_cors_allowed_origins_validation_empty(self):
        """Test CORS allowed origins rejects empty list."""
        with pytest.raises(ValueError, match="CORS allowed origins cannot be empty"):
            SecurityConfig(cors_allowed_origins=[])

    def test_security_flag_methods(self):
        """Test security flag helper methods."""
        config = SecurityConfig()
        assert config.is_input_validation_enabled() is False
        assert config.is_injection_detection_enabled() is False
        assert config.is_abuse_detection_enabled() is False

        config_with_master = SecurityConfig(enable_security=True)
        assert config_with_master.is_input_validation_enabled() is True
        assert config_with_master.is_injection_detection_enabled() is True
        assert config_with_master.is_abuse_detection_enabled() is True


@pytest.mark.unit
class TestFeatureFlags:
    """Test FeatureFlags module."""

    def test_default_values(self):
        """Test default feature flags values."""
        config = FeatureFlags()
        assert config.enable_prompt_caching is True
        assert config.cache_ttl_seconds == 600
        assert config.min_tokens_for_cache == 1024
        assert config.enable_moderation is False
        assert config.moderation_threshold == 0.5
        assert config.enable_refusals is False
        assert config.enable_safety_features is False
        assert config.enable_jailbreak_detection is False
        assert config.prepend_safety_message is False
        assert config.enable_audio is True
        assert config.default_voice == "alloy"
        assert config.default_audio_format == "mp3"
        assert config.enable_context_validation is True
        assert config.strict_token_counting is False
        assert config.stream_timeout_seconds == 300.0
        assert config.stream_token_timeout_seconds == 30.0
        assert config.stream_keepalive_enabled is True
        assert config.stream_keepalive_interval_seconds == 15.0

    def test_cache_ttl_validation_negative(self):
        """Test cache TTL rejects negative values."""
        with pytest.raises(ValueError, match="Cache TTL cannot be negative"):
            FeatureFlags(cache_ttl_seconds=-1)

    def test_min_tokens_for_cache_validation_negative(self):
        """Test min tokens for cache rejects negative values."""
        with pytest.raises(
            ValueError, match="Minimum tokens for cache cannot be negative"
        ):
            FeatureFlags(min_tokens_for_cache=-1)

    def test_moderation_threshold_validation_minimum(self):
        """Test moderation threshold rejects values below 0.0."""
        with pytest.raises(
            ValueError, match="Moderation threshold must be between 0.0 and 1.0"
        ):
            FeatureFlags(moderation_threshold=-0.1)

    def test_moderation_threshold_validation_maximum(self):
        """Test moderation threshold rejects values above 1.0."""
        with pytest.raises(
            ValueError, match="Moderation threshold must be between 0.0 and 1.0"
        ):
            FeatureFlags(moderation_threshold=1.1)

    def test_default_voice_validation_valid_voices(self):
        """Test default voice accepts all valid voices."""
        valid_voices = [
            "alloy",
            "ash",
            "ballad",
            "coral",
            "echo",
            "fable",
            "onyx",
            "nova",
            "shimmer",
            "sage",
            "verse",
        ]
        for voice in valid_voices:
            config = FeatureFlags(default_voice=voice)
            assert config.default_voice == voice

    def test_default_voice_validation_invalid(self):
        """Test default voice rejects invalid values."""
        with pytest.raises(ValueError, match="Default voice must be one of"):
            FeatureFlags(default_voice="invalid_voice")

    def test_default_audio_format_validation_valid_formats(self):
        """Test default audio format accepts all valid formats."""
        valid_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm16"]
        for fmt in valid_formats:
            config = FeatureFlags(default_audio_format=fmt)
            assert config.default_audio_format == fmt

    def test_default_audio_format_validation_invalid(self):
        """Test default audio format rejects invalid values."""
        with pytest.raises(ValueError, match="Default audio format must be one of"):
            FeatureFlags(default_audio_format="invalid")

    def test_stream_timeout_validation_negative(self):
        """Test stream timeout rejects negative values."""
        with pytest.raises(ValueError, match="Stream timeout must be positive"):
            FeatureFlags(stream_timeout_seconds=0)

    def test_stream_token_timeout_validation_negative(self):
        """Test stream token timeout rejects negative values."""
        with pytest.raises(ValueError, match="Stream token timeout must be positive"):
            FeatureFlags(stream_token_timeout_seconds=0)

    def test_stream_keepalive_interval_validation_negative(self):
        """Test stream keepalive interval rejects negative values."""
        with pytest.raises(ValueError, match="Keep-alive interval must be positive"):
            FeatureFlags(stream_keepalive_interval_seconds=0)


@pytest.mark.unit
class TestMetricsConfig:
    """Test MetricsConfig module."""

    def test_default_values(self):
        """Test default metrics configuration values."""
        config = MetricsConfig()
        assert config.enable_metrics is True
        assert config.enable_prometheus is False
        assert config.metrics_retention_hours == 24
        assert config.error_injection_enabled is False
        assert config.error_injection_rate == 0.0
        assert len(config.error_injection_types) == 4


@pytest.mark.unit
class TestAppConfig:
    """Test composed AppConfig."""

    def test_default_values(self):
        """Test default values for all modules."""
        config = AppConfig()
        assert config.server.host == "127.0.0.1"
        assert config.auth.require_api_key is False
        assert config.rate_limits.enabled is False
        assert config.kv_cache.enabled is True
        assert config.generation.response_delay == 0.5
        assert config.storage.file_storage_backend == StorageBackend.MEMORY
        assert config.security.enable_security is False
        assert config.features.enable_prompt_caching is True
        assert config.metrics.enable_metrics is True

    def test_backward_compatibility_server(self):
        """Test backward compatibility for server properties."""
        config = AppConfig()
        assert config.host == config.server.host
        assert config.port == config.server.port
        assert config.debug == config.server.debug

    def test_backward_compatibility_auth(self):
        """Test backward compatibility for auth properties."""
        config = AppConfig()
        assert config.require_api_key == config.auth.require_api_key
        assert config.api_keys == config.auth.api_keys
        assert config.hash_api_keys == config.auth.hash_api_keys

    def test_backward_compatibility_rate_limits(self):
        """Test backward compatibility for rate limit properties."""
        config = AppConfig()
        assert config.rate_limit_enabled == config.rate_limits.enabled
        assert config.rate_limit_tier == config.rate_limits.tier.value
        assert config.rate_limit_rpm == config.rate_limits.rpm_override
        assert config.rate_limit_tpm == config.rate_limits.tpm_override

    def test_backward_compatibility_kv_cache(self):
        """Test backward compatibility for KV cache properties."""
        config = AppConfig()
        assert config.kv_cache_enabled == config.kv_cache.enabled
        assert config.kv_cache_block_size == config.kv_cache.block_size
        assert config.kv_cache_num_workers == config.kv_cache.num_workers
        assert config.kv_overlap_weight == config.kv_cache.overlap_weight

    def test_backward_compatibility_generation(self):
        """Test backward compatibility for generation properties."""
        config = AppConfig()
        assert config.use_llm_generation == config.generation.use_llm_generation
        assert config.llm_model_name == config.generation.llm_model_name
        assert config.response_delay == config.generation.response_delay
        assert config.ttft_ms == config.generation.ttft_ms
        assert config.itl_ms == config.generation.itl_ms

    def test_backward_compatibility_storage(self):
        """Test backward compatibility for storage properties."""
        config = AppConfig()
        assert config.file_storage_backend == config.storage.file_storage_backend.value
        assert config.file_storage_path == config.storage.file_storage_path
        assert config.file_cleanup_enabled == config.storage.file_cleanup_enabled
        assert config.image_retention_hours == config.storage.image_retention_hours

    def test_backward_compatibility_security(self):
        """Test backward compatibility for security properties."""
        config = AppConfig()
        assert config.enable_security == config.security.enable_security
        assert config.enable_input_validation == config.security.enable_input_validation
        assert config.max_request_size == config.security.max_request_size
        assert config.cors_allowed_origins == config.security.cors_allowed_origins

    def test_backward_compatibility_features(self):
        """Test backward compatibility for feature properties."""
        config = AppConfig()
        assert config.enable_prompt_caching == config.features.enable_prompt_caching
        assert config.cache_ttl_seconds == config.features.cache_ttl_seconds
        assert config.enable_moderation == config.features.enable_moderation
        assert config.enable_audio == config.features.enable_audio
        assert config.default_voice == config.features.default_voice

    def test_backward_compatibility_methods(self):
        """Test backward compatibility for security methods."""
        config = AppConfig()
        assert (
            config.is_input_validation_enabled()
            == config.security.is_input_validation_enabled()
        )
        assert (
            config.is_injection_detection_enabled()
            == config.security.is_injection_detection_enabled()
        )
        assert (
            config.is_abuse_detection_enabled()
            == config.security.is_abuse_detection_enabled()
        )

    def test_nested_configuration_via_env(self, monkeypatch):
        """Test nested configuration via environment variables."""
        monkeypatch.setenv("FAKEAI_SERVER__PORT", "9000")
        monkeypatch.setenv("FAKEAI_AUTH__REQUIRE_API_KEY", "true")
        monkeypatch.setenv("FAKEAI_KV_CACHE__BLOCK_SIZE", "32")

        config = AppConfig()
        assert config.server.port == 9000
        assert config.auth.require_api_key is True
        assert config.kv_cache.block_size == 32

    def test_flat_env_vars_for_backward_compatibility(self, monkeypatch):
        """Test flat environment variables work via nested delimiter."""
        # With nested models, we need to use the nested delimiter
        monkeypatch.setenv("FAKEAI_SERVER__HOST", "0.0.0.0")
        monkeypatch.setenv("FAKEAI_SERVER__PORT", "8080")
        monkeypatch.setenv("FAKEAI_SERVER__DEBUG", "true")

        config = AppConfig()
        # Verify both nested and property access work
        assert config.server.host == "0.0.0.0"
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.debug is True

    def test_modular_config_independence(self):
        """Test that modular configs can be instantiated independently."""
        server = ServerConfig(port=9000)
        auth = AuthConfig(require_api_key=True)
        rate_limits = RateLimitConfig(enabled=True, tier=RateLimitTier.TIER_2)

        assert server.port == 9000
        assert auth.require_api_key is True
        assert rate_limits.tier == RateLimitTier.TIER_2

    def test_comprehensive_config_composition(self):
        """Test comprehensive configuration with all modules."""
        config = AppConfig()

        # Verify all module instances are created
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.auth, AuthConfig)
        assert isinstance(config.rate_limits, RateLimitConfig)
        assert isinstance(config.kv_cache, KVCacheConfig)
        assert isinstance(config.generation, GenerationConfig)
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.features, FeatureFlags)
        assert isinstance(config.metrics, MetricsConfig)
