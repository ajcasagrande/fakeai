#!/usr/bin/env python3
"""
Example: Semantic Embeddings with FakeAI

Demonstrates how to use semantic embeddings with sentence transformers
instead of random embeddings.

Requirements:
    pip install sentence-transformers

Usage:
    # Start server with semantic embeddings
    FAKEAI_USE_SEMANTIC_EMBEDDINGS=true fakeai server

    # Or in code:
    python examples/semantic_embeddings_example.py
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio

import numpy as np

from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import EmbeddingRequest


async def main():
    """Demonstrate semantic embeddings."""
    print("=== Semantic Embeddings Example ===\n")

    # Create service with semantic embeddings enabled
    print("1. Creating FakeAI service with semantic embeddings...")
    config = AppConfig(
        use_semantic_embeddings=True,
        embedding_model="all-MiniLM-L6-v2",
        embedding_use_gpu=False,
        response_delay=0.0,
    )
    service = FakeAIService(config)

    # Check if semantic embeddings are available
    if service.semantic_embeddings and service.semantic_embeddings.is_available():
        print("   ✓ Semantic embeddings enabled")
        info = service.semantic_embeddings.get_model_info()
        print(f"   Model: {info['model_name']}")
        print(f"   Dimensions: {info['native_dimensions']}")
        print(f"   Device: {info['device']}\n")
    else:
        print("   ⚠ Semantic embeddings not available, using fallback\n")

    # Example 1: Single embedding
    print("2. Generating single embedding...")
    request1 = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Machine learning is fascinating.",
    )
    response1 = await service.create_embedding(request1)
    emb1 = response1.data[0].embedding
    print(f"   Text: {request1.input}")
    print(f"   Dimensions: {len(emb1)}")
    print(f"   L2 norm: {np.linalg.norm(emb1):.6f}")
    print(f"   First 5 values: {emb1[:5]}\n")

    # Example 2: Batch embeddings
    print("3. Generating batch embeddings...")
    texts = [
        "The cat sat on the mat.",
        "A cat is sitting on the mat.",
        "Dogs are loyal companions.",
        "Quantum physics is complex.",
    ]
    request2 = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=texts,
    )
    response2 = await service.create_embedding(request2)
    embeddings = [data.embedding for data in response2.data]
    print(f"   Generated {len(embeddings)} embeddings")
    print(f"   Usage: {response2.usage.total_tokens} tokens\n")

    # Example 3: Semantic similarity
    print("4. Computing semantic similarity...")
    emb_cat1 = embeddings[0]
    emb_cat2 = embeddings[1]
    emb_dog = embeddings[2]
    emb_physics = embeddings[3]

    # Calculate similarities
    sim_cat_cat = float(np.dot(emb_cat1, emb_cat2))
    sim_cat_dog = float(np.dot(emb_cat1, emb_dog))
    sim_cat_physics = float(np.dot(emb_cat1, emb_physics))

    print(f"   Similarity (cat1 vs cat2):    {sim_cat_cat:.4f}")
    print(f"   Similarity (cat1 vs dog):     {sim_cat_dog:.4f}")
    print(f"   Similarity (cat1 vs physics): {sim_cat_physics:.4f}\n")

    # Example 4: Custom dimensions
    print("5. Custom dimension adjustment...")
    request3 = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Test with custom dimensions",
        dimensions=512,
    )
    response3 = await service.create_embedding(request3)
    emb3 = response3.data[0].embedding
    print(f"   Requested dimensions: 512")
    print(f"   Actual dimensions: {len(emb3)}")
    print(f"   L2 norm: {np.linalg.norm(emb3):.6f}\n")

    # Example 5: Compare with random embeddings
    print("6. Comparing semantic vs random embeddings...")
    config_random = AppConfig(
        use_semantic_embeddings=False,
        response_delay=0.0,
    )
    service_random = FakeAIService(config_random)

    request4 = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=texts[:2],
    )

    # Semantic embeddings
    response_semantic = await service.create_embedding(request4)
    emb_sem1 = response_semantic.data[0].embedding
    emb_sem2 = response_semantic.data[1].embedding
    sim_semantic = float(np.dot(emb_sem1, emb_sem2))

    # Random embeddings
    response_random = await service_random.create_embedding(request4)
    emb_rand1 = response_random.data[0].embedding
    emb_rand2 = response_random.data[1].embedding
    sim_random = float(np.dot(emb_rand1, emb_rand2))

    print(f"   Similar texts: '{texts[0]}' and '{texts[1]}'")
    print(f"   Semantic similarity: {sim_semantic:.4f}")
    print(f"   Random similarity:   {sim_random:.4f}")
    if service.semantic_embeddings and service.semantic_embeddings.is_available():
        print(f"   Difference: {abs(sim_semantic - sim_random):.4f}\n")
    else:
        print("   (Both using fallback, similar results expected)\n")

    print("=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
