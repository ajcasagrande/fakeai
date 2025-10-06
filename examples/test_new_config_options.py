#!/usr/bin/env python3
"""
Example demonstrating new configuration options.

This example shows how to use:
- KV cache settings
- Safety settings (moderation, refusals, jailbreak detection)
- Audio settings (voice, format)
- Performance settings (context validation, strict token counting)
"""

import os

from fakeai.config import AppConfig


def example_production_config():
    """Production configuration with all safety features enabled."""
    print("\n=== Production Configuration ===")

    config = AppConfig(
        host="0.0.0.0",
        port=8000,
        require_api_key=True,
        # KV Cache settings for better performance
        kv_cache_enabled=True,
        kv_cache_block_size=32,
        kv_cache_num_workers=8,
        kv_overlap_weight=1.2,
        # Safety settings enabled
        enable_moderation=True,
        moderation_threshold=0.8,
        enable_refusals=True,
        enable_jailbreak_detection=True,
        # Audio enabled with default settings
        enable_audio=True,
        default_voice="alloy",
        default_audio_format="mp3",
        # Performance monitoring enabled
        enable_context_validation=True,
        strict_token_counting=False,  # Use fast token counting
    )

    print(f"Host: {config.host}:{config.port}")
    print(
        f"KV Cache: enabled={config.kv_cache_enabled}, "
        f"block_size={config.kv_cache_block_size}, "
        f"workers={config.kv_cache_num_workers}"
    )
    print(
        f"Safety: moderation={config.enable_moderation}, "
        f"threshold={config.moderation_threshold}, "
        f"refusals={config.enable_refusals}"
    )
    print(
        f"Audio: enabled={config.enable_audio}, "
        f"voice={config.default_voice}, "
        f"format={config.default_audio_format}"
    )

    return config


def example_development_config():
    """Development configuration with minimal delays and safety checks disabled."""
    print("\n=== Development Configuration ===")

    config = AppConfig(
        host="127.0.0.1",
        port=8000,
        debug=True,
        require_api_key=False,
        # Minimal delays for fast testing
        response_delay=0.0,
        random_delay=False,
        # KV Cache enabled but with smaller settings
        kv_cache_enabled=True,
        kv_cache_block_size=16,
        kv_cache_num_workers=4,
        # Safety checks disabled for faster testing
        enable_moderation=False,
        enable_refusals=False,
        enable_jailbreak_detection=False,
        # Audio enabled for testing
        enable_audio=True,
        default_voice="nova",
        # Fast performance settings
        enable_context_validation=False,
        strict_token_counting=False,
    )

    print(f"Host: {config.host}:{config.port}")
    print(f"Debug: {config.debug}")
    print(f"Response delay: {config.response_delay}s")
    print(f"Safety checks: all disabled for development")
    print(f"KV Cache: basic settings for development")

    return config


def example_performance_config():
    """Performance-optimized configuration for load testing."""
    print("\n=== Performance-Optimized Configuration ===")

    config = AppConfig(
        # No delays
        response_delay=0.0,
        random_delay=False,
        # Maximum KV cache performance
        kv_cache_enabled=True,
        kv_cache_block_size=64,
        kv_cache_num_workers=16,
        kv_overlap_weight=1.5,
        # Minimal safety overhead
        enable_moderation=False,
        enable_refusals=False,
        enable_jailbreak_detection=False,
        # Audio enabled
        enable_audio=True,
        # Performance settings optimized
        enable_context_validation=False,  # Skip validation
        strict_token_counting=False,  # Use fast counting
    )

    print(f"Response delay: {config.response_delay}s (instant)")
    print(
        f"KV Cache: block_size={config.kv_cache_block_size}, "
        f"workers={config.kv_cache_num_workers}"
    )
    print(f"Safety checks: disabled for maximum performance")
    print(f"Context validation: {config.enable_context_validation}")

    return config


def example_audio_focused_config():
    """Audio-focused configuration with high-quality settings."""
    print("\n=== Audio-Focused Configuration ===")

    config = AppConfig(
        # Audio settings
        enable_audio=True,
        default_voice="nova",  # High-quality voice
        default_audio_format="opus",  # High-quality format
        # KV cache for better audio generation
        kv_cache_enabled=True,
        kv_cache_block_size=32,
        # Safety enabled
        enable_moderation=True,
        moderation_threshold=0.5,
        enable_refusals=True,
    )

    print(f"Audio enabled: {config.enable_audio}")
    print(f"Default voice: {config.default_voice}")
    print(f"Audio format: {config.default_audio_format}")
    print(f"KV Cache: enabled for better performance")

    return config


def example_env_vars_config():
    """Configuration from environment variables."""
    print("\n=== Environment Variables Configuration ===")

    # Set environment variables
    os.environ["FAKEAI_KV_CACHE_BLOCK_SIZE"] = "64"
    os.environ["FAKEAI_DEFAULT_VOICE"] = "shimmer"
    os.environ["FAKEAI_MODERATION_THRESHOLD"] = "0.9"
    os.environ["FAKEAI_ENABLE_AUDIO"] = "true"

    # Config will automatically load from environment
    config = AppConfig()

    print("Environment variables set:")
    print(f"  FAKEAI_KV_CACHE_BLOCK_SIZE=64")
    print(f"  FAKEAI_DEFAULT_VOICE=shimmer")
    print(f"  FAKEAI_MODERATION_THRESHOLD=0.9")
    print(f"  FAKEAI_ENABLE_AUDIO=true")
    print()
    print("Loaded configuration:")
    print(f"  KV cache block size: {config.kv_cache_block_size}")
    print(f"  Default voice: {config.default_voice}")
    print(f"  Moderation threshold: {config.moderation_threshold}")
    print(f"  Audio enabled: {config.enable_audio}")

    # Clean up
    del os.environ["FAKEAI_KV_CACHE_BLOCK_SIZE"]
    del os.environ["FAKEAI_DEFAULT_VOICE"]
    del os.environ["FAKEAI_MODERATION_THRESHOLD"]
    del os.environ["FAKEAI_ENABLE_AUDIO"]

    return config


def example_cli_override():
    """Configuration with CLI argument override."""
    print("\n=== CLI Override Configuration ===")

    # Set environment variable
    os.environ["FAKEAI_KV_CACHE_BLOCK_SIZE"] = "16"

    # CLI argument overrides environment variable
    config = AppConfig(kv_cache_block_size=64)

    print("Environment: FAKEAI_KV_CACHE_BLOCK_SIZE=16")
    print("CLI argument: --kv-cache-block-size 64")
    print(f"Final value: {config.kv_cache_block_size} (CLI wins)")

    # Clean up
    del os.environ["FAKEAI_KV_CACHE_BLOCK_SIZE"]

    return config


def main():
    """Run all configuration examples."""
    print("=" * 70)
    print("FakeAI Configuration Examples")
    print("=" * 70)

    # Production config
    example_production_config()

    # Development config
    example_development_config()

    # Performance config
    example_performance_config()

    # Audio-focused config
    example_audio_focused_config()

    # Environment variables
    example_env_vars_config()

    # CLI override
    example_cli_override()

    print("\n" + "=" * 70)
    print("All configuration examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
