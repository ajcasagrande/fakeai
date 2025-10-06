"""
Configuration behavior tests.

Tests configuration loading from environment variables and defaults.
"""

import os

import pytest

from fakeai.config import AppConfig


@pytest.mark.unit
class TestConfigurationDefaults:
    """Test configuration default values."""

    def test_default_host_is_localhost(self):
        """Default host should be 127.0.0.1 (localhost)."""
        config = AppConfig()

        assert config.host == "127.0.0.1"

    def test_default_port_is_8000(self):
        """Default port should be 8000."""
        config = AppConfig()

        assert config.port == 8000

    def test_default_auth_disabled(self):
        """Default should have authentication disabled."""
        config = AppConfig()

        assert config.require_api_key is False

    def test_default_api_keys_empty(self):
        """Default should have no API keys configured."""
        config = AppConfig()

        assert config.api_keys == []

    def test_default_response_delay_matches_docs(self):
        """Default response delay should be 0.5s as documented."""
        config = AppConfig()

        assert config.response_delay == 0.5

    def test_default_random_delay_enabled(self):
        """Default should have random delay enabled."""
        config = AppConfig()

        assert config.random_delay is True


@pytest.mark.unit
class TestConfigurationEnvironmentVariables:
    """Test configuration from environment variables."""

    def test_loads_host_from_env(self, monkeypatch):
        """Should load host from FAKEAI_HOST environment variable."""
        monkeypatch.setenv("FAKEAI_HOST", "0.0.0.0")

        config = AppConfig()

        assert config.host == "0.0.0.0"

    def test_loads_port_from_env(self, monkeypatch):
        """Should load port from FAKEAI_PORT environment variable."""
        monkeypatch.setenv("FAKEAI_PORT", "9000")

        config = AppConfig()

        assert config.port == 9000

    def test_loads_debug_from_env(self, monkeypatch):
        """Should load debug flag from FAKEAI_DEBUG."""
        monkeypatch.setenv("FAKEAI_DEBUG", "true")

        config = AppConfig()

        assert config.debug is True

    def test_loads_response_delay_from_env(self, monkeypatch):
        """Should load response delay from FAKEAI_RESPONSE_DELAY."""
        monkeypatch.setenv("FAKEAI_RESPONSE_DELAY", "1.5")

        config = AppConfig()

        assert config.response_delay == 1.5

    def test_loads_api_keys_from_env(self, monkeypatch):
        """Should load API keys from FAKEAI_API_KEYS (JSON array format)."""
        import json

        # Pydantic-settings expects JSON format for list types
        monkeypatch.setenv("FAKEAI_API_KEYS", json.dumps(["key1", "key2", "key3"]))

        config = AppConfig()

        assert config.api_keys == ["key1", "key2", "key3"]

    def test_loads_require_api_key_from_env(self, monkeypatch):
        """Should load require_api_key from FAKEAI_REQUIRE_API_KEY."""
        monkeypatch.setenv("FAKEAI_REQUIRE_API_KEY", "true")

        config = AppConfig()

        assert config.require_api_key is True


@pytest.mark.unit
class TestConfigurationValidation:
    """Test configuration validation behavior."""

    def test_rejects_invalid_port_too_high(self):
        """Should reject port numbers above 65535."""
        with pytest.raises(ValueError, match="Port must be between"):
            AppConfig(port=99999)

    def test_rejects_invalid_port_too_low(self):
        """Should reject port numbers below 1."""
        with pytest.raises(ValueError, match="Port must be between"):
            AppConfig(port=0)

    def test_rejects_negative_response_delay(self):
        """Should reject negative response delay."""
        with pytest.raises(ValueError, match="Response delay cannot be negative"):
            AppConfig(response_delay=-1.0)

    def test_rejects_negative_max_variance(self):
        """Should reject negative max variance."""
        with pytest.raises(ValueError, match="Max variance cannot be negative"):
            AppConfig(max_variance=-0.5)

    def test_accepts_valid_port_range(self):
        """Should accept valid port numbers."""
        config_low = AppConfig(port=1)
        config_high = AppConfig(port=65535)
        config_mid = AppConfig(port=8080)

        assert config_low.port == 1
        assert config_high.port == 65535
        assert config_mid.port == 8080


@pytest.mark.unit
class TestConfigurationOverrides:
    """Test configuration override behavior."""

    def test_explicit_args_override_defaults(self):
        """Explicitly provided arguments should override defaults."""
        config = AppConfig(
            host="192.168.1.1",
            port=9000,
            debug=True,
            response_delay=2.0,
        )

        assert config.host == "192.168.1.1"
        assert config.port == 9000
        assert config.debug is True
        assert config.response_delay == 2.0

    def test_explicit_args_override_env_vars(self, monkeypatch):
        """Explicitly provided arguments should override environment variables."""
        monkeypatch.setenv("FAKEAI_PORT", "7000")

        # Explicit arg should win
        config = AppConfig(port=9000)

        assert config.port == 9000  # Not 7000 from env


@pytest.mark.unit
class TestKVCacheConfiguration:
    """Test KV cache configuration options."""

    def test_default_kv_cache_enabled(self):
        """KV cache should be enabled by default."""
        config = AppConfig()
        assert config.kv_cache_enabled is True

    def test_default_kv_cache_block_size(self):
        """Default KV cache block size should be 16."""
        config = AppConfig()
        assert config.kv_cache_block_size == 16

    def test_default_kv_cache_num_workers(self):
        """Default number of workers should be 4."""
        config = AppConfig()
        assert config.kv_cache_num_workers == 4

    def test_default_kv_overlap_weight(self):
        """Default overlap weight should be 1.0."""
        config = AppConfig()
        assert config.kv_overlap_weight == 1.0

    def test_kv_cache_block_size_validation_minimum(self):
        """Should reject KV cache block size less than 1."""
        with pytest.raises(ValueError, match="KV cache block size must be at least 1"):
            AppConfig(kv_cache_block_size=0)

    def test_kv_cache_block_size_validation_maximum(self):
        """Should reject KV cache block size greater than 128."""
        with pytest.raises(ValueError, match="KV cache block size cannot exceed 128"):
            AppConfig(kv_cache_block_size=129)

    def test_kv_cache_num_workers_validation_minimum(self):
        """Should reject number of workers less than 1."""
        with pytest.raises(
            ValueError, match="KV cache number of workers must be at least 1"
        ):
            AppConfig(kv_cache_num_workers=0)

    def test_kv_cache_num_workers_validation_maximum(self):
        """Should reject number of workers greater than 64."""
        with pytest.raises(
            ValueError, match="KV cache number of workers cannot exceed 64"
        ):
            AppConfig(kv_cache_num_workers=65)

    def test_kv_overlap_weight_validation_minimum(self):
        """Should reject overlap weight less than 0.0."""
        with pytest.raises(
            ValueError, match="KV overlap weight must be between 0.0 and 2.0"
        ):
            AppConfig(kv_overlap_weight=-0.1)

    def test_kv_overlap_weight_validation_maximum(self):
        """Should reject overlap weight greater than 2.0."""
        with pytest.raises(
            ValueError, match="KV overlap weight must be between 0.0 and 2.0"
        ):
            AppConfig(kv_overlap_weight=2.1)

    def test_loads_kv_cache_settings_from_env(self, monkeypatch):
        """Should load KV cache settings from environment variables."""
        monkeypatch.setenv("FAKEAI_KV_CACHE_ENABLED", "false")
        monkeypatch.setenv("FAKEAI_KV_CACHE_BLOCK_SIZE", "32")
        monkeypatch.setenv("FAKEAI_KV_CACHE_NUM_WORKERS", "8")
        monkeypatch.setenv("FAKEAI_KV_OVERLAP_WEIGHT", "1.5")

        config = AppConfig()

        assert config.kv_cache_enabled is False
        assert config.kv_cache_block_size == 32
        assert config.kv_cache_num_workers == 8
        assert config.kv_overlap_weight == 1.5


@pytest.mark.unit
class TestSafetyConfiguration:
    """Test safety-related configuration options."""

    def test_default_enable_moderation(self):
        """Content moderation should be disabled by default (for testing)."""
        config = AppConfig()
        assert config.enable_moderation is False

    def test_default_moderation_threshold(self):
        """Default moderation threshold should be 0.5."""
        config = AppConfig()
        assert config.moderation_threshold == 0.5

    def test_default_enable_refusals(self):
        """Refusals should be disabled by default (for testing)."""
        config = AppConfig()
        assert config.enable_refusals is False

    def test_default_enable_jailbreak_detection(self):
        """Jailbreak detection should be disabled by default (for testing)."""
        config = AppConfig()
        assert config.enable_jailbreak_detection is False

    def test_moderation_threshold_validation_minimum(self):
        """Should reject moderation threshold less than 0.0."""
        with pytest.raises(
            ValueError, match="Moderation threshold must be between 0.0 and 1.0"
        ):
            AppConfig(moderation_threshold=-0.1)

    def test_moderation_threshold_validation_maximum(self):
        """Should reject moderation threshold greater than 1.0."""
        with pytest.raises(
            ValueError, match="Moderation threshold must be between 0.0 and 1.0"
        ):
            AppConfig(moderation_threshold=1.1)

    def test_moderation_threshold_boundary_values(self):
        """Should accept boundary values for moderation threshold."""
        config_min = AppConfig(moderation_threshold=0.0)
        config_max = AppConfig(moderation_threshold=1.0)

        assert config_min.moderation_threshold == 0.0
        assert config_max.moderation_threshold == 1.0

    def test_loads_safety_settings_from_env(self, monkeypatch):
        """Should load safety settings from environment variables."""
        monkeypatch.setenv("FAKEAI_ENABLE_MODERATION", "false")
        monkeypatch.setenv("FAKEAI_MODERATION_THRESHOLD", "0.7")
        monkeypatch.setenv("FAKEAI_ENABLE_REFUSALS", "false")
        monkeypatch.setenv("FAKEAI_ENABLE_JAILBREAK_DETECTION", "false")

        config = AppConfig()

        assert config.enable_moderation is False
        assert config.moderation_threshold == 0.7
        assert config.enable_refusals is False
        assert config.enable_jailbreak_detection is False


@pytest.mark.unit
class TestAudioConfiguration:
    """Test audio-related configuration options."""

    def test_default_enable_audio(self):
        """Audio should be enabled by default."""
        config = AppConfig()
        assert config.enable_audio is True

    def test_default_voice(self):
        """Default voice should be 'alloy'."""
        config = AppConfig()
        assert config.default_voice == "alloy"

    def test_default_audio_format(self):
        """Default audio format should be 'mp3'."""
        config = AppConfig()
        assert config.default_audio_format == "mp3"

    def test_default_voice_validation_valid_voices(self):
        """Should accept all valid voice options."""
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
            config = AppConfig(default_voice=voice)
            assert config.default_voice == voice

    def test_default_voice_validation_invalid_voice(self):
        """Should reject invalid voice options."""
        with pytest.raises(ValueError, match="Default voice must be one of"):
            AppConfig(default_voice="invalid_voice")

    def test_default_audio_format_validation_valid_formats(self):
        """Should accept all valid audio formats."""
        valid_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm16"]

        for fmt in valid_formats:
            config = AppConfig(default_audio_format=fmt)
            assert config.default_audio_format == fmt

    def test_default_audio_format_validation_invalid_format(self):
        """Should reject invalid audio formats."""
        with pytest.raises(ValueError, match="Default audio format must be one of"):
            AppConfig(default_audio_format="invalid_format")

    def test_loads_audio_settings_from_env(self, monkeypatch):
        """Should load audio settings from environment variables."""
        monkeypatch.setenv("FAKEAI_ENABLE_AUDIO", "false")
        monkeypatch.setenv("FAKEAI_DEFAULT_VOICE", "echo")
        monkeypatch.setenv("FAKEAI_DEFAULT_AUDIO_FORMAT", "opus")

        config = AppConfig()

        assert config.enable_audio is False
        assert config.default_voice == "echo"
        assert config.default_audio_format == "opus"


@pytest.mark.unit
class TestPerformanceConfiguration:
    """Test performance-related configuration options."""

    def test_default_enable_context_validation(self):
        """Context validation should be enabled by default."""
        config = AppConfig()
        assert config.enable_context_validation is True

    def test_default_strict_token_counting(self):
        """Strict token counting should be disabled by default."""
        config = AppConfig()
        assert config.strict_token_counting is False

    def test_loads_performance_settings_from_env(self, monkeypatch):
        """Should load performance settings from environment variables."""
        monkeypatch.setenv("FAKEAI_ENABLE_CONTEXT_VALIDATION", "false")
        monkeypatch.setenv("FAKEAI_STRICT_TOKEN_COUNTING", "true")

        config = AppConfig()

        assert config.enable_context_validation is False
        assert config.strict_token_counting is True


@pytest.mark.unit
class TestConfigurationComprehensive:
    """Comprehensive configuration tests with multiple options."""

    def test_all_new_features_can_be_disabled(self):
        """Should be able to disable all new features together."""
        config = AppConfig(
            kv_cache_enabled=False,
            enable_moderation=False,
            enable_refusals=False,
            enable_jailbreak_detection=False,
            enable_audio=False,
            enable_context_validation=False,
        )

        assert config.kv_cache_enabled is False
        assert config.enable_moderation is False
        assert config.enable_refusals is False
        assert config.enable_jailbreak_detection is False
        assert config.enable_audio is False
        assert config.enable_context_validation is False

    def test_all_new_features_with_custom_values(self):
        """Should accept custom values for all new features."""
        config = AppConfig(
            kv_cache_block_size=32,
            kv_cache_num_workers=8,
            kv_overlap_weight=1.5,
            moderation_threshold=0.75,
            default_voice="nova",
            default_audio_format="opus",
            strict_token_counting=True,
        )

        assert config.kv_cache_block_size == 32
        assert config.kv_cache_num_workers == 8
        assert config.kv_overlap_weight == 1.5
        assert config.moderation_threshold == 0.75
        assert config.default_voice == "nova"
        assert config.default_audio_format == "opus"
        assert config.strict_token_counting is True

    def test_mixed_env_and_explicit_overrides(self, monkeypatch):
        """Explicit arguments should override environment variables."""
        monkeypatch.setenv("FAKEAI_KV_CACHE_BLOCK_SIZE", "8")
        monkeypatch.setenv("FAKEAI_DEFAULT_VOICE", "echo")
        monkeypatch.setenv("FAKEAI_MODERATION_THRESHOLD", "0.3")

        config = AppConfig(
            kv_cache_block_size=64,
            default_voice="nova",
        )

        assert config.kv_cache_block_size == 64  # Explicit override
        assert config.default_voice == "nova"  # Explicit override
        assert config.moderation_threshold == 0.3  # From env
