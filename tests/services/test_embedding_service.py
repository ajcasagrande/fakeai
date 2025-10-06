"""
Tests for EmbeddingService

This module tests the embedding service functionality including:
- Single string and list of strings input
- Custom dimensions
- Semantic vs random embeddings
- Token tracking and usage metrics
- Error handling and edge cases
"""

#  SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest

from fakeai.config import AppConfig
from fakeai.metrics import MetricsTracker
from fakeai.models import EmbeddingRequest
from fakeai.services.embedding_service import EmbeddingService


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig(
        response_delay=0.0,
        use_semantic_embeddings=False,
    )


@pytest.fixture
def metrics_tracker():
    """Create metrics tracker."""
    return MetricsTracker()


@pytest.fixture
def embedding_service(config, metrics_tracker):
    """Create embedding service instance."""
    return EmbeddingService(
        config=config,
        metrics_tracker=metrics_tracker,
        model_registry=None,
    )


@pytest.mark.asyncio
async def test_single_string(embedding_service):
    """Test embedding generation with single string input."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello world",
    )

    response = await embedding_service.create_embedding(request)

    assert response.model == "text-embedding-ada-002"
    assert len(response.data) == 1
    assert response.data[0].index == 0
    assert len(response.data[0].embedding) == 1536  # Default dimensions
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens == 0
    assert response.usage.total_tokens == response.usage.prompt_tokens


@pytest.mark.asyncio
async def test_list_of_strings(embedding_service):
    """Test embedding generation with list of strings."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=["Hello world", "How are you?", "Testing embeddings"],
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 3
    assert response.data[0].index == 0
    assert response.data[1].index == 1
    assert response.data[2].index == 2

    # All should have default dimensions
    for embedding in response.data:
        assert len(embedding.embedding) == 1536


@pytest.mark.asyncio
async def test_custom_dimensions_small(embedding_service):
    """Test embedding generation with small custom dimensions."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello world",
        dimensions=256,
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data[0].embedding) == 256


@pytest.mark.asyncio
async def test_custom_dimensions_large(embedding_service):
    """Test embedding generation with large custom dimensions."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello world",
        dimensions=3072,
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data[0].embedding) == 3072


@pytest.mark.asyncio
async def test_custom_dimensions_various_sizes(embedding_service):
    """Test various dimension sizes."""
    dimensions_to_test = [128, 256, 512, 768, 1024, 1536, 2048, 3072]

    for dims in dimensions_to_test:
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test",
            dimensions=dims,
        )

        response = await embedding_service.create_embedding(request)
        assert len(response.data[0].embedding) == dims


@pytest.mark.asyncio
async def test_dimensions_validation_too_small(embedding_service):
    """Test that dimensions of 1 are allowed (minimum)."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello",
        dimensions=1,
    )

    # Should work with minimum dimension of 1
    response = await embedding_service.create_embedding(request)
    assert len(response.data[0].embedding) == 1


@pytest.mark.asyncio
async def test_dimensions_validation_too_large(embedding_service):
    """Test that dimensions above 3072 are rejected."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello",
        dimensions=4000,
    )

    with pytest.raises(ValueError, match="Dimensions must be between 1 and 3072"):
        await embedding_service.create_embedding(request)


@pytest.mark.asyncio
async def test_token_tracking(embedding_service):
    """Test that token usage is tracked correctly in the response."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="This is a test message with multiple words",
    )

    response = await embedding_service.create_embedding(request)

    # Verify token counts are tracked in response
    assert response.usage.total_tokens > 0
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens == 0
    assert response.usage.total_tokens == response.usage.prompt_tokens


@pytest.mark.asyncio
async def test_embedding_consistency(embedding_service):
    """Test that same input produces consistent embeddings (random but deterministic)."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello world",
        dimensions=512,
    )

    response1 = await embedding_service.create_embedding(request)
    response2 = await embedding_service.create_embedding(request)

    # Should be identical due to deterministic hashing
    assert response1.data[0].embedding == response2.data[0].embedding


@pytest.mark.asyncio
async def test_embedding_uniqueness(embedding_service):
    """Test that different inputs produce different embeddings."""
    request1 = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello world",
    )

    request2 = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Goodbye world",
    )

    response1 = await embedding_service.create_embedding(request1)
    response2 = await embedding_service.create_embedding(request2)

    assert response1.data[0].embedding != response2.data[0].embedding


@pytest.mark.asyncio
async def test_embedding_normalization(embedding_service):
    """Test that embeddings are L2 normalized (unit length)."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello world",
    )

    response = await embedding_service.create_embedding(request)
    embedding = response.data[0].embedding

    # Calculate L2 norm
    norm = np.linalg.norm(embedding)

    # Should be approximately 1.0 (unit vector)
    assert abs(norm - 1.0) < 0.001


@pytest.mark.asyncio
async def test_multiple_embeddings_normalized(embedding_service):
    """Test that all embeddings in batch are normalized."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=["First text", "Second text", "Third text"],
    )

    response = await embedding_service.create_embedding(request)

    for embedding_obj in response.data:
        embedding = embedding_obj.embedding
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.001


@pytest.mark.asyncio
async def test_token_ids_input_single(embedding_service):
    """Test embedding with token IDs input (single sequence)."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=[100, 200, 300, 400],
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 1
    assert len(response.data[0].embedding) == 1536


@pytest.mark.asyncio
async def test_token_ids_input_multiple(embedding_service):
    """Test embedding with token IDs input (multiple sequences)."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=[[100, 200], [300, 400, 500], [600]],
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 3


@pytest.mark.asyncio
async def test_empty_string_input(embedding_service):
    """Test embedding with empty string."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="",
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 1
    assert len(response.data[0].embedding) == 1536


@pytest.mark.asyncio
async def test_long_text_input(embedding_service):
    """Test embedding with very long text."""
    long_text = "Hello world " * 1000  # 2000 words

    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=long_text,
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 1
    assert response.usage.prompt_tokens > 1000


@pytest.mark.asyncio
async def test_special_characters(embedding_service):
    """Test embedding with special characters."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="!@#$%^&*()_+-=[]{}|;':\",./<>?",
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 1
    assert len(response.data[0].embedding) == 1536


@pytest.mark.asyncio
async def test_unicode_text(embedding_service):
    """Test embedding with unicode text."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello 世界 🌍 Привет мир",
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 1
    assert len(response.data[0].embedding) == 1536


@pytest.mark.asyncio
async def test_semantic_embeddings_enabled():
    """Test with semantic embeddings enabled (will use random as fallback)."""
    config = AppConfig(
        response_delay=0.0,
        use_semantic_embeddings=True,
    )
    metrics_tracker = MetricsTracker()
    service = EmbeddingService(
        config=config,
        metrics_tracker=metrics_tracker,
        model_registry=None,
    )

    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello world",
    )

    response = await service.create_embedding(request)

    # Should work even if semantic embeddings not available
    assert len(response.data) == 1
    assert len(response.data[0].embedding) == 1536


@pytest.mark.asyncio
async def test_batch_processing_performance(embedding_service):
    """Test that batch processing handles multiple inputs efficiently."""
    large_batch = [f"Test sentence number {i}" for i in range(100)]

    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=large_batch,
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 100
    assert all(len(emb.embedding) == 1536 for emb in response.data)


@pytest.mark.asyncio
async def test_usage_response_structure(embedding_service):
    """Test that usage response has correct structure."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Hello world",
    )

    response = await embedding_service.create_embedding(request)

    assert hasattr(response, "usage")
    assert hasattr(response.usage, "prompt_tokens")
    assert hasattr(response.usage, "completion_tokens")
    assert hasattr(response.usage, "total_tokens")
    assert response.usage.completion_tokens == 0
    assert response.usage.total_tokens == response.usage.prompt_tokens


@pytest.mark.asyncio
async def test_model_name_preservation(embedding_service):
    """Test that model name is preserved in response."""
    models_to_test = [
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-large",
        "custom-model",
    ]

    for model in models_to_test:
        request = EmbeddingRequest(
            model=model,
            input="Test",
        )

        response = await embedding_service.create_embedding(request)
        assert response.model == model


@pytest.mark.asyncio
async def test_object_type(embedding_service):
    """Test that response has correct object type."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Test",
    )

    response = await embedding_service.create_embedding(request)

    assert response.object == "list"
    assert all(emb.object == "embedding" for emb in response.data)


@pytest.mark.asyncio
async def test_index_ordering(embedding_service):
    """Test that embeddings maintain correct index order."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=["First", "Second", "Third", "Fourth", "Fifth"],
    )

    response = await embedding_service.create_embedding(request)

    for i, embedding in enumerate(response.data):
        assert embedding.index == i


@pytest.mark.asyncio
async def test_invalid_input_type():
    """Test that invalid input type raises ValueError."""
    config = AppConfig(response_delay=0.0)
    metrics_tracker = MetricsTracker()
    service = EmbeddingService(
        config=config,
        metrics_tracker=metrics_tracker,
        model_registry=None,
    )

    # This would fail at Pydantic validation level, so we test the internal method
    with pytest.raises(ValueError, match="Unsupported input format"):
        service._process_embedding_input({"invalid": "type"})


@pytest.mark.asyncio
async def test_encoding_format_base64(embedding_service):
    """Test base64 encoding format."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Test",
        encoding_format="base64",
    )

    response = await embedding_service.create_embedding(request)

    # With base64, embedding should be a string
    assert isinstance(response.data[0].embedding, str)
    # Should be valid base64
    import base64
    try:
        base64.b64decode(response.data[0].embedding)
    except Exception:
        pytest.fail("Invalid base64 string")


@pytest.mark.asyncio
async def test_encoding_format_float(embedding_service):
    """Test float encoding format (default)."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input="Test",
        encoding_format="float",
    )

    response = await embedding_service.create_embedding(request)

    # With float, embedding should be a list
    assert isinstance(response.data[0].embedding, list)
    assert all(isinstance(x, float) for x in response.data[0].embedding)


@pytest.mark.asyncio
async def test_batch_with_base64_encoding(embedding_service):
    """Test batch embeddings with base64 encoding."""
    request = EmbeddingRequest(
        model="text-embedding-ada-002",
        input=["Text 1", "Text 2", "Text 3"],
        encoding_format="base64",
    )

    response = await embedding_service.create_embedding(request)

    assert len(response.data) == 3
    for embedding_obj in response.data:
        assert isinstance(embedding_obj.embedding, str)
        # Verify valid base64
        import base64
        try:
            base64.b64decode(embedding_obj.embedding)
        except Exception:
            pytest.fail(f"Invalid base64 string at index {embedding_obj.index}")
