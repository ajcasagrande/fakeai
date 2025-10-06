"""
Anthropic Model Catalog

Complete catalog of Anthropic Claude models with accurate pricing and capabilities.
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import CAPABILITY_PRESETS, LatencyProfile, ModelCapabilities
from ..definition import ModelDefinition, create_model_definition


def _get_anthropic_models() -> list[ModelDefinition]:
    """
    Get all Anthropic Claude model definitions.

    Returns:
        List of Anthropic ModelDefinition instances
    """
    models = []

    # Claude 3.5 Sonnet (Latest flagship)
    claude_35_sonnet_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=8192,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,  # Not disclosed
        provider="anthropic",
        model_family="claude-3.5",
        tags=["chat", "vision", "latest", "flagship"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.4,
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
            display_name="Claude 3.5 Sonnet",
            description="Latest Claude model with vision, improved reasoning, and extended context.",
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

    # Claude 3 Opus (Most capable)
    claude_3_opus_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-3",
        tags=["chat", "vision", "powerful"],
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
            display_name="Claude 3 Opus",
            description="Most capable Claude 3 model for complex tasks requiring deep reasoning.",
            version="20240229",
            custom_fields={
                "pricing": {
                    "input_per_million": 15.0,
                    "output_per_million": 75.0,
                },
            },
        )
    )

    # Claude 3 Sonnet (Balanced)
    claude_3_sonnet_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-3",
        tags=["chat", "vision", "balanced"],
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
            display_name="Claude 3 Sonnet",
            description="Balanced Claude 3 model with excellent performance and value.",
            version="20240229",
            custom_fields={
                "pricing": {
                    "input_per_million": 3.0,
                    "output_per_million": 15.0,
                },
            },
        )
    )

    # Claude 3 Haiku (Fast and efficient)
    claude_3_haiku_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=200000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-3",
        tags=["chat", "vision", "efficient", "fast"],
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
            display_name="Claude 3 Haiku",
            description="Fast and efficient Claude 3 model for high-throughput tasks.",
            version="20240307",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.25,
                    "output_per_million": 1.25,
                },
            },
        )
    )

    # Claude 2.1 (Legacy)
    claude_21_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=200000,
        max_output_tokens=4096,
        supports_vision=False,
        parameter_count=None,
        provider="anthropic",
        model_family="claude-2",
        tags=["chat", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.5,
            tokens_per_second=40.0,
            min_delay=0.022,
            max_delay=0.03,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="claude-2.1",
            created=1699920000,  # 2023-11-14
            owned_by="anthropic",
            capabilities=claude_21_caps,
            display_name="Claude 2.1",
            description="Legacy Claude model with 200K context window. Consider upgrading to Claude 3.",
            version="2.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 8.0,
                    "output_per_million": 24.0,
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
