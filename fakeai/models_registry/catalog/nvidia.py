"""
NVIDIA Model Catalog

Complete catalog of NVIDIA NIM and Cosmos models including vision (video),
NeMo models, and reranking with accurate capabilities.
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import CAPABILITY_PRESETS, LatencyProfile, ModelCapabilities
from ..definition import ModelDefinition, create_model_definition


def _get_nvidia_models() -> list[ModelDefinition]:
    """
    Get all NVIDIA model definitions.

    Returns:
        List of NVIDIA ModelDefinition instances
    """
    models = []

    # NVIDIA Cosmos Vision (Video understanding)
    cosmos_vision_caps = CAPABILITY_PRESETS["vision"].clone(
        supports_video=True,
        supports_audio_input=True,
        max_context_length=32768,
        max_output_tokens=4096,
        parameter_count=None,  # Not disclosed
        provider="nvidia",
        model_family="cosmos",
        tags=["chat", "vision", "video", "multimodal"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.6,
            tokens_per_second=35.0,
            min_delay=0.025,
            max_delay=0.035,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="nvidia/cosmos-vision",
            created=1704067200,  # 2024-01-01
            owned_by="nvidia",
            capabilities=cosmos_vision_caps,
            display_name="NVIDIA Cosmos Vision",
            description="Multimodal model with video understanding and analysis capabilities.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 1.0,
                    "output_per_million": 3.0,
                },
                "video_support": True,
            },
        )
    )

    # NVIDIA NeMo Megatron (Llama 3.1 70B optimized)
    nemo_70b_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        parameter_count=70_000_000_000,
        provider="nvidia",
        model_family="nemo",
        tags=["chat", "optimized", "nim"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.28,
            tokens_per_second=71.0,
            min_delay=0.012,
            max_delay=0.017,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="nvidia/llama-3.1-nemotron-70b-instruct",
            created=1725840000,  # 2024-09-09
            owned_by="nvidia",
            capabilities=nemo_70b_caps,
            display_name="Llama 3.1 NeMo Megatron 70B",
            description="NVIDIA-optimized Llama 3.1 70B with improved performance and efficiency.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.88,
                    "output_per_million": 0.88,
                },
                "nim_optimized": True,
            },
        )
    )

    # NVIDIA Reranking Model
    rerank_caps = ModelCapabilities(
        supports_chat=False,
        supports_completion=False,
        supports_streaming=False,
        supports_embeddings=False,
        max_context_length=8192,
        max_output_tokens=1,
        provider="nvidia",
        model_family="reranking",
        tags=["reranking", "retrieval"],
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
            model_id="nvidia/nv-rerank-qa-mistral-4b",
            created=1704067200,
            owned_by="nvidia",
            capabilities=rerank_caps,
            display_name="NVIDIA Rerank QA Mistral 4B",
            description="Reranking model for question-answering retrieval tasks.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.02,
                    "output_per_million": 0.0,
                },
                "reranking": True,
            },
        )
    )

    return models


# Export the models list
NVIDIA_MODELS = _get_nvidia_models()


def get_nvidia_models() -> list[ModelDefinition]:
    """
    Get all NVIDIA models.

    Returns:
        List of NVIDIA ModelDefinition instances
    """
    return NVIDIA_MODELS.copy()
