"""
Tests for Vector Stores API

Tests complete vector store CRUD operations, file management,
chunking strategies, expiration policies, and search simulation.
"""

import pytest
import time

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import (
    AutoChunkingStrategy,
    CreateVectorStoreRequest,
    CreateVectorStoreFileRequest,
    CreateVectorStoreFileBatchRequest,
    ExpiresAfter,
    ModifyVectorStoreRequest,
    StaticChunkingStrategy,
)


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig(response_delay=0.0, debug=True)


@pytest.fixture
def service(config):
    """Create FakeAI service instance."""
    return FakeAIService(config)


@pytest.mark.asyncio
async def test_create_vector_store_basic(service):
    """Test creating a basic vector store."""
    request = CreateVectorStoreRequest(
        name="Test Vector Store",
    )

    vs = await service.create_vector_store(request)

    assert vs.id.startswith("vs_")
    assert vs.name == "Test Vector Store"
    assert vs.status == "completed"
    assert vs.file_counts.total == 0
    assert vs.usage_bytes == 0


@pytest.mark.asyncio
async def test_create_vector_store_with_files(service):
    """Test creating a vector store with files."""
    # Get a file to add
    files = await service.list_files()
    assert len(files.data) > 0
    file_id = files.data[0].id

    request = CreateVectorStoreRequest(
        name="Test Vector Store with Files",
        file_ids=[file_id],
    )

    vs = await service.create_vector_store(request)

    assert vs.id.startswith("vs_")
    assert vs.name == "Test Vector Store with Files"
    assert vs.status == "in_progress"
    assert vs.file_counts.total == 1
    assert vs.file_counts.in_progress == 1

    # Wait a bit for processing
    await asyncio.sleep(0.5)

    # Retrieve and check status
    vs_updated = await service.retrieve_vector_store(vs.id)
    assert vs_updated.status == "completed"
    assert vs_updated.file_counts.completed == 1
    assert vs_updated.file_counts.in_progress == 0


@pytest.mark.asyncio
async def test_create_vector_store_with_expiration(service):
    """Test creating a vector store with expiration policy."""
    request = CreateVectorStoreRequest(
        name="Expiring Vector Store",
        expires_after=ExpiresAfter(anchor="last_active_at", days=7),
    )

    vs = await service.create_vector_store(request)

    assert vs.expires_after is not None
    assert vs.expires_after.days == 7
    assert vs.expires_at is not None
    expected_expiry = vs.created_at + (7 * 86400)
    assert vs.expires_at == expected_expiry


@pytest.mark.asyncio
async def test_create_vector_store_with_metadata(service):
    """Test creating a vector store with metadata."""
    metadata = {"purpose": "test", "environment": "development"}
    request = CreateVectorStoreRequest(
        name="Vector Store with Metadata",
        metadata=metadata,
    )

    vs = await service.create_vector_store(request)

    assert vs.metadata == metadata


@pytest.mark.asyncio
async def test_list_vector_stores(service):
    """Test listing vector stores."""
    # Create a few vector stores
    for i in range(3):
        request = CreateVectorStoreRequest(name=f"Test Store {i}")
        await service.create_vector_store(request)

    # List all
    result = await service.list_vector_stores(limit=10)

    assert len(result.data) >= 3
    assert result.object == "list"


@pytest.mark.asyncio
async def test_list_vector_stores_pagination(service):
    """Test vector store list pagination."""
    # Create multiple stores
    for i in range(5):
        request = CreateVectorStoreRequest(name=f"Pagination Test {i}")
        await service.create_vector_store(request)

    # List with limit
    result1 = await service.list_vector_stores(limit=2)
    assert len(result1.data) == 2
    assert result1.has_more is True

    # List next page
    result2 = await service.list_vector_stores(limit=2, after=result1.last_id)
    assert len(result2.data) == 2
    # IDs should be different
    assert result2.data[0].id != result1.data[0].id


@pytest.mark.asyncio
async def test_retrieve_vector_store(service):
    """Test retrieving a vector store by ID."""
    # Create a store
    request = CreateVectorStoreRequest(name="Retrieve Test")
    vs_created = await service.create_vector_store(request)

    # Retrieve it
    vs_retrieved = await service.retrieve_vector_store(vs_created.id)

    assert vs_retrieved.id == vs_created.id
    assert vs_retrieved.name == vs_created.name
    assert vs_retrieved.last_active_at >= vs_created.created_at


@pytest.mark.asyncio
async def test_retrieve_nonexistent_vector_store(service):
    """Test retrieving a nonexistent vector store."""
    with pytest.raises(ValueError, match="not found"):
        await service.retrieve_vector_store("vs_nonexistent")


@pytest.mark.asyncio
async def test_modify_vector_store(service):
    """Test modifying a vector store."""
    # Create a store
    request = CreateVectorStoreRequest(name="Original Name")
    vs = await service.create_vector_store(request)

    # Modify it
    modify_request = ModifyVectorStoreRequest(
        name="Updated Name",
        metadata={"updated": "true"},
    )
    vs_modified = await service.modify_vector_store(vs.id, modify_request)

    assert vs_modified.name == "Updated Name"
    assert vs_modified.metadata == {"updated": "true"}


@pytest.mark.asyncio
async def test_modify_vector_store_expiration(service):
    """Test modifying vector store expiration."""
    # Create a store
    request = CreateVectorStoreRequest(name="Expiration Test")
    vs = await service.create_vector_store(request)

    # Add expiration
    modify_request = ModifyVectorStoreRequest(
        expires_after=ExpiresAfter(anchor="last_active_at", days=30)
    )
    vs_modified = await service.modify_vector_store(vs.id, modify_request)

    assert vs_modified.expires_after is not None
    assert vs_modified.expires_after.days == 30
    assert vs_modified.expires_at is not None


@pytest.mark.asyncio
async def test_delete_vector_store(service):
    """Test deleting a vector store."""
    # Create a store
    request = CreateVectorStoreRequest(name="Delete Test")
    vs = await service.create_vector_store(request)

    # Delete it
    result = await service.delete_vector_store(vs.id)

    assert result["id"] == vs.id
    assert result["deleted"] is True

    # Verify it's gone
    with pytest.raises(ValueError, match="not found"):
        await service.retrieve_vector_store(vs.id)


@pytest.mark.asyncio
async def test_add_file_to_vector_store(service):
    """Test adding a file to a vector store."""
    # Create empty store
    vs_request = CreateVectorStoreRequest(name="File Test")
    vs = await service.create_vector_store(vs_request)

    # Get a file
    files = await service.list_files()
    file_id = files.data[0].id

    # Add file to store
    file_request = CreateVectorStoreFileRequest(file_id=file_id)
    vs_file = await service.create_vector_store_file(vs.id, file_request)

    assert vs_file.id.startswith("vsf_")
    assert vs_file.vector_store_id == vs.id
    assert vs_file.status == "in_progress"
    assert vs_file.chunking_strategy is not None

    # Wait for processing
    await asyncio.sleep(0.6)

    # Check file status
    vs_file_updated = await service.retrieve_vector_store_file(vs.id, vs_file.id)
    assert vs_file_updated.status == "completed"


@pytest.mark.asyncio
async def test_add_file_with_static_chunking(service):
    """Test adding a file with static chunking strategy."""
    # Create store
    vs_request = CreateVectorStoreRequest(name="Chunking Test")
    vs = await service.create_vector_store(vs_request)

    # Get a file
    files = await service.list_files()
    file_id = files.data[0].id

    # Add with static chunking
    chunking = StaticChunkingStrategy(
        max_chunk_size_tokens=500,
        chunk_overlap_tokens=100,
    )
    file_request = CreateVectorStoreFileRequest(
        file_id=file_id, chunking_strategy=chunking
    )
    vs_file = await service.create_vector_store_file(vs.id, file_request)

    assert isinstance(vs_file.chunking_strategy, StaticChunkingStrategy)
    assert vs_file.chunking_strategy.max_chunk_size_tokens == 500
    assert vs_file.chunking_strategy.chunk_overlap_tokens == 100


@pytest.mark.asyncio
async def test_list_vector_store_files(service):
    """Test listing files in a vector store."""
    # Create store with files
    files = await service.list_files()
    file_ids = [f.id for f in files.data[:2]]

    vs_request = CreateVectorStoreRequest(
        name="List Files Test", file_ids=file_ids
    )
    vs = await service.create_vector_store(vs_request)

    # Wait for processing
    await asyncio.sleep(0.6)

    # List files
    file_list = await service.list_vector_store_files(vs.id, limit=10)

    assert len(file_list.data) == 2
    assert file_list.object == "list"


@pytest.mark.asyncio
async def test_delete_vector_store_file(service):
    """Test deleting a file from a vector store."""
    # Create store with file
    files = await service.list_files()
    file_id = files.data[0].id

    vs_request = CreateVectorStoreRequest(
        name="Delete File Test", file_ids=[file_id]
    )
    vs = await service.create_vector_store(vs_request)

    # Wait for processing
    await asyncio.sleep(0.6)

    # Get the vector store file
    vs_files = await service.list_vector_store_files(vs.id)
    assert len(vs_files.data) == 1
    vs_file_id = vs_files.data[0].id

    # Delete it
    result = await service.delete_vector_store_file(vs.id, vs_file_id)

    assert result["id"] == vs_file_id
    assert result["deleted"] is True

    # Verify it's gone
    vs_files_after = await service.list_vector_store_files(vs.id)
    assert len(vs_files_after.data) == 0


@pytest.mark.asyncio
async def test_create_file_batch(service):
    """Test creating a batch of files."""
    # Create store
    vs_request = CreateVectorStoreRequest(name="Batch Test")
    vs = await service.create_vector_store(vs_request)

    # Get multiple files
    files = await service.list_files()
    file_ids = [f.id for f in files.data[:3]]

    # Create batch
    batch_request = CreateVectorStoreFileBatchRequest(file_ids=file_ids)
    batch = await service.create_vector_store_file_batch(vs.id, batch_request)

    assert batch.id.startswith("vsfb_")
    assert batch.vector_store_id == vs.id
    assert batch.status == "in_progress"
    assert batch.file_counts.total == 3


@pytest.mark.asyncio
async def test_retrieve_file_batch(service):
    """Test retrieving a file batch."""
    # Create store with files
    files = await service.list_files()
    file_ids = [f.id for f in files.data[:2]]

    vs_request = CreateVectorStoreRequest(
        name="Batch Retrieve Test", file_ids=file_ids
    )
    vs = await service.create_vector_store(vs_request)

    # Wait for processing
    await asyncio.sleep(0.6)

    # Retrieve batch (using mock batch_id)
    batch = await service.retrieve_vector_store_file_batch(vs.id, "batch_test")

    assert batch.vector_store_id == vs.id
    assert batch.status == "completed"
    assert batch.file_counts.completed == 2


@pytest.mark.asyncio
async def test_cancel_file_batch(service):
    """Test cancelling a file batch."""
    # Create store with files
    files = await service.list_files()
    file_ids = [f.id for f in files.data[:2]]

    vs_request = CreateVectorStoreRequest(
        name="Batch Cancel Test", file_ids=file_ids
    )
    vs = await service.create_vector_store(vs_request)

    # Cancel immediately (before processing completes)
    batch = await service.cancel_vector_store_file_batch(vs.id, "batch_test")

    assert batch.status == "cancelled"


@pytest.mark.asyncio
async def test_chunking_simulation(service):
    """Test the chunking simulation logic."""
    # Get a file
    files = await service.list_files()
    file_id = files.data[0].id

    # Test auto chunking
    auto_chunks = await service._simulate_chunking(
        file_id, AutoChunkingStrategy()
    )
    assert len(auto_chunks) > 0
    assert all("id" in chunk for chunk in auto_chunks)
    assert all("text" in chunk for chunk in auto_chunks)
    assert all("token_count" in chunk for chunk in auto_chunks)

    # Test static chunking
    static_strategy = StaticChunkingStrategy(
        max_chunk_size_tokens=200, chunk_overlap_tokens=50
    )
    static_chunks = await service._simulate_chunking(file_id, static_strategy)
    assert len(static_chunks) > 0

    # Chunks should have overlap
    if len(static_chunks) > 1:
        # Check that start indices show overlap pattern
        assert static_chunks[1]["start_index"] < (
            static_chunks[0]["start_index"] + static_chunks[0]["token_count"]
        )


@pytest.mark.asyncio
async def test_embedding_generation(service):
    """Test chunk embedding generation."""
    chunks = [
        {"id": "chunk_1", "text": "Hello world", "token_count": 2},
        {"id": "chunk_2", "text": "Test embedding", "token_count": 2},
    ]

    embeddings = await service._create_chunk_embeddings(chunks)

    assert len(embeddings) == 2
    assert all(len(emb) == 1536 for emb in embeddings)
    # Check embeddings are normalized (L2 norm should be ~1.0)
    import numpy as np

    for emb in embeddings:
        norm = np.linalg.norm(emb)
        assert abs(norm - 1.0) < 0.001


@pytest.mark.asyncio
async def test_vector_store_search(service):
    """Test vector store search functionality."""
    # Create store with file
    files = await service.list_files()
    file_id = files.data[0].id

    vs_request = CreateVectorStoreRequest(
        name="Search Test", file_ids=[file_id]
    )
    vs = await service.create_vector_store(vs_request)

    # Wait for processing
    await asyncio.sleep(0.6)

    # Perform search
    results = await service._search_vector_store(
        vs.id, query_text="test query", top_k=5, score_threshold=0.0
    )

    assert isinstance(results, list)
    # May have results depending on random embeddings
    if len(results) > 0:
        assert all("chunk_id" in r for r in results)
        assert all("text" in r for r in results)
        assert all("score" in r for r in results)
        # Scores should be between -1 and 1 (cosine similarity)
        assert all(-1 <= r["score"] <= 1 for r in results)


@pytest.mark.asyncio
async def test_auto_chunking_defaults(service):
    """Test that auto chunking uses correct defaults."""
    files = await service.list_files()
    file_id = files.data[0].id

    chunks = await service._simulate_chunking(file_id, AutoChunkingStrategy())

    # Auto strategy should use 800 token chunks with 400 token overlap
    # Check that chunks are reasonably sized
    assert all(chunk["token_count"] <= 800 for chunk in chunks)


@pytest.mark.asyncio
async def test_vector_store_file_counts(service):
    """Test that file counts are properly tracked."""
    # Create store
    vs_request = CreateVectorStoreRequest(name="File Counts Test")
    vs = await service.create_vector_store(vs_request)

    # Add files one by one
    files = await service.list_files()
    for i in range(3):
        file_request = CreateVectorStoreFileRequest(file_id=files.data[i].id)
        await service.create_vector_store_file(vs.id, file_request)

    # Check counts
    vs_updated = await service.retrieve_vector_store(vs.id)
    assert vs_updated.file_counts.total == 3
    assert vs_updated.file_counts.in_progress == 3

    # Wait for processing
    await asyncio.sleep(1.0)

    # Check final counts
    vs_final = await service.retrieve_vector_store(vs.id)
    assert vs_final.file_counts.completed == 3
    assert vs_final.file_counts.in_progress == 0


@pytest.mark.asyncio
async def test_vector_store_usage_bytes(service):
    """Test that usage_bytes is tracked correctly."""
    # Get a file with known size
    files = await service.list_files()
    file_obj = files.data[0]

    vs_request = CreateVectorStoreRequest(
        name="Usage Test", file_ids=[file_obj.id]
    )
    vs = await service.create_vector_store(vs_request)

    # Wait for processing
    await asyncio.sleep(0.6)

    # Check usage_bytes
    vs_updated = await service.retrieve_vector_store(vs.id)
    assert vs_updated.usage_bytes == file_obj.bytes


# Import asyncio for sleep functions
import asyncio
