"""
Semantic Embeddings Module

This module provides semantic embedding generation using sentence transformers.
Falls back to random embeddings if sentence-transformers is not available.
"""

#  SPDX-License-Identifier: Apache-2.0

import hashlib
import logging
from functools import lru_cache
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.info("sentence-transformers not available, using random embeddings")


class SemanticEmbeddingGenerator:
    """
    Generates semantic embeddings using sentence transformers.

    Features:
    - Multiple model support (all-MiniLM-L6-v2, all-mpnet-base-v2)
    - GPU acceleration (CUDA)
    - Batch encoding for efficiency
    - LRU caching for identical texts
    - Dimension adjustment (padding/truncation)
    - L2 normalization (OpenAI compatible)
    - Graceful fallback to random embeddings
    """

    # Model configurations
    MODEL_CONFIGS = {
        "all-MiniLM-L6-v2": {
            "dimensions": 384,
            "max_seq_length": 256,
            "description": "Fast and efficient (22M params)",
        },
        "all-mpnet-base-v2": {
            "dimensions": 768,
            "max_seq_length": 384,
            "description": "High quality (110M params)",
        },
        "sentence-transformers/all-MiniLM-L6-v2": {
            "dimensions": 384,
            "max_seq_length": 256,
            "description": "Fast and efficient (22M params)",
        },
        "sentence-transformers/all-mpnet-base-v2": {
            "dimensions": 768,
            "max_seq_length": 384,
            "description": "High quality (110M params)",
        },
    }

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        use_gpu: bool = True,
        cache_size: int = 512,
    ):
        """
        Initialize semantic embedding generator.

        Args:
            model_name: Name of the sentence transformer model
            use_gpu: Whether to use GPU if available
            cache_size: Size of LRU cache for embeddings
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.cache_size = cache_size
        self._model: Any | None = None
        self._model_loaded = False
        self._load_failed = False

        # Get model config
        self.model_config = self.MODEL_CONFIGS.get(
            model_name,
            {"dimensions": 384, "max_seq_length": 256, "description": "Unknown model"},
        )
        self.native_dimensions = self.model_config["dimensions"]

        logger.info(
            f"SemanticEmbeddingGenerator initialized with model={model_name}, "
            f"use_gpu={use_gpu}, native_dims={self.native_dimensions}"
        )

    def _load_model(self) -> bool:
        """
        Lazy load the sentence transformer model.

        Returns:
            True if model loaded successfully, False otherwise
        """
        if self._model_loaded:
            return True

        if self._load_failed:
            return False

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning(
                "sentence-transformers not available, using random embeddings"
            )
            self._load_failed = True
            return False

        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")

            # Determine device
            device = None
            if self.use_gpu:
                try:
                    import torch

                    if torch.cuda.is_available():
                        device = "cuda"
                        logger.info("Using GPU (CUDA) for embeddings")
                    else:
                        device = "cpu"
                        logger.info("CUDA not available, using CPU")
                except ImportError:
                    device = "cpu"
                    logger.info("PyTorch not available, using CPU")
            else:
                device = "cpu"
                logger.info("Using CPU for embeddings (GPU disabled)")

            # Load model
            self._model = SentenceTransformer(self.model_name, device=device)
            self._model_loaded = True

            logger.info(
                f"Model loaded successfully: {self.model_name} "
                f"(dims={self.native_dimensions}, device={device})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            self._load_failed = True
            return False

    def is_available(self) -> bool:
        """
        Check if semantic embeddings are available.

        Returns:
            True if sentence transformers can be used, False otherwise
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return False

        if self._load_failed:
            return False

        return self._load_model()

    @lru_cache(maxsize=512)
    def _encode_cached(self, text: str, dimensions: int | None) -> tuple[float, ...]:
        """
        Cached encoding for single text.

        Args:
            text: Text to encode
            dimensions: Target dimensions (None for native)

        Returns:
            Tuple of floats representing the embedding
        """
        # Generate embedding
        embedding = self._model.encode(
            text,
            normalize_embeddings=False,  # We'll normalize after dimension adjustment
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        # Adjust dimensions if needed
        if dimensions and dimensions != len(embedding):
            embedding = self._adjust_dimensions(embedding, dimensions)

        # L2 normalize
        embedding = self._normalize_l2(embedding)

        # Convert to tuple for caching
        return tuple(float(x) for x in embedding)

    def encode(
        self,
        texts: str | list[str],
        dimensions: int | None = None,
    ) -> list[float] | list[list[float]]:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text string or list of texts
            dimensions: Target dimensions (None for native dimensions)

        Returns:
            Single embedding or list of embeddings
        """
        # Handle single text
        if isinstance(texts, str):
            if not self.is_available():
                return self._fallback_embedding(texts, dimensions)

            embedding = list(self._encode_cached(texts, dimensions))
            return embedding

        # Handle list of texts
        if not self.is_available():
            return [self._fallback_embedding(text, dimensions) for text in texts]

        # Use batch encoding for efficiency
        return self.encode_batch(texts, dimensions)

    def encode_batch(
        self,
        texts: list[str],
        dimensions: int | None = None,
        batch_size: int = 32,
    ) -> list[list[float]]:
        """
        Batch encode multiple texts for efficiency.

        Args:
            texts: List of texts to encode
            dimensions: Target dimensions (None for native)
            batch_size: Batch size for encoding

        Returns:
            List of embeddings
        """
        if not self.is_available():
            return [self._fallback_embedding(text, dimensions) for text in texts]

        # Check cache first for all texts
        cached_results = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            try:
                # Try to get from cache
                cached = self._encode_cached(text, dimensions)
                cached_results.append((i, list(cached)))
            except Exception:
                # Not in cache, needs encoding
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Encode uncached texts in batch
        if uncached_texts:
            embeddings = self._model.encode(
                uncached_texts,
                normalize_embeddings=False,
                show_progress_bar=False,
                batch_size=batch_size,
                convert_to_numpy=True,
            )

            # Process each embedding
            for idx, embedding in zip(uncached_indices, embeddings):
                # Adjust dimensions if needed
                if dimensions and dimensions != len(embedding):
                    embedding = self._adjust_dimensions(embedding, dimensions)

                # L2 normalize
                embedding = self._normalize_l2(embedding)

                # Convert to list
                embedding_list = [float(x) for x in embedding]
                cached_results.append((idx, embedding_list))

                # Add to cache
                try:
                    self._encode_cached(texts[idx], dimensions)
                except Exception:
                    pass  # Cache miss is fine

        # Sort by original index and return
        cached_results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in cached_results]

    def get_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity (-1.0 to 1.0)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate dot product (cosine similarity for normalized vectors)
        similarity = float(np.dot(vec1, vec2))

        # Ensure it's in valid range
        similarity = max(-1.0, min(1.0, similarity))

        return similarity

    def _adjust_dimensions(
        self, embedding: np.ndarray, target_dimensions: int
    ) -> np.ndarray:
        """
        Adjust embedding dimensions by padding or truncation.

        Args:
            embedding: Original embedding vector
            target_dimensions: Target number of dimensions

        Returns:
            Adjusted embedding vector
        """
        current_dims = len(embedding)

        if current_dims == target_dimensions:
            return embedding

        if current_dims < target_dimensions:
            # Pad with zeros
            padding = np.zeros(target_dimensions - current_dims)
            return np.concatenate([embedding, padding])
        else:
            # Truncate
            return embedding[:target_dimensions]

    def _normalize_l2(self, embedding: np.ndarray) -> np.ndarray:
        """
        L2 normalize embedding to unit length.

        Args:
            embedding: Embedding vector to normalize

        Returns:
            Normalized embedding vector
        """
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding

    def _fallback_embedding(
        self, text: str, dimensions: int | None = None
    ) -> list[float]:
        """
        Generate random embedding as fallback.

        Args:
            text: Text to generate embedding for
            dimensions: Target dimensions

        Returns:
            Random embedding vector
        """
        target_dims = dimensions or self.native_dimensions

        # Use stable hash-based random generation
        text_hash = hashlib.sha256(text.encode()).digest()
        # Limit seed to 32-bit unsigned int range (0 to 2**32 - 1)
        seed = int.from_bytes(text_hash[:4], byteorder="big") % (2**32)
        rng = np.random.RandomState(seed)

        # Generate random embedding
        embedding = rng.randn(target_dims).astype(np.float32)

        # L2 normalize
        embedding = self._normalize_l2(embedding)

        return [float(x) for x in embedding]

    def get_model_info(self) -> dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "native_dimensions": self.native_dimensions,
            "max_seq_length": self.model_config.get("max_seq_length", 256),
            "description": self.model_config.get("description", "Unknown model"),
            "use_gpu": self.use_gpu,
            "available": self.is_available(),
            "loaded": self._model_loaded,
            "device": (
                getattr(self._model, "device", "unknown")
                if self._model
                else "not loaded"
            ),
        }


# Global instance (lazily initialized)
_global_generator: SemanticEmbeddingGenerator | None = None


def get_semantic_embedding_generator(
    model_name: str = "all-MiniLM-L6-v2",
    use_gpu: bool = True,
) -> SemanticEmbeddingGenerator:
    """
    Get or create global semantic embedding generator.

    Args:
        model_name: Name of the sentence transformer model
        use_gpu: Whether to use GPU if available

    Returns:
        SemanticEmbeddingGenerator instance
    """
    global _global_generator

    if _global_generator is None:
        _global_generator = SemanticEmbeddingGenerator(
            model_name=model_name,
            use_gpu=use_gpu,
        )

    return _global_generator


def reset_global_generator() -> None:
    """Reset the global generator (useful for testing)."""
    global _global_generator
    _global_generator = None
