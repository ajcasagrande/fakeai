"""
OpenAI Model Catalog

Complete catalog of OpenAI models including GPT-OSS, GPT-4, GPT-3.5, O1,
embeddings, and moderation models with accurate pricing and capabilities.
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import (
    CAPABILITY_PRESETS,
    LatencyProfile,
    ModelCapabilities,
    MoEConfig,
)
from ..definition import ModelDefinition, create_model_definition


def _get_openai_models() -> list[ModelDefinition]:
    """
    Get all OpenAI model definitions.

    Returns:
        List of OpenAI ModelDefinition instances
    """
    models = []

    # GPT-OSS Models (Open-source reasoning models with MoE architecture)
    # Released August 2025, Apache 2.0 license

    # GPT-OSS-120B (flagship reasoning model)
    gpt_oss_120b_caps = CAPABILITY_PRESETS["reasoning"].clone(
        supports_vision=True,
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        max_context_length=128000,
        max_output_tokens=16384,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=120_000_000_000,
            active_params=37_000_000_000,
            num_experts=16,
            experts_per_token=2,
        ),
        parameter_count=120_000_000_000,
        provider="openai",
        model_family="gpt-oss",
        tags=["reasoning", "vision", "audio", "moe", "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.6,
            tokens_per_second=35.0,
            min_delay=0.02,
            max_delay=0.04,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="openai/gpt-oss-120b",
            created=1704067200,  # 2024-01-01
            owned_by="openai",
            capabilities=gpt_oss_120b_caps,
            display_name="GPT-OSS-120B",
            description="120B parameter reasoning model with vision and audio. MoE architecture, supports predicted outputs.",
            version="2024-08-01",
            custom_fields={
                "pricing": {
                    "input_per_million": 10.0,
                    "output_per_million": 30.0,
                    "cached_input_per_million": 5.0,
                },
                "license": "Apache 2.0",
            },
        )
    )

    # GPT-OSS-20B (smaller efficient reasoning model)
    gpt_oss_20b_caps = CAPABILITY_PRESETS["reasoning"].clone(
        supports_vision=True,
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        max_context_length=128000,
        max_output_tokens=16384,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=20_000_000_000,
            active_params=7_000_000_000,
            num_experts=8,
            experts_per_token=2,
        ),
        parameter_count=20_000_000_000,
        provider="openai",
        model_family="gpt-oss",
        tags=["reasoning", "vision", "audio", "moe", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.3,
            tokens_per_second=67.0,
            min_delay=0.01,
            max_delay=0.02,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="openai/gpt-oss-20b",
            created=1704067200,
            owned_by="openai",
            capabilities=gpt_oss_20b_caps,
            display_name="GPT-OSS-20B",
            description="20B parameter efficient reasoning model with vision and audio. MoE architecture.",
            version="2024-08-01",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.15,
                    "output_per_million": 0.60,
                    "cached_input_per_million": 0.075,
                },
                "license": "Apache 2.0",
            },
        )
    )

    # GPT-4 Family

    # GPT-4 (original)
    gpt4_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=8192,
        max_output_tokens=8192,
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
        tags=["chat", "moe", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.8,
            tokens_per_second=28.0,
            min_delay=0.03,
            max_delay=0.05,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="openai/gpt-oss-120b",
            created=1678886400,  # 2023-03-15
            owned_by="openai",
            capabilities=gpt4_caps,
            display_name="GPT-4",
            description="Original GPT-4 model with 8K context window. MoE architecture.",
            version="0613",
            custom_fields={
                "pricing": {
                    "input_per_million": 30.0,
                    "output_per_million": 60.0,
                },
            },
        )
    )

    # GPT-4 Turbo
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
        tags=["chat", "vision", "moe", "turbo"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.4,
            tokens_per_second=50.0,
            min_delay=0.018,
            max_delay=0.025,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="openai/gpt-oss-120b",
            created=1699481600,  # 2023-11-09
            owned_by="openai",
            capabilities=gpt4_turbo_caps,
            display_name="GPT-4 Turbo",
            description="Fast GPT-4 with 128K context window and vision capabilities.",
            version="1106-preview",
            custom_fields={
                "pricing": {
                    "input_per_million": 10.0,
                    "output_per_million": 30.0,
                },
            },
        )
    )

    # openai/gpt-oss-120b (multimodal flagship)
    gpt4o_caps = CAPABILITY_PRESETS["multimodal"].clone(
        max_context_length=128000,
        max_output_tokens=16384,
        supports_predicted_outputs=True,
        supports_parallel_tool_calls=True,
        parameter_count=200_000_000_000,
        provider="openai",
        model_family="gpt-4o",
        tags=["chat", "vision", "audio", "multimodal", "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.25,
            tokens_per_second=67.0,
            min_delay=0.012,
            max_delay=0.018,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="openai/gpt-oss-120b",
            created=1715644800,  # 2024-05-14
            owned_by="openai",
            capabilities=gpt4o_caps,
            display_name="GPT-4o",
            description="Flagship multimodal model with vision, audio, and predicted outputs support.",
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

    # openai/gpt-oss-20b (small efficient multimodal)
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
            model_id="openai/gpt-oss-20b",
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

    # GPT-3.5 Turbo Family

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
            model_id="meta-llama/Llama-3.1-8B-Instruct",
            created=1677628800,  # 2023-03-01
            owned_by="openai",
            capabilities=gpt35_caps,
            display_name="GPT-3.5 Turbo",
            description="Fast and efficient chat model with 16K context window.",
            version="0125",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.50,
                    "output_per_million": 1.50,
                },
            },
        )
    )

    # O1 Family (Reasoning Models - Legacy)

    o1_caps = CAPABILITY_PRESETS["reasoning"].clone(
        supports_vision=False,
        supports_audio_input=False,
        supports_function_calling=False,
        supports_tool_use=False,
        supports_json_mode=True,
        max_context_length=200000,
        max_output_tokens=100000,
        parameter_count=671_000_000_000,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=671_000_000_000,
            active_params=37_000_000_000,
            num_experts=256,
            experts_per_token=8,
        ),
        provider="openai",
        model_family="o1",
        tags=["reasoning", "moe", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.7,
            tokens_per_second=33.0,
            min_delay=0.025,
            max_delay=0.04,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="deepseek-ai/DeepSeek-R1",
            created=1725840000,  # 2024-09-09
            owned_by="openai",
            capabilities=o1_caps,
            display_name="O1 (Legacy)",
            description="Legacy reasoning model (based on DeepSeek architecture). Use GPT-OSS for latest reasoning.",
            version="2024-09-12",
            custom_fields={
                "pricing": {
                    "input_per_million": 15.0,
                    "output_per_million": 60.0,
                },
            },
        )
    )

    o1_mini_caps = CAPABILITY_PRESETS["reasoning"].clone(
        supports_vision=False,
        supports_audio_input=False,
        supports_function_calling=False,
        supports_tool_use=False,
        supports_json_mode=True,
        max_context_length=128000,
        max_output_tokens=65536,
        parameter_count=32_000_000_000,
        provider="openai",
        model_family="o1",
        tags=["reasoning", "efficient", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.35,
            tokens_per_second=62.0,
            min_delay=0.014,
            max_delay=0.02,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            created=1725840000,
            owned_by="openai",
            capabilities=o1_mini_caps,
            display_name="O1 Mini (Legacy)",
            description="Small reasoning model. Use GPT-OSS-20B for latest efficient reasoning.",
            version="2024-09-12",
            custom_fields={
                "pricing": {
                    "input_per_million": 3.0,
                    "output_per_million": 12.0,
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
            model_id="nomic-ai/nomic-embed-text-v1.5",
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
            model_id="BAAI/bge-m3",
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
            model_id="sentence-transformers/all-mpnet-base-v2",
            created=1672531200,  # 2023-01-01
            owned_by="openai",
            capabilities=embedding_ada_caps,
            display_name="text-embedding-ada-002",
            description="Legacy embedding model with 1536 dimensions.",
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
