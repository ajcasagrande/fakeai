"""
FakeAI Model Registry

Centralized model management system with capabilities tracking,
thread-safe registry, auto-creation support, and intelligent discovery.
"""

from .capabilities import (
    CAPABILITY_PRESETS,
    LATENCY_PRESETS,
    LatencyProfile,
    ModelCapabilities,
    MoEConfig,
)
from .definition import ModelDefinition, create_model_definition
from .discovery import (
    FineTunedModelInfo,
    MatchResult,
    ModelCharacteristics,
    ModelMatcher,
    fuzzy_match_model,
    infer_model_characteristics,
    normalize_model_id,
    parse_fine_tuned_model,
    suggest_similar_models,
)
from .registry import ModelRegistry

__all__ = [
    # Capabilities
    "ModelCapabilities",
    "LatencyProfile",
    "MoEConfig",
    "CAPABILITY_PRESETS",
    "LATENCY_PRESETS",
    # Definition
    "ModelDefinition",
    "create_model_definition",
    # Registry
    "ModelRegistry",
    # Discovery - Functions
    "fuzzy_match_model",
    "normalize_model_id",
    "infer_model_characteristics",
    "parse_fine_tuned_model",
    "suggest_similar_models",
    # Discovery - Classes
    "ModelMatcher",
    "ModelCharacteristics",
    "MatchResult",
    "FineTunedModelInfo",
]
