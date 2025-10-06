"""
Tests for semantic embeddings module.

Tests semantic embedding generation using sentence transformers,
dimension adjustment, L2 normalization, fallback behavior, and integration.
"""

#  SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest

from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import EmbeddingRequest
from fakeai.semantic_embeddings import (
    SemanticEmbeddingGenerator,
    get_semantic_embedding_generator,
    reset_global_generator,
)


class TestSemanticEmbeddingGenerator:
    """Test semantic embedding generator."""

    def test_basic_encoding(self):
        """Test basic text encoding."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Test single text
        text = "Hello, world!"
        embedding = generator.encode(text)

        # Check type and shape
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # Native dimensions for all-MiniLM-L6-v2
        assert all(isinstance(x, float) for x in embedding)

        # Check L2 normalization (should be close to 1.0)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5

    def test_batch_encoding(self):
        """Test batch text encoding."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Test multiple texts
        texts = [
            "Hello, world!",
            "Goodbye, world!",
            "Machine learning is fascinating.",
        ]
        embeddings = generator.encode_batch(texts)

        # Check type and shape
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) == 384 for emb in embeddings)

        # Check L2 normalization
        for embedding in embeddings:
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 1e-5

    def test_encode_with_list_input(self):
        """Test encoding with list of texts."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Test list input
        texts = ["First text", "Second text"]
        embeddings = generator.encode(texts)

        # Check type and shape
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        assert all(isinstance(emb, list) for emb in embeddings)

    def test_similarity_calculation(self):
        """Test cosine similarity calculation."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Create embeddings for similar and dissimilar texts
        similar_text1 = "The cat sat on the mat."
        similar_text2 = "A cat is sitting on the mat."
        dissimilar_text = "Quantum physics is complex."

        emb1 = generator.encode(similar_text1)
        emb2 = generator.encode(similar_text2)
        emb3 = generator.encode(dissimilar_text)

        # Calculate similarities
        sim_similar = generator.get_similarity(emb1, emb2)
        sim_dissimilar = generator.get_similarity(emb1, emb3)

        # Check similarity values are in range
        assert -1.0 <= sim_similar <= 1.0
        assert -1.0 <= sim_dissimilar <= 1.0

        # Only check semantic similarity if actual semantic embeddings are available
        if generator.is_available():
            # Similar texts should have higher similarity
            assert sim_similar > sim_dissimilar
            assert sim_similar > 0.5  # Should be reasonably similar

    def test_dimension_adjustment_padding(self):
        """Test dimension adjustment with padding."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",  # 384 native dimensions
            use_gpu=False,
        )

        # Request more dimensions than native
        text = "Test text"
        embedding = generator.encode(text, dimensions=768)

        # Check shape
        assert len(embedding) == 768

        # Check L2 normalization
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5

    def test_dimension_adjustment_truncation(self):
        """Test dimension adjustment with truncation."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",  # 384 native dimensions
            use_gpu=False,
        )

        # Request fewer dimensions than native
        text = "Test text"
        embedding = generator.encode(text, dimensions=128)

        # Check shape
        assert len(embedding) == 128

        # Check L2 normalization
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5

    def test_l2_normalization(self):
        """Test L2 normalization."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Generate multiple embeddings
        texts = [f"Text number {i}" for i in range(10)]
        embeddings = generator.encode_batch(texts)

        # Check all are normalized
        for embedding in embeddings:
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 1e-5

    def test_caching(self):
        """Test LRU caching."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
            cache_size=512,
        )

        # Generate same embedding twice
        text = "Cached text"
        emb1 = generator.encode(text)
        emb2 = generator.encode(text)

        # Should be identical (from cache)
        assert emb1 == emb2

    def test_is_available(self):
        """Test availability check."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Check if available
        available = generator.is_available()

        # Should be available if sentence-transformers is installed
        # May be False if not installed, which is fine
        assert isinstance(available, bool)

    def test_fallback_embedding(self):
        """Test fallback to random embeddings."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Force use of fallback
        text = "Test text"
        embedding = generator._fallback_embedding(text, dimensions=384)

        # Check shape and type
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

        # Check L2 normalization
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5

        # Check consistency (same text should give same embedding)
        embedding2 = generator._fallback_embedding(text, dimensions=384)
        assert embedding == embedding2

    def test_model_info(self):
        """Test model information retrieval."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        info = generator.get_model_info()

        # Check info structure
        assert isinstance(info, dict)
        assert "model_name" in info
        assert "native_dimensions" in info
        assert "max_seq_length" in info
        assert "description" in info
        assert "use_gpu" in info
        assert "available" in info

        # Check values
        assert info["model_name"] == "all-MiniLM-L6-v2"
        assert info["native_dimensions"] == 384
        assert info["use_gpu"] is False
        assert isinstance(info["available"], bool)

    def test_gpu_cpu_consistency(self):
        """Test consistency between GPU and CPU."""
        # Create two generators (one GPU, one CPU)
        generator_cpu = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # If GPU is not available, this will fall back to CPU anyway
        generator_gpu = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=True,
        )

        # Generate embeddings
        text = "Test text for GPU/CPU comparison"
        emb_cpu = generator_cpu.encode(text)
        emb_gpu = generator_gpu.encode(text)

        # Should be very similar (may have small numerical differences)
        similarity = np.dot(emb_cpu, emb_gpu)
        assert similarity > 0.99  # Very high similarity

    def test_different_models(self):
        """Test different sentence transformer models."""
        models = [
            ("all-MiniLM-L6-v2", 384),
            ("all-mpnet-base-v2", 768),
        ]

        for model_name, expected_dims in models:
            generator = SemanticEmbeddingGenerator(
                model_name=model_name,
                use_gpu=False,
            )

            text = "Test text"
            embedding = generator.encode(text)

            # Check dimensions
            if generator.is_available():
                assert len(embedding) == expected_dims
            else:
                # Fallback mode
                assert len(embedding) == expected_dims

    def test_global_generator(self):
        """Test global generator singleton."""
        # Reset first
        reset_global_generator()

        # Get generator
        gen1 = get_semantic_embedding_generator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Get again
        gen2 = get_semantic_embedding_generator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Should be same instance
        assert gen1 is gen2

        # Reset
        reset_global_generator()


class TestSemanticEmbeddingsIntegration:
    """Test semantic embeddings integration with FakeAI service."""

    @pytest.mark.asyncio
    async def test_service_with_semantic_embeddings(self):
        """Test FakeAI service with semantic embeddings enabled."""
        config = AppConfig(
            use_semantic_embeddings=True,
            embedding_model="all-MiniLM-L6-v2",
            embedding_use_gpu=False,
            response_delay=0.0,
        )
        service = FakeAIService(config)

        # Create embedding request
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Hello, world!",
        )

        response = await service.create_embedding(request)

        # Check response
        assert len(response.data) == 1
        embedding = response.data[0].embedding

        # Check embedding properties
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # Default dimensions
        assert all(isinstance(x, float) for x in embedding)

        # Check L2 normalization
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5

    @pytest.mark.asyncio
    async def test_service_with_custom_dimensions(self):
        """Test FakeAI service with custom dimensions."""
        config = AppConfig(
            use_semantic_embeddings=True,
            embedding_model="all-MiniLM-L6-v2",
            embedding_use_gpu=False,
            response_delay=0.0,
        )
        service = FakeAIService(config)

        # Request custom dimensions
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Hello, world!",
            dimensions=512,
        )

        response = await service.create_embedding(request)

        # Check dimensions
        embedding = response.data[0].embedding
        assert len(embedding) == 512

    @pytest.mark.asyncio
    async def test_service_without_semantic_embeddings(self):
        """Test FakeAI service without semantic embeddings (random)."""
        config = AppConfig(
            use_semantic_embeddings=False,
            response_delay=0.0,
        )
        service = FakeAIService(config)

        # Create embedding request
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Hello, world!",
        )

        response = await service.create_embedding(request)

        # Check response (should use random embeddings)
        assert len(response.data) == 1
        embedding = response.data[0].embedding
        assert isinstance(embedding, list)
        assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_service_semantic_similarity(self):
        """Test semantic similarity in service responses."""
        config = AppConfig(
            use_semantic_embeddings=True,
            embedding_model="all-MiniLM-L6-v2",
            embedding_use_gpu=False,
            response_delay=0.0,
        )
        service = FakeAIService(config)

        # Create embeddings for similar texts
        request1 = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="The cat sat on the mat.",
        )
        request2 = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="A cat is sitting on the mat.",
        )
        request3 = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Quantum physics is fascinating.",
        )

        response1 = await service.create_embedding(request1)
        response2 = await service.create_embedding(request2)
        response3 = await service.create_embedding(request3)

        emb1 = response1.data[0].embedding
        emb2 = response2.data[0].embedding
        emb3 = response3.data[0].embedding

        # Calculate similarities
        sim_similar = float(np.dot(emb1, emb2))
        sim_dissimilar = float(np.dot(emb1, emb3))

        # Similar texts should have higher similarity
        # Only check if semantic embeddings are actually available
        if service.semantic_embeddings and service.semantic_embeddings.is_available():
            assert sim_similar > sim_dissimilar

    @pytest.mark.asyncio
    async def test_service_batch_embeddings(self):
        """Test batch embedding generation in service."""
        config = AppConfig(
            use_semantic_embeddings=True,
            embedding_model="all-MiniLM-L6-v2",
            embedding_use_gpu=False,
            response_delay=0.0,
        )
        service = FakeAIService(config)

        # Create batch request
        texts = [
            "First text",
            "Second text",
            "Third text",
        ]
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input=texts,
        )

        response = await service.create_embedding(request)

        # Check response
        assert len(response.data) == 3
        for i, data in enumerate(response.data):
            assert data.index == i
            assert len(data.embedding) == 1536

    @pytest.mark.asyncio
    async def test_service_fallback_on_error(self):
        """Test service fallback to random on error."""
        config = AppConfig(
            use_semantic_embeddings=True,
            embedding_model="invalid-model-name",  # Invalid model
            embedding_use_gpu=False,
            response_delay=0.0,
        )
        service = FakeAIService(config)

        # Should fall back to random embeddings
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Hello, world!",
        )

        response = await service.create_embedding(request)

        # Should still work (with fallback)
        assert len(response.data) == 1
        embedding = response.data[0].embedding
        assert isinstance(embedding, list)
        assert len(embedding) == 1536


class TestDimensionAdjustment:
    """Test dimension adjustment logic."""

    def test_pad_to_larger_dimensions(self):
        """Test padding to larger dimensions."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Create a small embedding
        embedding = np.array([1.0, 2.0, 3.0])

        # Pad to larger size
        adjusted = generator._adjust_dimensions(embedding, target_dimensions=10)

        # Check size
        assert len(adjusted) == 10

        # Check values (first 3 should match, rest should be 0)
        assert adjusted[0] == 1.0
        assert adjusted[1] == 2.0
        assert adjusted[2] == 3.0
        assert all(adjusted[i] == 0.0 for i in range(3, 10))

    def test_truncate_to_smaller_dimensions(self):
        """Test truncation to smaller dimensions."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Create a large embedding
        embedding = np.array([float(i) for i in range(10)])

        # Truncate to smaller size
        adjusted = generator._adjust_dimensions(embedding, target_dimensions=5)

        # Check size
        assert len(adjusted) == 5

        # Check values
        assert adjusted[0] == 0.0
        assert adjusted[1] == 1.0
        assert adjusted[2] == 2.0
        assert adjusted[3] == 3.0
        assert adjusted[4] == 4.0

    def test_no_adjustment_needed(self):
        """Test no adjustment when dimensions match."""
        generator = SemanticEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            use_gpu=False,
        )

        # Create embedding with target dimensions
        embedding = np.array([float(i) for i in range(10)])

        # No adjustment
        adjusted = generator._adjust_dimensions(embedding, target_dimensions=10)

        # Check size
        assert len(adjusted) == 10

        # Check values (should be unchanged)
        assert np.array_equal(adjusted, embedding)
