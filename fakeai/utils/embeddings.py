"""
Embedding generation and normalization utilities.

This module provides functions for generating random embeddings with stable
hashing and normalizing embedding vectors using L2 normalization.
"""

#  SPDX-License-Identifier: Apache-2.0

import hashlib
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=512)
def create_random_embedding(text: str, dimensions: int) -> list[float]:
    """
    Create a random embedding vector with a stable hash based on the text.

    Args:
        text: The text to generate an embedding for
        dimensions: The number of dimensions for the embedding vector

    Returns:
        A list of floats representing the embedding vector

    Note:
        This function uses LRU caching to avoid recomputing embeddings for
        the same text/dimensions combination. Cache size increased to 512
        for better hit rates in production workloads.
    """
    # Create a stable seed from the text hash
    text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    np.random.seed(text_hash)

    # Generate a random embedding with the right distribution
    embedding = np.random.normal(0, 1, dimensions)

    # Reset the random seed to avoid affecting other random operations
    np.random.seed()

    return embedding.tolist()


def normalize_embedding(embedding: list[float]) -> list[float]:
    """
    Normalize an embedding vector to unit length (L2 normalization).

    Args:
        embedding: The embedding vector to normalize

    Returns:
        The normalized embedding vector
    """
    # Convert to numpy array for efficient operations
    vec = np.array(embedding)

    # Calculate the L2 norm (Euclidean norm)
    norm = np.linalg.norm(vec)

    # Normalize the vector
    if norm > 0:
        normalized = vec / norm
    else:
        normalized = vec

    return normalized.tolist()
