"""
FakeAI Model Registry Catalog

Pre-defined model catalogs organized by provider.
Includes OpenAI, Anthropic, Meta, Mistral, DeepSeek, and NVIDIA models.
"""

#  SPDX-License-Identifier: Apache-2.0

from .anthropic import ANTHROPIC_MODELS, get_anthropic_models
from .deepseek import DEEPSEEK_MODELS, get_deepseek_models
from .meta import META_MODELS, get_meta_models
from .mistral import MISTRAL_MODELS, get_mistral_models
from .nvidia import NVIDIA_MODELS, get_nvidia_models

# Import provider catalogs
from .openai import OPENAI_MODELS, get_openai_models

# Import registry loader functions
from .registry_loader import (
    PROVIDER_CATALOGS,
    ProviderName,
    create_default_registry,
    find_models_by_capability,
    get_provider_models,
    get_provider_stats,
    list_all_model_ids,
    load_all_models,
    load_provider_models,
)

__all__ = [
    # Provider model lists
    "OPENAI_MODELS",
    "ANTHROPIC_MODELS",
    "META_MODELS",
    "MISTRAL_MODELS",
    "DEEPSEEK_MODELS",
    "NVIDIA_MODELS",
    # Provider getter functions
    "get_openai_models",
    "get_anthropic_models",
    "get_meta_models",
    "get_mistral_models",
    "get_deepseek_models",
    "get_nvidia_models",
    # Registry loader
    "ProviderName",
    "PROVIDER_CATALOGS",
    "get_provider_models",
    "load_provider_models",
    "load_all_models",
    "create_default_registry",
    "get_provider_stats",
    "list_all_model_ids",
    "find_models_by_capability",
]
