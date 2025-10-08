"""
Google AI Model Catalog

Complete catalog of Google AI models including Gemini 2.5 family, Gemma models,
and other Google AI offerings with accurate pricing and capabilities.

Updated: October 2025
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import CAPABILITY_PRESETS, LatencyProfile, ModelCapabilities
from ..definition import ModelDefinition


def _get_google_models() -> list[ModelDefinition]:
    """
    Get all Google AI model definitions.

    Returns:
        List of Google ModelDefinition instances
    """
    models = []

    # Gemini 2.5 Pro (Most advanced - March 2025)
    gemini_25_pro_caps = CAPABILITY_PRESETS["reasoning"].clone(
        supports_vision=True,
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        max_context_length=2_000_000,  # 2M tokens!
        max_output_tokens=8192,
        parameter_count=None,  # Not disclosed
        provider="google",
        model_family="gemini-2.5",
        tags=[
            "reasoning",
            "vision",
            "audio",
            "multimodal",
            "latest",
            "flagship"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.55,
            tokens_per_second=38.0,
            min_delay=0.024,
            max_delay=0.033,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gemini-2.5-pro",
            created=1741132800,  # 2025-03-01
            owned_by="google",
            capabilities=gemini_25_pro_caps,
            display_name="Gemini 2.5 Pro",
            description="Most advanced Gemini with 2M context window, built-in thinking, and strong reasoning/coding capabilities.",
            version="2.5-pro",
            custom_fields={
                "pricing": {
                    "input_per_million": 1.25,  # <200K context
                    "output_per_million": 5.0,
                    "long_context_input_per_million": 2.50,  # >200K context
                    "long_context_output_per_million": 10.0,
                },
            },
        )
    )

    # Gemini 2.5 Flash (Fast and efficient - September 2024/2025)
    gemini_25_flash_caps = CAPABILITY_PRESETS["vision"].clone(
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        supports_parallel_tool_calls=True,
        max_context_length=1_000_000,  # 1M tokens
        max_output_tokens=8192,
        parameter_count=None,
        provider="google",
        model_family="gemini-2.5",
        tags=["chat", "vision", "audio", "multimodal", "efficient", "fast"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.28,
            tokens_per_second=75.0,
            min_delay=0.012,
            max_delay=0.017,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gemini-2.5-flash",
            created=1727654400,  # 2025-09-29 (approximate)
            owned_by="google",
            capabilities=gemini_25_flash_caps,
            display_name="Gemini 2.5 Flash",
            description="Fast multimodal model with thinking capabilities, 1M context window, and excellent price/performance.",
            version="2.5-flash",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.075,
                    "output_per_million": 0.30,
                },
            },
        )
    )

    # Gemini 2.5 Flash-Lite (Ultra-fast - September 2025)
    gemini_25_flash_lite_caps = CAPABILITY_PRESETS["chat"].clone(
        supports_vision=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        max_context_length=1_000_000,
        max_output_tokens=8192,
        parameter_count=None,
        provider="google",
        model_family="gemini-2.5",
        tags=["chat", "vision", "multimodal", "ultra-fast", "efficient"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.08,
            tokens_per_second=544.0,  # Extremely fast!
            min_delay=0.003,
            max_delay=0.006,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gemini-2.5-flash-lite",
            created=1727654400,
            owned_by="google",
            capabilities=gemini_25_flash_lite_caps,
            display_name="Gemini 2.5 Flash-Lite",
            description="Ultra-fast lightweight model with 544 tokens/second output speed and 1M context.",
            version="2.5-flash-lite",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.0375,
                    "output_per_million": 0.15,
                },
            },
        ))

    # Gemini 2.5 Flash Image (Specialized image generation)
    gemini_25_flash_image_caps = ModelCapabilities(
        supports_chat=False,
        supports_completion=False,
        supports_streaming=True,
        supports_embeddings=False,
        supports_vision=True,
        max_context_length=8192,
        max_output_tokens=1,  # Returns image
        parameter_count=None,
        provider="google",
        model_family="gemini-2.5",
        tags=["image-generation", "vision"],
        latency_profile=LatencyProfile(
            time_to_first_token=1.5,
            tokens_per_second=1.0,
            min_delay=1.0,
            max_delay=2.0,
        ),
        custom_metadata={
            "generates_images": True,
        },
    )

    models.append(
        ModelDefinition(
            model_id="gemini-2.5-flash-image",
            created=1727654400,
            owned_by="google",
            capabilities=gemini_25_flash_image_caps,
            display_name="Gemini 2.5 Flash Image",
            description="State-of-the-art image generation model. Priced per image (1290 output tokens per image).",
            version="2.5-flash-image",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.0,
                    "output_per_million": 30.0,  # $0.039 per image
                },
                "tokens_per_image": 1290,
            },
        )
    )

    # Gemini 2.0 Flash (Previous generation - still excellent)
    gemini_20_flash_caps = CAPABILITY_PRESETS["vision"].clone(
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        max_context_length=1_000_000,
        max_output_tokens=8192,
        parameter_count=None,
        provider="google",
        model_family="gemini-2.0",
        tags=["chat", "vision", "audio", "multimodal"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.30,
            tokens_per_second=72.0,
            min_delay=0.013,
            max_delay=0.018,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gemini-2.0-flash",
            created=1735689600,  # 2025-01-01
            owned_by="google",
            capabilities=gemini_20_flash_caps,
            display_name="Gemini 2.0 Flash",
            description="Previous generation fast multimodal model with 1M context. Consider upgrading to 2.5 Flash.",
            version="2.0-flash",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.10,
                    "output_per_million": 0.40,
                },
            },
        )
    )

    # Gemini 1.5 Pro (Legacy - February 2024)
    gemini_15_pro_caps = CAPABILITY_PRESETS["vision"].clone(
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        max_context_length=2_000_000,  # 2M tokens
        max_output_tokens=8192,
        parameter_count=None,
        provider="google",
        model_family="gemini-1.5",
        tags=["chat", "vision", "audio", "multimodal", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.65,
            tokens_per_second=34.0,
            min_delay=0.027,
            max_delay=0.036,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gemini-1.5-pro",
            created=1707782400,  # 2024-02-13
            owned_by="google",
            capabilities=gemini_15_pro_caps,
            display_name="Gemini 1.5 Pro (Legacy)",
            description="Legacy model with 2M context. Consider upgrading to Gemini 2.5 Pro for better performance.",
            version="1.5-pro",
            custom_fields={
                "pricing": {
                    "input_per_million": 1.25,
                    "output_per_million": 5.0,
                    "long_context_input_per_million": 2.50,
                    "long_context_output_per_million": 10.0,
                },
            },
        )
    )

    # Gemini 1.5 Flash (Legacy)
    gemini_15_flash_caps = CAPABILITY_PRESETS["vision"].clone(
        supports_audio_input=True,
        supports_function_calling=True,
        supports_tool_use=True,
        supports_json_mode=True,
        max_context_length=1_000_000,
        max_output_tokens=8192,
        parameter_count=None,
        provider="google",
        model_family="gemini-1.5",
        tags=["chat", "vision", "audio", "multimodal", "legacy"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.35,
            tokens_per_second=68.0,
            min_delay=0.014,
            max_delay=0.019,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gemini-1.5-flash",
            created=1715644800,  # 2024-05-14
            owned_by="google",
            capabilities=gemini_15_flash_caps,
            display_name="Gemini 1.5 Flash (Legacy)",
            description="Legacy fast model. Consider upgrading to Gemini 2.5 Flash for better performance.",
            version="1.5-flash",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.075,
                    "output_per_million": 0.30,
                },
            },
        )
    )

    # Gemma 3n E4B (Ultra-efficient open model)
    gemma_3n_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=8192,
        max_output_tokens=4096,
        parameter_count=4_000_000_000,
        provider="google",
        model_family="gemma",
        tags=["chat", "efficient", "edge", "open-source"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.06,
            tokens_per_second=250.0,
            min_delay=0.003,
            max_delay=0.005,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="gemma-3n-e4b",
            created=1727740800,  # 2025-10-01 (approximate)
            owned_by="google",
            capabilities=gemma_3n_caps,
            display_name="Gemma 3n E4B",
            description="Ultra-efficient 4B open model optimized for edge deployment. Most affordable model available.",
            version="3n",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.03,
                    "output_per_million": 0.03,
                },
                "license": "Apache 2.0",
            },
        )
    )

    # PaLM 2 (Legacy - maintained for compatibility)
    palm2_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=8192,
        max_output_tokens=8192,
        supports_function_calling=False,
        parameter_count=None,
        provider="google",
        model_family="palm",
        tags=["chat", "legacy", "deprecated"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.8,
            tokens_per_second=30.0,
            min_delay=0.03,
            max_delay=0.04,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="text-bison@002",
            created=1683158400,  # 2023-05-04
            owned_by="google",
            capabilities=palm2_caps,
            display_name="PaLM 2 (text-bison) - Legacy",
            description="Legacy PaLM 2 model. Strongly recommend upgrading to Gemini 2.5 Flash.",
            version="002",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.50,
                    "output_per_million": 0.50,
                },
                "deprecated": True,
            },
        )
    )

    return models


# Export the models list
GOOGLE_MODELS = _get_google_models()


def get_google_models() -> list[ModelDefinition]:
    """
    Get all Google AI models.

    Returns:
        List of Google ModelDefinition instances
    """
    return GOOGLE_MODELS.copy()
