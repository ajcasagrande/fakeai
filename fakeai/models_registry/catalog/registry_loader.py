"""
Registry Loader

Utilities for loading model catalogs into the registry.
Provides functions to create pre-configured registries and load models by provider.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Literal

from ..definition import ModelDefinition
from ..registry import ModelRegistry
from .anthropic import get_anthropic_models
from .deepseek import get_deepseek_models
from .meta import get_meta_models
from .mistral import get_mistral_models
from .nvidia import get_nvidia_models

# Import all provider catalogs
from .openai import get_openai_models

# Provider type
ProviderName = Literal[
    "openai", "anthropic", "meta", "mistral", "deepseek", "nvidia", "all"
]


# Provider catalog mapping
PROVIDER_CATALOGS = {
    "openai": get_openai_models,
    "anthropic": get_anthropic_models,
    "meta": get_meta_models,
    "mistral": get_mistral_models,
    "deepseek": get_deepseek_models,
    "nvidia": get_nvidia_models,
}


def get_provider_models(provider: ProviderName) -> list[ModelDefinition]:
    """
    Get models from a specific provider catalog without loading into registry.

    Args:
        provider: Provider name (openai, anthropic, meta, mistral, deepseek, nvidia, all)

    Returns:
        List of ModelDefinition instances

    Raises:
        ValueError: If provider is invalid

    Example:
        >>> models = get_provider_models("openai")
        >>> print(f"Found {len(models)} OpenAI models")
    """
    if provider == "all":
        # Return all models from all providers
        all_models = []
        for catalog_func in PROVIDER_CATALOGS.values():
            all_models.extend(catalog_func())
        return all_models

    if provider not in PROVIDER_CATALOGS:
        available = ", ".join(list(PROVIDER_CATALOGS.keys()) + ["all"])
        raise ValueError(f"Invalid provider '{provider}'. Available: {available}")

    return PROVIDER_CATALOGS[provider]()


def load_provider_models(
    registry: ModelRegistry,
    providers: ProviderName | list[ProviderName],
) -> int:
    """
    Load models from one or more providers into the registry.

    Args:
        registry: ModelRegistry instance to load into
        providers: Provider name or list of provider names

    Returns:
        Number of models loaded

    Example:
        >>> registry = ModelRegistry()
        >>> count = load_provider_models(registry, "openai")
        >>> print(f"Loaded {count} OpenAI models")

        >>> count = load_provider_models(registry, ["openai", "meta"])
        >>> print(f"Loaded {count} models from multiple providers")
    """
    if isinstance(providers, str):
        providers = [providers]

    total_loaded = 0

    for provider in providers:
        if provider == "all":
            # Load all providers
            for provider_name in PROVIDER_CATALOGS.keys():
                models = get_provider_models(provider_name)
                for model in models:
                    try:
                        registry[model.model_id] = model
                        total_loaded += 1
                    except ValueError:
                        # Skip if already exists
                        pass
        else:
            models = get_provider_models(provider)
            for model in models:
                try:
                    registry[model.model_id] = model
                    total_loaded += 1
                except ValueError:
                    # Skip if already exists
                    pass

    return total_loaded


def load_all_models(registry: ModelRegistry) -> int:
    """
    Load all models from all providers into the registry.

    Args:
        registry: ModelRegistry instance to load into

    Returns:
        Number of models loaded

    Example:
        >>> registry = ModelRegistry()
        >>> count = load_all_models(registry)
        >>> print(f"Loaded {count} models from all providers")
    """
    return load_provider_models(registry, "all")


def create_default_registry(
    providers: ProviderName | list[ProviderName] = "all",
) -> ModelRegistry:
    """
    Create a ModelRegistry pre-loaded with specified provider models.

    Args:
        providers: Provider(s) to load (default: "all")

    Returns:
        ModelRegistry instance with loaded models

    Example:
        >>> # Load all models
        >>> registry = create_default_registry()

        >>> # Load only OpenAI models
        >>> registry = create_default_registry(providers="openai")

        >>> # Load multiple providers
        >>> registry = create_default_registry(providers=["openai", "meta"])
    """
    registry = ModelRegistry()
    load_provider_models(registry, providers)
    return registry


def get_provider_stats() -> dict[str, int]:
    """
    Get statistics about available models per provider.

    Returns:
        Dictionary mapping provider names to model counts

    Example:
        >>> stats = get_provider_stats()
        >>> for provider, count in stats.items():
        ...     print(f"{provider}: {count} models")
    """
    stats = {}
    for provider_name, catalog_func in PROVIDER_CATALOGS.items():
        models = catalog_func()
        stats[provider_name] = len(models)

    # Add total
    stats["total"] = sum(stats.values())

    return stats


def list_all_model_ids() -> list[str]:
    """
    Get all model IDs from all providers.

    Returns:
        List of all model IDs across all providers

    Example:
        >>> all_ids = list_all_model_ids()
        >>> print(f"Total models: {len(all_ids)}")
        >>> print("Sample:", all_ids[:5])
    """
    all_models = get_provider_models("all")
    return [model.model_id for model in all_models]


def find_models_by_capability(capability: str) -> list[ModelDefinition]:
    """
    Find all models that support a specific capability across all providers.

    Args:
        capability: Capability name (chat, vision, reasoning, etc.)

    Returns:
        List of ModelDefinition instances with the capability

    Example:
        >>> reasoning_models = find_models_by_capability("reasoning")
        >>> for model in reasoning_models:
        ...     print(f"{model.model_id}: {model.owned_by}")
    """
    all_models = get_provider_models("all")
    matching = []

    for model in all_models:
        if model.capabilities.has_capability(capability):
            matching.append(model)

    return matching


__all__ = [
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
