"""
Cohere Model Catalog

Complete catalog of Cohere models including Command A family, Command R family,
and specialized models with accurate pricing and capabilities.

Updated: October 2025
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import CAPABILITY_PRESETS, LatencyProfile, ModelCapabilities
from ..definition import ModelDefinition


def _get_cohere_models() -> list[ModelDefinition]:
    """
    Get all Cohere model definitions.

    Returns:
        List of Cohere ModelDefinition instances
    """
    models = []

    # Command A Vision (Latest multimodal - July 2025)
    command_a_vision_caps = CAPABILITY_PRESETS["vision"].clone(
        max_context_length=256000,  # 256K tokens
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_parallel_tool_calls=True,
        parameter_count=111_000_000_000,
        provider="cohere",
        model_family="command-a",
        tags=["chat", "vision", "multimodal", "latest", "enterprise"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.40,
            tokens_per_second=52.0,
            min_delay=0.017,
            max_delay=0.024,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="command-a-vision",
            created=1753401600,  # 2025-07-31
            owned_by="cohere",
            capabilities=command_a_vision_caps,
            display_name="Command A Vision",
            description="Latest multimodal Command A with vision capabilities, 256K context, and 111B parameters.",
            version="2025-07",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.50,
                    "output_per_million": 10.0,
                },
            },
        )
    )

    # Command A Reasoning (Specialized reasoning - August 2025)
    command_a_reasoning_caps = CAPABILITY_PRESETS["reasoning"].clone(
        max_context_length=256000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_parallel_tool_calls=True,
        supports_vision=False,
        supports_audio_input=False,
        parameter_count=111_000_000_000,
        provider="cohere",
        model_family="command-a",
        tags=["reasoning", "chat", "latest", "enterprise"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.42,
            tokens_per_second=50.0,
            min_delay=0.018,
            max_delay=0.025,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="command-a-reasoning",
            created=1756080000,  # 2025-08-25
            owned_by="cohere",
            capabilities=command_a_reasoning_caps,
            display_name="Command A Reasoning",
            description="Specialized reasoning variant of Command A with 256K context for complex analytical tasks.",
            version="2025-08",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.50,
                    "output_per_million": 10.0,
                },
            },
        )
    )

    # Command A (Main model - March 2025)
    command_a_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=256000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_parallel_tool_calls=True,
        parameter_count=111_000_000_000,
        provider="cohere",
        model_family="command-a",
        tags=["chat", "enterprise", "flagship"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.38,
            tokens_per_second=54.0,
            min_delay=0.016,
            max_delay=0.023,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="command-a",
            created=1741996800,  # 2025-03-13
            owned_by="cohere",
            capabilities=command_a_caps,
            display_name="Command A",
            description="Enterprise-ready 111B parameter model with 256K context, 150% more efficient than Command R+.",
            version="2025-03",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.50,
                    "output_per_million": 10.0,
                },
            },
        )
    )

    # Command R+ (August 2024 update)
    command_rplus_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_parallel_tool_calls=True,
        parameter_count=104_000_000_000,
        provider="cohere",
        model_family="command-r",
        tags=["chat", "enterprise", "rag"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.45,
            tokens_per_second=47.0,
            min_delay=0.019,
            max_delay=0.026,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="command-r-plus",
            created=1722470400,  # 2024-08-01
            owned_by="cohere",
            capabilities=command_rplus_caps,
            display_name="Command R+",
            description="Powerful 104B model optimized for RAG and complex tasks. Consider upgrading to Command A.",
            version="08-2024",
            custom_fields={
                "pricing": {
                    "input_per_million": 2.50,
                    "output_per_million": 10.0,
                },
            },
        )
    )

    # Command R (Standard model)
    command_r_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_parallel_tool_calls=True,
        parameter_count=35_000_000_000,
        provider="cohere",
        model_family="command-r",
        tags=["chat", "efficient", "rag"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.12,  # Very low latency
            tokens_per_second=95.0,
            min_delay=0.009,
            max_delay=0.014,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="command-r",
            created=1717200000,  # 2024-06-01
            owned_by="cohere",
            capabilities=command_r_caps,
            display_name="Command R",
            description="Efficient 35B model optimized for RAG with lowest latency (0.12s TTFT) and 128K context.",
            version="06-2024",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.15,
                    "output_per_million": 0.60,
                },
            },
        )
    )

    # Command R7B (Small efficient model)
    command_r7b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        parameter_count=7_000_000_000,
        provider="cohere",
        model_family="command-r",
        tags=["chat", "efficient", "small"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.10,
            tokens_per_second=130.0,
            min_delay=0.006,
            max_delay=0.010,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="command-r7b",
            created=1717200000,
            owned_by="cohere",
            capabilities=command_r7b_caps,
            display_name="Command R7B",
            description="Small efficient 7B model with 128K context, ideal for high-throughput applications.",
            version="06-2024",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.0375,
                    "output_per_million": 0.15,
                },
            },
        ))

    # Aya Expanse 32B (Multilingual specialist)
    aya_expanse_32b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        parameter_count=32_000_000_000,
        provider="cohere",
        model_family="aya",
        tags=["chat", "multilingual", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.13,  # Very low latency
            tokens_per_second=90.0,
            min_delay=0.010,
            max_delay=0.015,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="aya-expanse-32b",
            created=1727740800,  # 2025-10-01 (approximate)
            owned_by="cohere",
            capabilities=aya_expanse_32b_caps,
            display_name="Aya Expanse 32B",
            description="Multilingual 32B model with exceptional low latency (0.13s TTFT) supporting 23+ languages.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.60,
                    "output_per_million": 2.40,
                },
                "languages": 23,
            },
        )
    )

    # Embed v3 (Embeddings model)
    embed_v3_caps = CAPABILITY_PRESETS["embeddings"].clone(
        max_context_length=512,
        provider="cohere",
        model_family="embed",
        tags=["embeddings", "multilingual"],
        parameter_count=None,
    )

    models.append(
        ModelDefinition(
            model_id="embed-english-v3.0",
            created=1699481600,  # 2023-11-09
            owned_by="cohere",
            capabilities=embed_v3_caps,
            display_name="Embed English v3",
            description="English embedding model with 1024 dimensions, optimized for search and clustering.",
            version="3.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.10,
                    "output_per_million": 0.0,
                },
                "dimensions": 1024,
            },
        )
    )

    embed_multilingual_v3_caps = embed_v3_caps.clone(
        tags=["embeddings", "multilingual"],
    )

    models.append(
        ModelDefinition(
            model_id="embed-multilingual-v3.0",
            created=1699481600,
            owned_by="cohere",
            capabilities=embed_multilingual_v3_caps,
            display_name="Embed Multilingual v3",
            description="Multilingual embedding model supporting 100+ languages with 1024 dimensions.",
            version="3.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.10,
                    "output_per_million": 0.0,
                },
                "dimensions": 1024,
                "languages": 100,
            },
        ))

    # Rerank v3.5 (Reranking model)
    rerank_caps = ModelCapabilities(
        supports_chat=False,
        supports_completion=False,
        supports_streaming=False,
        supports_embeddings=False,
        max_context_length=4096,
        max_output_tokens=1,
        provider="cohere",
        model_family="rerank",
        tags=["reranking", "retrieval", "multilingual"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.05,
            tokens_per_second=100.0,
            min_delay=0.005,
            max_delay=0.01,
        ),
        custom_metadata={
            "supports_reranking": True,
        },
    )

    models.append(
        ModelDefinition(
            model_id="rerank-v3.5",
            created=1717200000,
            owned_by="cohere",
            capabilities=rerank_caps,
            display_name="Rerank v3.5",
            description="Reranking model for improving search relevance, supports multilingual queries.",
            version="3.5",
            custom_fields={
                "pricing": {
                    "per_1000_searches": 2.0,
                },
                "reranking": True,
            },
        ))

    return models


# Export the models list
COHERE_MODELS = _get_cohere_models()


def get_cohere_models() -> list[ModelDefinition]:
    """
    Get all Cohere models.

    Returns:
        List of Cohere ModelDefinition instances
    """
    return COHERE_MODELS.copy()
