"""
Anthropic Model Catalog

Complete catalog of Anthropic Claude models with accurate pricing and capabilities.

Updated: October 2025
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import CAPABILITY_PRESETS, LatencyProfile
from ..definition import ModelDefinition


def _get_anthropic_models() -> list[ModelDefinition]:
    """
    Get all Anthropic Claude model definitions.

    Returns:
        List of Anthropic ModelDefinition instances
    """
    models = []

    # Claude 4.5 Sonnet (Latest flagship - September 2025)
    claude_45_sonnet_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=64000,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,  # Not disclosed
        provider="anthropic",
        model_family="claude-4.5",
        tags=["chat", "vision", "latest", "flagship", "coding"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.38,
            tokens_per_second=52.0,
            min_delay=0.017,
            max_delay=0.024,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-sonnet-4-5",
            created=1727654400,  # 2025-09-29
            owned_by="anthropic",
            capabilities=claude_45_sonnet_caps,
            display_name="Claude Sonnet 4.5",
            description="Latest Claude model with exceptional coding abilities, 200K context (1M available), and up to 64K output. SWE-bench: 77.2% standard, 82.0% parallel.",
            version="20250929",
            custom_fields={
                "pricing": {
                    "input_per_million": 3.0,
                    "output_per_million": 15.0,
                    "cached_input_per_million": 0.30,
                    "long_context_input_per_million": 6.0,  # > 200K tokens
                    "long_context_output_per_million": 22.50,
                },
                "swe_bench_verified": 77.2,
                "swe_bench_parallel": 82.0,
            },
        )
    )

    # Claude 4 Sonnet (February 2025)
    claude_4_sonnet_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=8192,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-4",
        tags=["chat", "vision", "balanced"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.40,
            tokens_per_second=50.0,
            min_delay=0.018,
            max_delay=0.025,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-sonnet-4",
            created=1738368000,  # 2025-02-01 (approximate)
            owned_by="anthropic",
            capabilities=claude_4_sonnet_caps,
            display_name="Claude Sonnet 4",
            description="Claude 4 Sonnet with vision, improved reasoning, and extended context.",
            version="20250201",
            custom_fields={
                "pricing": {
                    "input_per_million": 3.0,
                    "output_per_million": 15.0,
                    "cached_input_per_million": 0.30,
                },
            },
        )
    )

    # Claude 4 Opus (Most powerful - 2025)
    claude_4_opus_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=8192,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-4",
        tags=["chat", "vision", "powerful", "premium"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.82,
            tokens_per_second=27.0,
            min_delay=0.033,
            max_delay=0.043,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-opus-4",
            created=1738368000,
            owned_by="anthropic",
            capabilities=claude_4_opus_caps,
            display_name="Claude Opus 4",
            description="Most powerful Claude 4 model for highly complex tasks requiring deep reasoning and analysis.",
            version="20250201",
            custom_fields={
                "pricing": {
                    "input_per_million": 15.0,
                    "output_per_million": 75.0,
                },
            },
        ))

    # Claude 4 Haiku (Fast and efficient - 2025)
    claude_4_haiku_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=8192,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-4",
        tags=["chat", "vision", "efficient", "fast"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.20,
            tokens_per_second=88.0,
            min_delay=0.009,
            max_delay=0.014,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-haiku-4",
            created=1738368000,
            owned_by="anthropic",
            capabilities=claude_4_haiku_caps,
            display_name="Claude Haiku 4",
            description="Fast and efficient Claude 4 model for high-throughput tasks with vision support.",
            version="20250201",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.80,
                    "output_per_million": 4.0,
                },
            },
        ))

    # Claude 3.5 Sonnet (2024 - Legacy)
    claude_35_sonnet_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=8192,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-3.5",
        tags=["chat", "vision", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.40,
            tokens_per_second=50.0,
            min_delay=0.018,
            max_delay=0.025,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-3-5-sonnet-20241022",
            created=1729555200,  # 2024-10-22
            owned_by="anthropic",
            capabilities=claude_35_sonnet_caps,
            display_name="Claude 3.5 Sonnet (Legacy)",
            description="Legacy Claude 3.5 model. Consider upgrading to Claude 4.5 Sonnet for better performance.",
            version="20241022",
            custom_fields={
                "pricing": {
                    "input_per_million": 3.0,
                    "output_per_million": 15.0,
                    "cached_input_per_million": 0.30,
                },
            },
        )
    )

    # Claude 3 Opus (Legacy)
    claude_3_opus_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-3",
        tags=["chat", "vision", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.85,
            tokens_per_second=26.0,
            min_delay=0.035,
            max_delay=0.045,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-3-opus-20240229",
            created=1709251200,  # 2024-03-01
            owned_by="anthropic",
            capabilities=claude_3_opus_caps,
            display_name="Claude 3 Opus (Legacy)",
            description="Legacy Claude 3 model. Consider upgrading to Claude 4 Opus.",
            version="20240229",
            custom_fields={
                "pricing": {
                    "input_per_million": 15.0,
                    "output_per_million": 75.0,
                },
            },
        )
    )

    # Claude 3 Sonnet (Legacy)
    claude_3_sonnet_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-3",
        tags=["chat", "vision", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.45,
            tokens_per_second=45.0,
            min_delay=0.02,
            max_delay=0.028,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-3-sonnet-20240229",
            created=1709251200,
            owned_by="anthropic",
            capabilities=claude_3_sonnet_caps,
            display_name="Claude 3 Sonnet (Legacy)",
            description="Legacy Claude 3 model. Consider upgrading to Claude 4 Sonnet.",
            version="20240229",
            custom_fields={
                "pricing": {
                    "input_per_million": 3.0,
                    "output_per_million": 15.0,
                },
            },
        ))

    # Claude 3 Haiku (Legacy)
    claude_3_haiku_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-3",
        tags=["chat", "vision", "legacy", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.22,
            tokens_per_second=83.0,
            min_delay=0.01,
            max_delay=0.015,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-3-haiku-20240307",
            created=1709769600,  # 2024-03-07
            owned_by="anthropic",
            capabilities=claude_3_haiku_caps,
            display_name="Claude 3 Haiku (Legacy)",
            description="Legacy Claude 3 model. Consider upgrading to Claude 4 Haiku.",
            version="20240307",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.25,
                    "output_per_million": 1.25,
                },
            },
        )
    )

    return models


# Export the models list
ANTHROPIC_MODELS = _get_anthropic_models()


def get_anthropic_models() -> list[ModelDefinition]:
    """
    Get all Anthropic Claude models.

    Returns:
        List of Anthropic ModelDefinition instances
    """
    return ANTHROPIC_MODELS.copy()
