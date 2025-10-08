"""
DeepSeek Model Catalog

Complete catalog of DeepSeek models including V3.1 (hybrid), V3 (MoE), R1 (reasoning),
and distilled variants with accurate pricing and capabilities.

Updated: October 2025
"""

#  SPDX-License-Identifier: Apache-2.0

from ..capabilities import (
    CAPABILITY_PRESETS,
    LatencyProfile,
    MoEConfig,
)
from ..definition import ModelDefinition


def _get_deepseek_models() -> list[ModelDefinition]:
    """
    Get all DeepSeek model definitions.

    Returns:
        List of DeepSeek ModelDefinition instances
    """
    models = []

    # DeepSeek V3.1 (671B MoE hybrid - Latest, August 2025)
    deepseek_v31_caps = CAPABILITY_PRESETS["reasoning"].clone(
        max_context_length=128000,
        max_output_tokens=8192,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=671_000_000_000,  # 671B total
            active_params=37_000_000_000,  # 37B active per forward pass
            num_experts=256,  # 256 expert modules
            experts_per_token=8,  # 8 experts activated per token
        ),
        parameter_count=671_000_000_000,
        provider="deepseek",
        model_family="deepseek-v3.1",
        tags=[
            "chat",
            "reasoning",
            "moe",
            "large",
            "flagship",
            "hybrid",
            "latest"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.68,
            tokens_per_second=34.0,
            min_delay=0.026,
            max_delay=0.036,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="deepseek-v3.1",
            created=1722470400,  # 2025-08-01
            owned_by="deepseek",
            capabilities=deepseek_v31_caps,
            display_name="DeepSeek V3.1",
            description="Latest hybrid 671B MoE model (37B active). Combines V3 speed with R1 reasoning via switchable thinking modes.",
            version="3.1",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.14,
                    "output_per_million": 0.28,
                },
                "license": "MIT",
                "hybrid_thinking": True,
            },
        )
    )

    # DeepSeek V3 (671B MoE flagship)
    deepseek_v3_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=8192,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=671_000_000_000,
            active_params=37_000_000_000,
            num_experts=256,
            experts_per_token=8,
        ),
        parameter_count=671_000_000_000,
        provider="deepseek",
        model_family="deepseek-v3",
        tags=["chat", "moe", "large"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.7,
            tokens_per_second=33.0,
            min_delay=0.028,
            max_delay=0.038,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="deepseek-v3",
            created=1704067200,  # 2024-01-01
            owned_by="deepseek",
            capabilities=deepseek_v3_caps,
            display_name="DeepSeek V3",
            description="Massive 671B MoE model with 256 experts (37B active). Consider upgrading to V3.1.",
            version="3.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.27,
                    "output_per_million": 1.10,
                },
                "license": "DeepSeek License",
            },
        )
    )

    # DeepSeek-R1 (Reasoning model - January 2025)
    deepseek_r1_caps = CAPABILITY_PRESETS["reasoning"].clone(
        max_context_length=200000,
        max_output_tokens=100000,
        supports_vision=False,
        supports_audio_input=False,
        supports_function_calling=False,
        supports_tool_use=False,
        supports_json_mode=True,
        is_moe=True,
        moe_config=MoEConfig(
            total_params=671_000_000_000,
            active_params=37_000_000_000,
            num_experts=256,
            experts_per_token=8,
        ),
        parameter_count=671_000_000_000,
        provider="deepseek",
        model_family="deepseek-r1",
        tags=["reasoning", "moe", "large"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.7,
            tokens_per_second=33.0,
            min_delay=0.028,
            max_delay=0.038,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="deepseek-ai/DeepSeek-R1",
            created=1736640000,  # 2025-01-12
            owned_by="deepseek",
            capabilities=deepseek_r1_caps,
            display_name="DeepSeek-R1",
            description="Reasoning 671B MoE model with 200K context, 100K output. Consider V3.1 for better value.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.55,
                    "output_per_million": 2.19,
                },
                "license": "MIT",
            },
        )
    )

    # DeepSeek-R1-0528 (Updated reasoning model - May 2025)
    deepseek_r1_0528_caps = deepseek_r1_caps.clone(
        tags=["reasoning", "moe", "large", "updated"],
    )

    models.append(
        ModelDefinition(
            model_id="deepseek-ai/DeepSeek-R1-0528",
            created=1748390400,  # 2025-05-28
            owned_by="deepseek",
            capabilities=deepseek_r1_0528_caps,
            display_name="DeepSeek-R1-0528",
            description="Upgraded R1 reasoning model. Consider V3.1 for hybrid thinking capabilities.",
            version="1.0-0528",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.55,
                    "output_per_million": 2.19,
                },
                "license": "MIT",
            },
        )
    )

    # DeepSeek-R1-Distill-Qwen-32B (Efficient distilled reasoning)
    deepseek_r1_distill_32b_caps = CAPABILITY_PRESETS["reasoning"].clone(
        max_context_length=128000,
        max_output_tokens=65536,
        supports_vision=False,
        supports_audio_input=False,
        supports_function_calling=False,
        supports_tool_use=False,
        supports_json_mode=True,
        parameter_count=32_000_000_000,
        provider="deepseek",
        model_family="deepseek-r1-distill",
        tags=["reasoning", "efficient", "distilled"],
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
            created=1736640000,
            owned_by="deepseek",
            capabilities=deepseek_r1_distill_32b_caps,
            display_name="DeepSeek-R1-Distill-Qwen-32B",
            description="Efficient 32B distilled reasoning model. Best price/performance for reasoning tasks.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.14,
                    "output_per_million": 0.28,
                },
                "license": "MIT",
            },
        ))

    # DeepSeek-R1-Distill-Llama-70B (Larger distilled reasoning)
    deepseek_r1_distill_70b_caps = CAPABILITY_PRESETS["reasoning"].clone(
        max_context_length=128000,
        max_output_tokens=65536,
        supports_vision=False,
        supports_audio_input=False,
        supports_function_calling=False,
        supports_tool_use=False,
        supports_json_mode=True,
        parameter_count=70_000_000_000,
        provider="deepseek",
        model_family="deepseek-r1-distill",
        tags=["reasoning", "balanced", "distilled"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.5,
            tokens_per_second=43.0,
            min_delay=0.021,
            max_delay=0.028,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            created=1736640000,
            owned_by="deepseek",
            capabilities=deepseek_r1_distill_70b_caps,
            display_name="DeepSeek-R1-Distill-Llama-70B",
            description="Balanced 70B distilled reasoning model.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.27,
                    "output_per_million": 1.10,
                },
                "license": "MIT",
            },
        )
    )

    # DeepSeek Coder (Code-specialized model)
    deepseek_coder_caps = CAPABILITY_PRESETS["chat"].clone(
        max_context_length=128000,
        max_output_tokens=4096,
        supports_json_mode=True,
        supports_function_calling=True,
        supports_tool_use=True,
        parameter_count=33_000_000_000,
        provider="deepseek",
        model_family="deepseek-coder",
        tags=["chat", "code", "specialized"],
        latency_profile=LatencyProfile(
            time_to_first_token=0.35,
            tokens_per_second=60.0,
            min_delay=0.015,
            max_delay=0.021,
        ),
    )

    models.append(
        ModelDefinition(
            model_id="deepseek-coder",
            created=1698969600,  # 2023-11-03
            owned_by="deepseek",
            capabilities=deepseek_coder_caps,
            display_name="DeepSeek Coder",
            description="Code-specialized 33B model optimized for programming tasks.",
            version="1.0",
            custom_fields={
                "pricing": {
                    "input_per_million": 0.14,
                    "output_per_million": 0.28,
                },
                "license": "DeepSeek License",
            },
        )
    )

    return models


# Export the models list
DEEPSEEK_MODELS = _get_deepseek_models()


def get_deepseek_models() -> list[ModelDefinition]:
    """
    Get all DeepSeek models.

    Returns:
        List of DeepSeek ModelDefinition instances
    """
    return DEEPSEEK_MODELS.copy()
