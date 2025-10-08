"""
Meta Llama Model Catalog

Complete catalog of Meta's Llama models (Llama 4, Llama 3.1, Llama 3, Llama 2)
with accurate capabilities and performance characteristics.

Updated: October 2025
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import (
    CAPABILITY_PRESETS,
    LatencyProfile,
    MoEConfig,
)
from ..definition import ModelDefinition


def _get_meta_models() -> list[ModelDefinition]:
    """
    Get all Meta Llama model definitions.

    Returns:
        List of Meta ModelDefinition instances
    """
    models = []

    # Llama 4 Family (April 2025 - Latest)

    # Llama 4 Scout (10M context!)
    llama_4_scout_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=10_000_000,  # 10 million tokens!
        max_output_tokens=32768,
        supports_json_mode=True,
        supports_vision=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=109_000_000_000,
            active_params=17_000_000_000,
            num_experts=16,
            experts_per_token=1,
        ),
        parameter_count=109_000_000_000,
        provider="meta",
        model_family="llama-4",
        tags=[
            "chat",
            "vision",
            "multimodal",
            "moe",
            "ultra-long-context",
            "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.45,
            tokens_per_second=55.0,
            min_delay=0.016,
            max_delay=0.022,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-4-Scout",
            created=1743811200,  # 2025-04-05
            owned_by="meta",
            capabilities=llama_4_scout_caps,
            display_name="Llama 4 Scout",
            description="Revolutionary 10M token context window model. 17B active params, 109B total (16 experts). First multimodal Llama.",
            version="4.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.19,
                    "output_per_million": 0.19,
                },
                "license": "Llama 4 Community License (free up to 700M MAU)",
            },
        )
    )

    # Llama 4 Maverick (1M context)
    llama_4_maverick_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=1_000_000,
        max_output_tokens=32768,
        supports_json_mode=True,
        supports_vision=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=400_000_000_000,
            active_params=17_000_000_000,
            num_experts=128,
            experts_per_token=1,
        ),
        parameter_count=400_000_000_000,
        provider="meta",
        model_family="llama-4",
        tags=["chat", "vision", "multimodal", "moe", "powerful", "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.55,
            tokens_per_second=47.0,
            min_delay=0.019,
            max_delay=0.026,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-4-Maverick",
            created=1743811200,
            owned_by="meta",
            capabilities=llama_4_maverick_caps,
            display_name="Llama 4 Maverick",
            description="Powerful Llama 4 with 1M context. 17B active params, 400B total (128 experts). Multimodal support.",
            version="4.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.19,
                    "output_per_million": 0.19,
                },
                "license": "Llama 4 Community License (free up to 700M MAU)",
            },
        ))

    # Llama 4 Behemoth (Announced, training)
    # Note: Including as placeholder since it was announced but not released
    # yet
    llama_4_behemoth_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=1_000_000,
        max_output_tokens=32768,
        supports_json_mode=True,
        supports_vision=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=2_000_000_000_000,  # 2T total!
            active_params=288_000_000_000,  # 288B active
            num_experts=16,
            experts_per_token=1,
        ),
        parameter_count=2_000_000_000_000,
        provider="meta",
        model_family="llama-4",
        tags=["chat", "vision", "multimodal", "moe", "flagship", "training"],
        latency_profile=LatencyProfile(
            time_to_first_token=1.2,
            tokens_per_second=20.0,
            min_delay=0.045,
            max_delay=0.06,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="meta-llama/Llama-4-Behemoth",
            created=1743811200,
            owned_by="meta",
            capabilities=llama_4_behemoth_caps,
            display_name="Llama 4 Behemoth (Training)",
            description="Flagship Llama 4: 288B active params, ~2T total (16 experts). Still in training as of Oct 2025.",
            version="4.0-preview",
            custom_fields={
                "pricing": {
                    "input_per_million": 5.0,  # Estimated
                    "output_per_million": 15.0,  # Estimated
                },
                "license": "Llama 4 Community License (free up to 700M MAU)",
                "status": "training",
            },
        )
    )

    # Llama 3.1 Family (July 2024)

    # Llama 3.1 405B
    llama_31_405b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=405_000_000_000,
        provider="meta",
        model_family="llama-3.1",
        tags=["chat", "large", "flagship"],
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
            description="Flagship Llama 3.1 model with 405B parameters and 128K context. Consider upgrading to Llama 4.",
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
        tags=["chat", "balanced"],
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
            description="Balanced Llama 3.1 with 70B parameters and 128K context.",
            version="3.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.88,
                    "output_per_million": 0.88,
                },
                "license": "Llama 3.1 Community License",
            },
        ))

    # Llama 3.1 8B
    llama_31_8b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        parameter_count=8_000_000_000,
        provider="meta",
        model_family="llama-3.1",
        tags=["chat", "efficient"],
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
            description="Efficient Llama 3.1 with 8B parameters and 128K context.",
            version="3.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.18,
                    "output_per_million": 0.18,
                },
                "license": "Llama 3.1 Community License",
            },
        ))

    # Llama 3 Family (April 2024 - Legacy)

    # Llama 3 70B
    llama_3_70b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=8192,
        max_output_tokens=4096,
        parameter_count=70_000_000_000,
        provider="meta",
        model_family="llama-3",
        tags=["chat", "balanced", "legacy"],
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
            display_name="Llama 3 70B Instruct (Legacy)",
            description="Legacy Llama 3 model. Consider upgrading to Llama 3.1 or Llama 4.",
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
        tags=["chat", "efficient", "legacy"],
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
            display_name="Llama 3 8B Instruct (Legacy)",
            description="Legacy Llama 3 model. Consider upgrading to Llama 3.1 or Llama 4.",
            version="3.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.18,
                    "output_per_million": 0.18,
                },
                "license": "Llama 3 Community License",
            },
        ))

    # Llama 2 Family (July 2023 - Legacy, kept for compatibility)

    # Llama 2 70B
    llama_2_70b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=4096,
        max_output_tokens=4096,
        supports_function_calling=False,
        parameter_count=70_000_000_000,
        provider="meta",
        model_family="llama-2",
        tags=["chat", "legacy", "deprecated"],
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
            display_name="Llama 2 70B Chat (Legacy)",
            description="Legacy Llama 2. Strongly consider upgrading to Llama 4 for better performance.",
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
