"""
Generation configuration module.

This module provides response generation configuration options.
"""

#  SPDX-License-Identifier: Apache-2.0

from pydantic import Field, field_validator

from .base import ModuleConfig


class GenerationConfig(ModuleConfig):
    """Response generation configuration settings."""

    # LLM generation settings
    use_llm_generation: bool = Field(
        default=False,
        description="Use lightweight LLM for text generation (requires transformers, torch).",
    )
    llm_model_name: str = Field(
        default="distilgpt2",
        description="Model name for LLM generation (distilgpt2, gpt2, gpt2-medium, etc.).",
    )
    llm_use_gpu: bool = Field(
        default=True,
        description="Use GPU for LLM generation if available.",
    )

    # Semantic embedding settings
    use_semantic_embeddings: bool = Field(
        default=False,
        description="Use semantic embeddings via sentence-transformers (requires installation).",
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for semantic embeddings.",
    )
    embedding_use_gpu: bool = Field(
        default=True,
        description="Use GPU for embedding generation if available.",
    )

    # Image generation settings
    generate_actual_images: bool = Field(
        default=True,
        description="Generate actual images instead of fake URLs.",
    )

    # Response timing settings
    response_delay: float = Field(
        default=0.5,
        description="Base delay for responses in seconds.",
    )
    random_delay: bool = Field(
        default=True,
        description="Add random variation to response delays.",
    )
    max_variance: float = Field(
        default=0.3,
        description="Maximum variance for random delays (as a factor).",
    )

    # Latency simulation settings (TTFT and ITL)
    ttft_ms: float = Field(
        default=20.0,
        ge=0.0,
        description="Time to first token in milliseconds (default: 20ms).",
    )
    ttft_variance_percent: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Variance/jitter for TTFT as percentage (default: 10%).",
    )
    itl_ms: float = Field(
        default=5.0,
        ge=0.0,
        description="Inter-token latency in milliseconds (default: 5ms).",
    )
    itl_variance_percent: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Variance/jitter for ITL as percentage (default: 10%).",
    )

    @field_validator("response_delay")
    @classmethod
    def validate_response_delay(cls, v: float) -> float:
        """Validate response delay."""
        if v < 0:
            raise ValueError("Response delay cannot be negative")
        return v

    @field_validator("max_variance")
    @classmethod
    def validate_max_variance(cls, v: float) -> float:
        """Validate max variance."""
        if v < 0:
            raise ValueError("Max variance cannot be negative")
        return v

    @field_validator("embedding_model")
    @classmethod
    def validate_embedding_model(cls, v: str) -> str:
        """Validate embedding model name."""
        valid_models = {
            "all-MiniLM-L6-v2",
            "all-mpnet-base-v2",
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
        }
        if v not in valid_models:
            # Allow custom models, just log a warning
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Using custom embedding model '{v}'. "
                f"Recommended models: {', '.join(sorted(valid_models))}"
            )
        return v
