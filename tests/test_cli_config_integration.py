"""
Test CLI and configuration integration.

Tests that CLI arguments properly override environment variables
and that all configuration options work correctly together.
"""


import pytest

from fakeai.config import AppConfig


@pytest.mark.unit
class TestCLIConfigIntegration:
    """Test CLI and configuration integration."""

    def test_cli_args_override_env_for_kv_cache(self, monkeypatch):
        """CLI arguments should override environment variables for KV cache settings."""
        monkeypatch.setenv("FAKEAI_KV_CACHE_ENABLED", "false")
        monkeypatch.setenv("FAKEAI_KV_CACHE_BLOCK_SIZE", "8")
        monkeypatch.setenv("FAKEAI_KV_CACHE_NUM_WORKERS", "2")

        # CLI args should override
        config = AppConfig(
            kv_cache_enabled=True,
            kv_cache_block_size=32,
            kv_cache_num_workers=8,
        )

        assert config.kv_cache_enabled is True  # CLI override
        assert config.kv_cache_block_size == 32  # CLI override
        assert config.kv_cache_num_workers == 8  # CLI override

    def test_cli_args_override_env_for_safety(self, monkeypatch):
        """CLI arguments should override environment variables for safety settings."""
        monkeypatch.setenv("FAKEAI_ENABLE_MODERATION", "false")
        monkeypatch.setenv("FAKEAI_MODERATION_THRESHOLD", "0.3")
        monkeypatch.setenv("FAKEAI_ENABLE_REFUSALS", "false")

        # CLI args should override
        config = AppConfig(
            enable_moderation=True,
            moderation_threshold=0.8,
            enable_refusals=True,
        )

        assert config.enable_moderation is True  # CLI override
        assert config.moderation_threshold == 0.8  # CLI override
        assert config.enable_refusals is True  # CLI override

    def test_cli_args_override_env_for_audio(self, monkeypatch):
        """CLI arguments should override environment variables for audio settings."""
        monkeypatch.setenv("FAKEAI_ENABLE_AUDIO", "false")
        monkeypatch.setenv("FAKEAI_DEFAULT_VOICE", "echo")
        monkeypatch.setenv("FAKEAI_DEFAULT_AUDIO_FORMAT", "opus")

        # CLI args should override
        config = AppConfig(
            enable_audio=True,
            default_voice="nova",
            default_audio_format="mp3",
        )

        assert config.enable_audio is True  # CLI override
        assert config.default_voice == "nova"  # CLI override
        assert config.default_audio_format == "mp3"  # CLI override

    def test_env_vars_used_when_no_cli_args(self, monkeypatch):
        """Environment variables should be used when no CLI arguments provided."""
        monkeypatch.setenv("FAKEAI_KV_CACHE_BLOCK_SIZE", "64")
        monkeypatch.setenv("FAKEAI_DEFAULT_VOICE", "shimmer")
        monkeypatch.setenv("FAKEAI_MODERATION_THRESHOLD", "0.9")
        monkeypatch.setenv("FAKEAI_STRICT_TOKEN_COUNTING", "true")

        config = AppConfig()

        assert config.kv_cache_block_size == 64
        assert config.default_voice == "shimmer"
        assert config.moderation_threshold == 0.9
        assert config.strict_token_counting is True

    def test_partial_cli_override_with_env_vars(self, monkeypatch):
        """Should use CLI args for overridden values and env vars for others."""
        monkeypatch.setenv("FAKEAI_KV_CACHE_BLOCK_SIZE", "64")
        monkeypatch.setenv("FAKEAI_KV_CACHE_NUM_WORKERS", "16")
        monkeypatch.setenv("FAKEAI_DEFAULT_VOICE", "echo")
        monkeypatch.setenv("FAKEAI_MODERATION_THRESHOLD", "0.7")

        # Only override some values
        config = AppConfig(
            kv_cache_block_size=32,  # Override
            default_voice="nova",  # Override
        )

        assert config.kv_cache_block_size == 32  # CLI override
        assert config.kv_cache_num_workers == 16  # From env
        assert config.default_voice == "nova"  # CLI override
        assert config.moderation_threshold == 0.7  # From env


@pytest.mark.unit
class TestCompleteConfigurationScenarios:
    """Test complete configuration scenarios."""

    def test_production_like_configuration(self):
        """Test a production-like configuration with multiple features."""
        config = AppConfig(
            host="0.0.0.0",
            port=8000,
            require_api_key=True,
            api_keys=["sk-prod-key-1", "sk-prod-key-2"],
            rate_limit_enabled=True,
            kv_cache_enabled=True,
            kv_cache_block_size=32,
            kv_cache_num_workers=8,
            enable_moderation=True,
            moderation_threshold=0.8,
            enable_refusals=True,
            enable_jailbreak_detection=True,
            enable_audio=True,
            default_voice="alloy",
            enable_context_validation=True,
            strict_token_counting=False,
        )

        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.require_api_key is True
        assert len(config.api_keys) == 2
        assert config.rate_limit_enabled is True
        assert config.kv_cache_enabled is True
        assert config.kv_cache_block_size == 32
        assert config.enable_moderation is True
        assert config.moderation_threshold == 0.8
        assert config.enable_audio is True

    def test_development_configuration(self):
        """Test a development configuration with safety features disabled."""
        config = AppConfig(
            host="127.0.0.1",
            port=8000,
            debug=True,
            require_api_key=False,
            response_delay=0.0,
            random_delay=False,
            enable_moderation=False,
            enable_refusals=False,
            enable_jailbreak_detection=False,
            strict_token_counting=False,
        )

        assert config.host == "127.0.0.1"
        assert config.debug is True
        assert config.require_api_key is False
        assert config.response_delay == 0.0
        assert config.random_delay is False
        assert config.enable_moderation is False
        assert config.enable_refusals is False
        assert config.strict_token_counting is False

    def test_performance_optimized_configuration(self):
        """Test a performance-optimized configuration."""
        config = AppConfig(
            response_delay=0.0,
            random_delay=False,
            kv_cache_enabled=True,
            kv_cache_block_size=64,
            kv_cache_num_workers=16,
            enable_context_validation=False,
            strict_token_counting=False,
            enable_moderation=False,
        )

        assert config.response_delay == 0.0
        assert config.random_delay is False
        assert config.kv_cache_block_size == 64
        assert config.kv_cache_num_workers == 16
        assert config.enable_context_validation is False
        assert config.strict_token_counting is False

    def test_audio_focused_configuration(self):
        """Test an audio-focused configuration."""
        config = AppConfig(
            enable_audio=True,
            default_voice="nova",
            default_audio_format="opus",
            kv_cache_enabled=True,
            enable_moderation=True,
        )

        assert config.enable_audio is True
        assert config.default_voice == "nova"
        assert config.default_audio_format == "opus"
        assert config.kv_cache_enabled is True
        assert config.enable_moderation is True

    def test_all_boolean_flags_can_be_toggled(self):
        """Test that all boolean configuration flags can be toggled."""
        # Enable all
        config_enabled = AppConfig(
            debug=True,
            random_delay=True,
            require_api_key=True,
            rate_limit_enabled=True,
            enable_prompt_caching=True,
            kv_cache_enabled=True,
            enable_moderation=True,
            enable_refusals=True,
            enable_jailbreak_detection=True,
            enable_audio=True,
            enable_context_validation=True,
            strict_token_counting=True,
        )

        assert config_enabled.debug is True
        assert config_enabled.random_delay is True
        assert config_enabled.require_api_key is True
        assert config_enabled.rate_limit_enabled is True
        assert config_enabled.enable_prompt_caching is True
        assert config_enabled.kv_cache_enabled is True
        assert config_enabled.enable_moderation is True
        assert config_enabled.enable_refusals is True
        assert config_enabled.enable_jailbreak_detection is True
        assert config_enabled.enable_audio is True
        assert config_enabled.enable_context_validation is True
        assert config_enabled.strict_token_counting is True

        # Disable all
        config_disabled = AppConfig(
            debug=False,
            random_delay=False,
            require_api_key=False,
            rate_limit_enabled=False,
            enable_prompt_caching=False,
            kv_cache_enabled=False,
            enable_moderation=False,
            enable_refusals=False,
            enable_jailbreak_detection=False,
            enable_audio=False,
            enable_context_validation=False,
            strict_token_counting=False,
        )

        assert config_disabled.debug is False
        assert config_disabled.random_delay is False
        assert config_disabled.require_api_key is False
        assert config_disabled.rate_limit_enabled is False
        assert config_disabled.enable_prompt_caching is False
        assert config_disabled.kv_cache_enabled is False
        assert config_disabled.enable_moderation is False
        assert config_disabled.enable_refusals is False
        assert config_disabled.enable_jailbreak_detection is False
        assert config_disabled.enable_audio is False
        assert config_disabled.enable_context_validation is False
        assert config_disabled.strict_token_counting is False


@pytest.mark.unit
class TestConfigurationEdgeCases:
    """Test edge cases in configuration."""

    def test_boundary_values_for_numeric_settings(self):
        """Test boundary values for numeric configuration settings."""
        config = AppConfig(
            port=1,  # Minimum
            response_delay=0.0,  # Minimum
            max_variance=0.0,  # Minimum
            kv_cache_block_size=1,  # Minimum
            kv_cache_num_workers=1,  # Minimum
            kv_overlap_weight=0.0,  # Minimum
            moderation_threshold=0.0,  # Minimum
        )

        assert config.port == 1
        assert config.response_delay == 0.0
        assert config.max_variance == 0.0
        assert config.kv_cache_block_size == 1
        assert config.kv_cache_num_workers == 1
        assert config.kv_overlap_weight == 0.0
        assert config.moderation_threshold == 0.0

        config_max = AppConfig(
            port=65535,  # Maximum
            kv_cache_block_size=128,  # Maximum
            kv_cache_num_workers=64,  # Maximum
            kv_overlap_weight=2.0,  # Maximum
            moderation_threshold=1.0,  # Maximum
        )

        assert config_max.port == 65535
        assert config_max.kv_cache_block_size == 128
        assert config_max.kv_cache_num_workers == 64
        assert config_max.kv_overlap_weight == 2.0
        assert config_max.moderation_threshold == 1.0

    def test_all_valid_audio_voices(self):
        """Test all valid audio voice options."""
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

    def test_all_valid_audio_formats(self):
        """Test all valid audio format options."""
        valid_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm16"]

        for fmt in valid_formats:
            config = AppConfig(default_audio_format=fmt)
            assert config.default_audio_format == fmt

    def test_empty_api_keys_list(self):
        """Test that empty API keys list works correctly."""
        config = AppConfig(api_keys=[])
        assert config.api_keys == []
        assert config.require_api_key is False

    def test_multiple_api_keys(self):
        """Test that multiple API keys can be configured."""
        keys = [f"sk-key-{i}" for i in range(10)]
        config = AppConfig(api_keys=keys)
        assert len(config.api_keys) == 10
        assert config.api_keys == keys
