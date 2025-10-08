"""
Mistral AI Model Catalog

Complete catalog of Mistral AI models including Mistral Large 2.1, Mixtral (MoE),
and Mistral models with accurate pricing and capabilities.

Updated: October 2025
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import (
    CAPABILITY_PRESETS,
    LatencyProfile,
    MoEConfig,
)
from ..definition import ModelDefinition


def _get_mistral_models() -> list[ModelDefinition]:
    """
    Get all Mistral AI model definitions.

    Returns:
        List of Mistral ModelDefinition instances
    """
    models = []

    # Mistral Large 2.1 (123B - Latest November 2024/2025)
    mistral_large_21_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_parallel_tool_calls=True,
        parameter_count=123_000_000_000,
        provider="mistral",
        model_family="mistral-large",
        tags=["chat", "large", "flagship", "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.48,
            tokens_per_second=46.0,
            min_delay=0.019,
            max_delay=0.027,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="mistral-large-2411",
            created=1732147200,  # 2024-11-21
            owned_by="mistral",
            capabilities=mistral_large_21_caps,
            display_name="Mistral Large 2.1",
            description="Latest 123B parameter flagship with 128K context. Supports 12+ languages and 80 coding languages.",
            version="2.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.0,
                    "output_per_million": 6.0,
                },
                "license": "Commercial",
            },
        )
    )

    # Alias for Mistral Large latest
    models.append(
        ModelDefinition(
            model_id="mistral-large-latest",
            created=1732147200,
            owned_by="mistral",
            capabilities=mistral_large_21_caps,
            display_name="Mistral Large (Latest)",
            description="Alias for Mistral Large 2.1. Always points to the latest version.",
            version="latest",
            parent="mistral-large-2411",
            root="mistral-large-2411",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.0,
                    "output_per_million": 6.0,
                },
                "license": "Commercial",
            },
        ))

    # Mixtral 8x22B (Large MoE flagship)
    mixtral_8x22b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=65536,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=141_000_000_000,  # 8 experts × 22B each
            active_params=39_000_000_000,  # 2 experts active per token
            num_experts=8,
            experts_per_token=2,
        ),
        parameter_count=141_000_000_000,
        provider="mistral",
        model_family="mixtral",
        tags=["chat", "moe", "large"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.55,
            tokens_per_second=40.0,
            min_delay=0.023,
            max_delay=0.032,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="mistralai/Mixtral-8x22B-Instruct-v0.1",
            created=1712793600,  # 2024-04-11
            owned_by="mistral",
            capabilities=mixtral_8x22b_caps,
            display_name="Mixtral 8x22B Instruct",
            description="Large MoE model with 8 experts of 22B parameters each (141B total, 39B active).",
            version="0.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.0,
                    "output_per_million": 6.0,
                },
                "license": "Apache 2.0",
            },
        )
    )

    # Mixtral 8x7B (Original MoE model)
    mixtral_8x7b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=32768,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=46_700_000_000,
            # 8 experts × 7B each (with shared layers)
            active_params=12_900_000_000,  # 2 experts active per token
            num_experts=8,
            experts_per_token=2,
        ),
        parameter_count=46_700_000_000,
        provider="mistral",
        model_family="mixtral",
        tags=["chat", "moe", "balanced"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.38,
            tokens_per_second=55.0,
            min_delay=0.016,
            max_delay=0.022,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
            created=1702339200,  # 2023-12-12
            owned_by="mistral",
            capabilities=mixtral_8x7b_caps,
            display_name="Mixtral 8x7B Instruct",
            description="Balanced MoE model with 8 experts of 7B parameters each (47B total, 13B active).",
            version="0.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.70,
                    "output_per_million": 0.70,
                },
                "license": "Apache 2.0",
            },
        )
    )

    # Mistral Medium 3 (May 2025)
    mistral_medium3_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        parameter_count=None,
        provider="mistral",
        model_family="mistral-medium",
        tags=["chat", "balanced"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.33,
            tokens_per_second=58.0,
            min_delay=0.015,
            max_delay=0.021,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="mistral-medium-3",
            created=1746057600,  # 2025-05-01 (approximate)
            owned_by="mistral",
            capabilities=mistral_medium3_caps,
            display_name="Mistral Medium 3",
            description="Balanced model with improved performance/cost ratio and 128K context.",
            version="3",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.7,
                    "output_per_million": 8.1,
                },
                "license": "Commercial",
            },
        )
    )

    # Mistral Small (Commercial)
    mistral_small_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=32768,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        parameter_count=None,
        provider="mistral",
        model_family="mistral-small",
        tags=["chat", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.2,
            tokens_per_second=80.0,
            min_delay=0.011,
            max_delay=0.015,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="mistral-small-latest",
            created=1717200000,  # 2024-06-01
            owned_by="mistral",
            capabilities=mistral_small_caps,
            display_name="Mistral Small",
            description="Efficient model optimized for cost and latency.",
            version="latest",
            custom_fields={
                "pricing": {
                    "input_per_million": 1.0,
                    "output_per_million": 3.0,
                },
                "license": "Commercial",
            },
        )
    )

    # Ministral 3B (Ultra-efficient)
    ministral_3b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=3_000_000_000,
        provider="mistral",
        model_family="ministral",
        tags=["chat", "efficient", "edge"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.08,
            tokens_per_second=200.0,
            min_delay=0.004,
            max_delay=0.007,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="ministral-3b",
            created=1727740800,  # 2025-10-01 (approximate)
            owned_by="mistral",
            capabilities=ministral_3b_caps,
            display_name="Ministral 3B",
            description="Ultra-efficient 3B model for edge deployment and high-throughput use cases.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.04,
                    "output_per_million": 0.04,
                },
                "license": "Commercial",
            },
        )
    )

    # Mistral 7B (Original single-expert model - Legacy)
    mistral_7b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=32768,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=7_000_000_000,
        provider="mistral",
        model_family="mistral",
        tags=["chat", "efficient", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.145,
            tokens_per_second=125.0,
            min_delay=0.007,
            max_delay=0.01,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="mistralai/Mistral-7B-Instruct-v0.2",
            created=1702339200,  # 2023-12-12
            owned_by="mistral",
            capabilities=mistral_7b_caps,
            display_name="Mistral 7B Instruct v0.2 (Legacy)",
            description="Legacy 7B model. Consider upgrading to Ministral 3B or Mistral Small for better performance.",
            version="0.2",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.25,
                    "output_per_million": 0.25,
                },
                "license": "Apache 2.0",
            },
        )
    )

    return models


# Export the models list
MISTRAL_MODELS = _get_mistral_models()


def get_mistral_models() -> list[ModelDefinition]:
    """
    Get all Mistral AI models.

    Returns:
        List of Mistral ModelDefinition instances
    """
    return MISTRAL_MODELS.copy()
