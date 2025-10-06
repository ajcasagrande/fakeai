"""
Meta Llama Model Catalog

Complete catalog of Meta's Llama models (Llama 3.1, Llama 3, Llama 2)
with accurate capabilities and performance characteristics.
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import CAPABILITY_PRESETS, LatencyProfile, ModelCapabilities
from ..definition import ModelDefinition, create_model_definition


def _get_meta_models() -> list[ModelDefinition]:
    """
    Get all Meta Llama model definitions.

    Returns:
        List of Meta ModelDefinition instances
    """
    models = []

    # Llama 3.1 Family (Latest - July 2024)

    # Llama 3.1 405B (Flagship)
    llama_31_405b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=405_000_000_000,
        provider="meta",
        model_family="llama-3.1",
        tags=["chat", "large", "flagship", "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.9,
            tokens_per_second=24.0,
            min_delay=0.038,
            max_delay=0.05,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-3.1-405B-Instruct",
            created=1721606400,  # 2024-07-22
            owned_by="meta",
            capabilities=llama_31_405b_caps,
            display_name="Llama 3.1 405B Instruct",
            description="Flagship Llama model with 405B parameters and 128K context window.",
            version="3.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 5.0,
                    "output_per_million": 15.0,
                },
                "license": "Llama 3.1 Community License",
            },
        )
    )

    # Llama 3.1 70B
    llama_31_70b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=70_000_000_000,
        provider="meta",
        model_family="llama-3.1",
        tags=["chat", "balanced", "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.48,
            tokens_per_second=43.0,
            min_delay=0.021,
            max_delay=0.028,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-3.1-70B-Instruct",
            created=1721606400,
            owned_by="meta",
            capabilities=llama_31_70b_caps,
            display_name="Llama 3.1 70B Instruct",
            description="Balanced Llama model with 70B parameters and 128K context window.",
            version="3.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.88,
                    "output_per_million": 0.88,
                },
                "license": "Llama 3.1 Community License",
            },
        )
    )

    # Llama 3.1 8B
    llama_31_8b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=8_000_000_000,
        provider="meta",
        model_family="llama-3.1",
        tags=["chat", "efficient", "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.14,
            tokens_per_second=133.0,
            min_delay=0.006,
            max_delay=0.009,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-3.1-8B-Instruct",
            created=1721606400,
            owned_by="meta",
            capabilities=llama_31_8b_caps,
            display_name="Llama 3.1 8B Instruct",
            description="Efficient Llama model with 8B parameters and 128K context window.",
            version="3.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.18,
                    "output_per_million": 0.18,
                },
                "license": "Llama 3.1 Community License",
            },
        )
    )

    # Llama 3 Family (April 2024)

    # Llama 3 70B
    llama_3_70b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=8192,
        max_output_tokens=4096,
        parameter_count=70_000_000_000,
        provider="meta",
        model_family="llama-3",
        tags=["chat", "balanced"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.5,
            tokens_per_second=42.0,
            min_delay=0.022,
            max_delay=0.029,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-3-70B-Instruct",
            created=1713398400,  # 2024-04-18
            owned_by="meta",
            capabilities=llama_3_70b_caps,
            display_name="Llama 3 70B Instruct",
            description="Llama 3 model with 70B parameters and 8K context window.",
            version="3.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.88,
                    "output_per_million": 0.88,
                },
                "license": "Llama 3 Community License",
            },
        )
    )

    # Llama 3 8B
    llama_3_8b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=8192,
        max_output_tokens=4096,
        parameter_count=8_000_000_000,
        provider="meta",
        model_family="llama-3",
        tags=["chat", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.15,
            tokens_per_second=125.0,
            min_delay=0.007,
            max_delay=0.01,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-3-8B-Instruct",
            created=1713398400,
            owned_by="meta",
            capabilities=llama_3_8b_caps,
            display_name="Llama 3 8B Instruct",
            description="Efficient Llama 3 model with 8B parameters and 8K context window.",
            version="3.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.18,
                    "output_per_million": 0.18,
                },
                "license": "Llama 3 Community License",
            },
        )
    )

    # Llama 2 Family (July 2023 - Legacy)

    # Llama 2 70B
    llama_2_70b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=4096,
        max_output_tokens=4096,
        supports_function_calling=False,
        parameter_count=70_000_000_000,
        provider="meta",
        model_family="llama-2",
        tags=["chat", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.5,
            tokens_per_second=42.0,
            min_delay=0.022,
            max_delay=0.029,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-2-70b-chat-hf",
            created=1689206400,  # 2023-07-13
            owned_by="meta",
            capabilities=llama_2_70b_caps,
            display_name="Llama 2 70B Chat",
            description="Legacy Llama 2 model with 70B parameters. Consider upgrading to Llama 3.",
            version="2.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.70,
                    "output_per_million": 0.90,
                },
                "license": "Llama 2 Community License",
            },
        )
    )

    # Llama 2 13B
    llama_2_13b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=4096,
        max_output_tokens=4096,
        supports_function_calling=False,
        parameter_count=13_000_000_000,
        provider="meta",
        model_family="llama-2",
        tags=["chat", "legacy", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.22,
            tokens_per_second=83.0,
            min_delay=0.01,
            max_delay=0.015,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-2-13b-chat-hf",
            created=1689206400,
            owned_by="meta",
            capabilities=llama_2_13b_caps,
            display_name="Llama 2 13B Chat",
            description="Legacy Llama 2 model with 13B parameters. Consider upgrading to Llama 3.",
            version="2.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.30,
                    "output_per_million": 0.30,
                },
                "license": "Llama 2 Community License",
            },
        )
    )

    # Llama 2 7B
    llama_2_7b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=4096,
        max_output_tokens=4096,
        supports_function_calling=False,
        parameter_count=7_000_000_000,
        provider="meta",
        model_family="llama-2",
        tags=["chat", "legacy", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.15,
            tokens_per_second=125.0,
            min_delay=0.007,
            max_delay=0.01,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-2-7b-chat-hf",
            created=1689206400,
            owned_by="meta",
            capabilities=llama_2_7b_caps,
            display_name="Llama 2 7B Chat",
            description="Legacy Llama 2 model with 7B parameters. Consider upgrading to Llama 3.",
            version="2.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.20,
                    "output_per_million": 0.20,
                },
                "license": "Llama 2 Community License",
            },
        )
    )

    return models


# Export the models list
META_MODELS = _get_meta_models()


def get_meta_models() -> list[ModelDefinition]:
    """
    Get all Meta Llama models.

    Returns:
        List of Meta ModelDefinition instances
    """
    return META_MODELS.copy()
