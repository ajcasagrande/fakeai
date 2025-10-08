"""
OpenAI Model Catalog

Complete catalog of OpenAI models including GPT-5, GPT-4.1, GPT-4o, GPT-3.5,
embeddings, and moderation models with accurate pricing and capabilities.

Updated: October 2025
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import (
    CAPABILITY_PRESETS,
    LatencyProfile,
    MoEConfig,
)
from ..definition import ModelDefinition


def _get_openai_models() -> list[ModelDefinition]:
    """
    Get all OpenAI model definitions.

    Returns:
        List of OpenAI ModelDefinition instances
    """
    models = []

    # GPT-5 Family (Released August 2025)

    # GPT-5 (Flagship)
    gpt5_caps = CAPABILITY_PRESETS["reasoning"].clone(
        supports_vision=True,
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        max_context_length=400000,  # 272K input + 128K output
        max_output_tokens=128000,
        parameter_count=None,  # Not disclosed
        provider="openai",
        model_family="gpt-5",
        tags=[
            "reasoning",
            "vision",
            "audio",
            "multimodal",
            "latest",
            "flagship"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.35,
            tokens_per_second=60.0,
            min_delay=0.015,
            max_delay=0.022,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-5",
            created=1723075200,  # 2025-08-07
            owned_by="openai",
            capabilities=gpt5_caps,
            display_name="GPT-5",
            description="OpenAI's most advanced model with 400K context window, multimodal capabilities, and real-time routing between reasoning modes.",
            version="2025-08-07",
            custom_fields={
                "pricing": {
                    "input_per_million": 1.25,
                    "output_per_million": 10.0,
                },
            },
        )
    )

    # GPT-5 Mini (Efficient variant)
    gpt5_mini_caps = CAPABILITY_PRESETS["reasoning"].clone(
        supports_vision=True,
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        max_context_length=256000,
        max_output_tokens=64000,
        parameter_count=None,
        provider="openai",
        model_family="gpt-5",
        tags=["reasoning", "vision", "audio", "multimodal", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.22,
            tokens_per_second=90.0,
            min_delay=0.01,
            max_delay=0.015,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-5-mini",
            created=1723075200,
            owned_by="openai",
            capabilities=gpt5_mini_caps,
            display_name="GPT-5 Mini",
            description="Efficient GPT-5 variant with strong performance and lower cost.",
            version="2025-08-07",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.50,
                    "output_per_million": 2.50,
                },
            },
        ))

    # GPT-5 Nano (Most efficient)
    gpt5_nano_caps = CAPABILITY_PRESETS["chat"].clone(
        supports_vision=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        max_context_length=128000,
        max_output_tokens=16384,
        parameter_count=None,
        provider="openai",
        model_family="gpt-5",
        tags=["chat", "vision", "efficient", "fast"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.15,
            tokens_per_second=120.0,
            min_delay=0.007,
            max_delay=0.012,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-5-nano",
            created=1723075200,
            owned_by="openai",
            capabilities=gpt5_nano_caps,
            display_name="GPT-5 Nano",
            description="Ultra-efficient GPT-5 variant for high-throughput tasks.",
            version="2025-08-07",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.20,
                    "output_per_million": 0.80,
                },
            },
        ))

    # GPT-4.1 Family (Latest GPT-4 generation)

    # GPT-4.1 (Main model)
    gpt41_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=1000000,  # 1M tokens
        max_output_tokens=32768,
        supports_json_mode=True,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,
        provider="openai",
        model_family="gpt-4.1",
        tags=["chat", "vision", "coding", "long-context"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.32,
            tokens_per_second=65.0,
            min_delay=0.014,
            max_delay=0.02,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-4.1",
            created=1727740800,  # 2025-10-01 (approximate)
            owned_by="openai",
            capabilities=gpt41_caps,
            display_name="GPT-4.1",
            description="Latest GPT-4 generation with 1M context window, excellent for coding and instruction following.",
            version="2025-10-01",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.0,
                    "output_per_million": 8.0,
                },
            },
        )
    )

    # GPT-4.1 Mini
    gpt41_mini_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=512000,
        max_output_tokens=16384,
        supports_json_mode=True,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,
        provider="openai",
        model_family="gpt-4.1",
        tags=["chat", "vision", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.20,
            tokens_per_second=95.0,
            min_delay=0.009,
            max_delay=0.014,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-4.1-mini",
            created=1727740800,
            owned_by="openai",
            capabilities=gpt41_mini_caps,
            display_name="GPT-4.1 Mini",
            description="Efficient GPT-4.1 variant with strong performance at lower cost.",
            version="2025-10-01",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.40,
                    "output_per_million": 1.60,
                },
            },
        ))

    # GPT-4.1 Nano
    gpt41_nano_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=8192,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        parameter_count=None,
        provider="openai",
        model_family="gpt-4.1",
        tags=["chat", "efficient", "fast"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.12,
            tokens_per_second=140.0,
            min_delay=0.006,
            max_delay=0.01,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-4.1-nano",
            created=1727740800,
            owned_by="openai",
            capabilities=gpt41_nano_caps,
            display_name="GPT-4.1 Nano",
            description="Ultra-efficient GPT-4.1 variant for cost-sensitive workloads.",
            version="2025-10-01",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.10,
                    "output_per_million": 0.40,
                },
            },
        ))

    # GPT-4o (Multimodal flagship - 2024)
    gpt4o_caps = CAPABILITY_PRESETS["multimodal"].clone(
        max_context_length=128000,
        max_output_tokens=16384,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        parameter_count=200_000_000_000,
        provider="openai",
        model_family="gpt-4o",
        tags=["chat", "vision", "audio", "multimodal"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.25,
            tokens_per_second=67.0,
            min_delay=0.012,
            max_delay=0.018,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-4o",
            created=1715644800,  # 2024-05-14
            owned_by="openai",
            capabilities=gpt4o_caps,
            display_name="GPT-4o",
            description="Multimodal model with vision, audio, and predicted outputs support.",
            version="2024-08-06",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.50,
                    "output_per_million": 10.0,
                    "cached_input_per_million": 1.25,
                },
            },
        )
    )

    # GPT-4o Mini (Small efficient multimodal)
    gpt4o_mini_caps = CAPABILITY_PRESETS["multimodal"].clone(
        max_context_length=128000,
        max_output_tokens=16384,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        parameter_count=8_000_000_000,
        provider="openai",
        model_family="gpt-4o",
        tags=["chat", "vision", "audio", "multimodal", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.18,
            tokens_per_second=100.0,
            min_delay=0.008,
            max_delay=0.012,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-4o-mini",
            created=1720569600,  # 2024-07-10
            owned_by="openai",
            capabilities=gpt4o_mini_caps,
            display_name="GPT-4o Mini",
            description="Small, efficient multimodal model with excellent price/performance.",
            version="2024-07-18",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.15,
                    "output_per_million": 0.60,
                    "cached_input_per_million": 0.075,
                },
            },
        )
    )

    # GPT-4 Turbo (Legacy)
    gpt4_turbo_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=1_760_000_000_000,
            active_params=220_000_000_000,
            num_experts=8,
            experts_per_token=1,
        ),
        parameter_count=1_760_000_000_000,
        provider="openai",
        model_family="gpt-4",
        tags=["chat", "vision", "moe", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.4,
            tokens_per_second=50.0,
            min_delay=0.018,
            max_delay=0.025,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-4-turbo",
            created=1699481600,  # 2023-11-09
            owned_by="openai",
            capabilities=gpt4_turbo_caps,
            display_name="GPT-4 Turbo (Legacy)",
            description="Legacy GPT-4 with 128K context window and vision. Consider upgrading to GPT-4.1 or GPT-5.",
            version="1106-preview",
            custom_fields={
                "pricing": {
                    "input_per_million": 10.0,
                    "output_per_million": 30.0,
                },
            },
        )
    )

    # GPT-3.5 Turbo (Legacy)
    gpt35_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=16385,
        max_output_tokens=4096,
        parameter_count=175_000_000_000,
        provider="openai",
        model_family="gpt-3.5",
        tags=["chat", "legacy", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.2,
            tokens_per_second=100.0,
            min_delay=0.008,
            max_delay=0.012,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gpt-3.5-turbo",
            created=1677628800,  # 2023-03-01
            owned_by="openai",
            capabilities=gpt35_caps,
            display_name="GPT-3.5 Turbo (Legacy)",
            description="Legacy fast and efficient chat model. Consider upgrading to GPT-4.1-nano for better performance.",
            version="0125",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.50,
                    "output_per_million": 1.50,
                },
            },
        )
    )

    # Embedding Models

    embedding_small_caps = CAPABILITY_PRESETS["embeddings"].clone(
        max_context_length=8191,
        provider="openai",
        model_family="embeddings",
        tags=["embeddings", "efficient"],
        parameter_count=None,
    )

    models.append(
        ModelDefinition(
            model_id="text-embedding-3-small",
            created=1704931200,  # 2024-01-11
            owned_by="openai",
            capabilities=embedding_small_caps,
            display_name="text-embedding-3-small",
            description="Small, efficient embedding model with 1536 dimensions.",
            version="3",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.02,
                    "output_per_million": 0.0,
                },
                "dimensions": 1536,
            },
        )
    )

    embedding_large_caps = CAPABILITY_PRESETS["embeddings"].clone(
        max_context_length=8191,
        provider="openai",
        model_family="embeddings",
        tags=["embeddings", "large"],
        parameter_count=None,
    )

    models.append(
        ModelDefinition(
            model_id="text-embedding-3-large",
            created=1704931200,
            owned_by="openai",
            capabilities=embedding_large_caps,
            display_name="text-embedding-3-large",
            description="Large embedding model with 3072 dimensions.",
            version="3",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.13,
                    "output_per_million": 0.0,
                },
                "dimensions": 3072,
            },
        )
    )

    embedding_ada_caps = CAPABILITY_PRESETS["embeddings"].clone(
        max_context_length=8191,
        provider="openai",
        model_family="embeddings",
        tags=["embeddings", "legacy"],
        parameter_count=None,
    )

    models.append(
        ModelDefinition(
            model_id="text-embedding-ada-002",
            created=1672531200,  # 2023-01-01
            owned_by="openai",
            capabilities=embedding_ada_caps,
            display_name="text-embedding-ada-002 (Legacy)",
            description="Legacy embedding model. Consider upgrading to text-embedding-3-small.",
            version="2",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.10,
                    "output_per_million": 0.0,
                },
                "dimensions": 1536,
            },
        )
    )

    # Moderation Models

    moderation_caps = CAPABILITY_PRESETS["moderation"].clone(
        max_context_length=32768,
        provider="openai",
        model_family="moderation",
        tags=["moderation", "safety"],
    )

    models.append(
        ModelDefinition(
            model_id="text-moderation-latest",
            created=1677628800,
            owned_by="openai",
            capabilities=moderation_caps,
            display_name="Text Moderation (Latest)",
            description="Latest content moderation model for safety checking.",
            version="latest",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.0,
                    "output_per_million": 0.0,
                },
            },
        )
    )

    models.append(
        ModelDefinition(
            model_id="text-moderation-stable",
            created=1677628800,
            owned_by="openai",
            capabilities=moderation_caps,
            display_name="Text Moderation (Stable)",
            description="Stable content moderation model for safety checking.",
            version="stable",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.0,
                    "output_per_million": 0.0,
                },
            },
        )
    )

    return models


# Export the models list
OPENAI_MODELS = _get_openai_models()


def get_openai_models() -> list[ModelDefinition]:
    """
    Get all OpenAI models.

    Returns:
        List of OpenAI ModelDefinition instances
    """
    return OPENAI_MODELS.copy()
