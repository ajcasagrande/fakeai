"""
Embedding Service

This module provides the embedding generation service, supporting both
semantic embeddings (via sentence transformers) and random hash-based embeddings.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import logging
import random
import struct
from typing import Any

from fakeai.config import AppConfig
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    Embedding,
    EmbeddingRequest,
    EmbeddingResponse,
    Usage,
)
from fakeai.utils import (
    calculate_token_count,
    create_random_embedding,
    normalize_embedding,
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.

    Features:
    - Support for string or list[str] input
    - Custom dimensions (256-3072)
    - Semantic embeddings when enabled, fallback to random
    - Token tracking and usage metrics
    - Model validation and auto-creation
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        model_registry: Any = None,
    ):
        """
        Initialize the embedding service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracking singleton
            model_registry: Optional model registry for validation
        """
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.model_registry = model_registry

        # Optional semantic embeddings
        self.semantic_generator = None
        if config.use_semantic_embeddings:
            try:
                from fakeai.semantic_embeddings import get_semantic_embedding_generator

                self.semantic_generator = get_semantic_embedding_generator(
                    model_name=getattr(
                        config, "semantic_model_name", "all-MiniLM-L6-v2"
                    ),
                    use_gpu=getattr(config, "semantic_use_gpu", True),
                )
                if self.semantic_generator.is_available():
                    logger.info("Semantic embeddings enabled and available")
                else:
                    logger.warning(
                        "Semantic embeddings requested but not available, using random"
                    )
                    self.semantic_generator = None
            except Exception as e:
                logger.warning(
                    f"Failed to initialize semantic embeddings: {e}, using random"
                )
                self.semantic_generator = None

    async def create_embedding(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:
        """
        Create embeddings for input text(s).

        Args:
            request: Embedding request with model, input, and optional dimensions

        Returns:
            EmbeddingResponse with generated embeddings and usage stats

        Raises:
            ValueError: If input format is unsupported
        """
        # Convert input to a list of strings
        inputs = self._process_embedding_input(request.input)

        # Get dimensions (default 1536 for OpenAI text-embedding-ada-002)
        dimensions = request.dimensions or 1536

        # Validate dimensions range
        if dimensions < 1 or dimensions > 3072:
            raise ValueError(f"Dimensions must be between 1 and 3072, got {dimensions}")

        # Calculate token count
        total_tokens = sum(calculate_token_count(text) for text in inputs)

        # Simulate computational delay based on input size and dimensions
        delay = 0.01 * (total_tokens / 100) * (dimensions / 1000)
        await asyncio.sleep(delay + random.uniform(0.05, 0.2))

        # Generate embeddings (semantic or random)
        embeddings = await self._generate_embeddings(inputs, dimensions)

        # Convert to base64 if requested
        if request.encoding_format == "base64":
            embeddings = self._encode_embeddings_to_base64(embeddings)

        # Create response
        response = EmbeddingResponse(
            data=embeddings,
            model=request.model,
            usage=Usage(
                prompt_tokens=total_tokens,
                completion_tokens=0,
                total_tokens=total_tokens,
            ),
        )

        # Track token usage
        self.metrics_tracker.track_tokens("/v1/embeddings", total_tokens)

        return response

    async def _generate_embeddings(
        self,
        inputs: list[str],
        dimensions: int,
    ) -> list[Embedding]:
        """
        Generate embedding vectors for input texts.

        Args:
            inputs: List of text strings to embed
            dimensions: Target embedding dimensions

        Returns:
            List of Embedding objects
        """
        embeddings = []

        if self.semantic_generator and self.semantic_generator.is_available():
            # Use semantic embeddings
            try:
                embedding_vectors = self.semantic_generator.encode_batch(
                    inputs,
                    dimensions=dimensions,
                )
                for i, embedding_vector in enumerate(embedding_vectors):
                    embeddings.append(
                        Embedding(
                            embedding=embedding_vector,
                            index=i,
                        )
                    )
                return embeddings
            except Exception as e:
                logger.warning(
                    f"Semantic embedding generation failed: {e}, falling back to random"
                )

        # Use random embeddings (fallback or default)
        for i, text in enumerate(inputs):
            embedding_vector = create_random_embedding(text, dimensions)
            embedding_vector = normalize_embedding(embedding_vector)
            embeddings.append(
                Embedding(
                    embedding=embedding_vector,
                    index=i,
                )
            )

        return embeddings

    def _encode_embeddings_to_base64(self, embeddings: list[Embedding]) -> list[Embedding]:
        """
        Convert embedding vectors to base64 encoded strings.

        Args:
            embeddings: List of Embedding objects with float vectors

        Returns:
            List of Embedding objects with base64 encoded vectors
        """
        encoded_embeddings = []
        for embedding in embeddings:
            # Convert float list to bytes using struct
            float_bytes = struct.pack(f"{len(embedding.embedding)}f", *embedding.embedding)
            # Encode to base64
            base64_str = base64.b64encode(float_bytes).decode("utf-8")
            # Create new embedding with base64 string
            encoded_embeddings.append(
                Embedding(
                    embedding=base64_str,
                    index=embedding.index,
                )
            )
        return encoded_embeddings

    def _process_embedding_input(
        self,
        input_data: str | list[str] | list[int] | list[list[int]],
    ) -> list[str]:
        """
        Process the embedding input into a list of strings.

        Args:
            input_data: Input in various formats (string, list of strings, or token IDs)

        Returns:
            List of text strings to embed

        Raises:
            ValueError: If input format is unsupported
        """
        if isinstance(input_data, str):
            return [input_data]

        if isinstance(input_data, list):
            # List of strings
            if all(isinstance(item, str) for item in input_data):
                return input_data

            # List of token IDs (single sequence)
            if all(isinstance(item, int) for item in input_data):
                # Use placeholder for token IDs
                return [f"[Token IDs input with {len(input_data)} tokens]"]

            # List of token ID lists (multiple sequences)
            if all(
                isinstance(item, list) and all(isinstance(i, int) for i in item)
                for item in input_data
            ):
                # Convert each token ID list to a placeholder string
                return [
                    f"[Token IDs input with {len(ids)} tokens]" for ids in input_data
                ]

        raise ValueError(f"Unsupported input format for embeddings: {type(input_data)}")
