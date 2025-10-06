"""
Mistral AI Model Catalog

Complete catalog of Mistral AI models including Mixtral (MoE) and Mistral models
with accurate pricing and capabilities.
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import (
    CAPABILITY_PRESETS,
    LatencyProfile,
    ModelCapabilities,
    MoEConfig,
)
from ..definition import ModelDefinition, create_model_definition


def _get_mistral_models() -> list[ModelDefinition]:
    """
    Get all Mistral AI model definitions.

    Returns:
        List of Mistral ModelDefinition instances
    """
    models = []

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
        tags=["chat", "moe", "large", "flagship"],
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
            total_params=46_700_000_000,  # 8 experts × 7B each (with shared layers)
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

    # Short alias for Mixtral 8x7B
    models.append(
        ModelDefinition(
            model_id="mixtral-8x7b",
            created=1702339200,
            owned_by="mistral",
            capabilities=mixtral_8x7b_caps,
            display_name="Mixtral 8x7B",
            description="Alias for Mixtral 8x7B Instruct. Balanced MoE model.",
            version="0.1",
            parent="mistralai/Mixtral-8x7B-Instruct-v0.1",
            root="mistralai/Mixtral-8x7B-Instruct-v0.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.70,
                    "output_per_million": 0.70,
                },
                "license": "Apache 2.0",
            },
        )
    )

    # Short alias for Mixtral 8x22B
    models.append(
        ModelDefinition(
            model_id="mixtral-8x22b",
            created=1712793600,
            owned_by="mistral",
            capabilities=mixtral_8x22b_caps,
            display_name="Mixtral 8x22B",
            description="Alias for Mixtral 8x22B Instruct. Large MoE model.",
            version="0.1",
            parent="mistralai/Mixtral-8x22B-Instruct-v0.1",
            root="mistralai/Mixtral-8x22B-Instruct-v0.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.0,
                    "output_per_million": 6.0,
                },
                "license": "Apache 2.0",
            },
        )
    )

    # Mistral 7B (Original single-expert model)
    mistral_7b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=32768,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=7_000_000_000,
        provider="mistral",
        model_family="mistral",
        tags=["chat", "efficient"],
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
            display_name="Mistral 7B Instruct v0.2",
            description="Efficient 7B parameter model with 32K context window.",
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

    # Mistral Small (Commercial)
    mistral_small_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=32768,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        parameter_count=None,  # Not disclosed
        provider="mistral",
        model_family="mistral",
        tags=["chat", "efficient", "commercial"],
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
            description="Efficient commercial model optimized for cost and latency.",
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

    # Mistral Medium (Commercial)
    mistral_medium_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=32768,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        parameter_count=None,
        provider="mistral",
        model_family="mistral",
        tags=["chat", "balanced", "commercial"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.35,
            tokens_per_second=55.0,
            min_delay=0.016,
            max_delay=0.022,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="mistral-medium-latest",
            created=1717200000,
            owned_by="mistral",
            capabilities=mistral_medium_caps,
            display_name="Mistral Medium",
            description="Balanced commercial model for general-purpose use.",
            version="latest",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.7,
                    "output_per_million": 8.1,
                },
                "license": "Commercial",
            },
        )
    )

    # Mistral Large (Commercial flagship)
    mistral_large_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,
        provider="mistral",
        model_family="mistral",
        tags=["chat", "large", "commercial", "flagship"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.5,
            tokens_per_second=45.0,
            min_delay=0.02,
            max_delay=0.028,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="mistral-large-latest",
            created=1717200000,
            owned_by="mistral",
            capabilities=mistral_large_caps,
            display_name="Mistral Large",
            description="Flagship commercial model with 128K context window.",
            version="latest",
            custom_fields={
                "pricing": {
                    "input_per_million": 4.0,
                    "output_per_million": 12.0,
                },
                "license": "Commercial",
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
