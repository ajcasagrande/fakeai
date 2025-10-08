"""
Comprehensive tests for the Batch API implementation.

Tests batch creation, processing, cancellation, error handling, and output file generation.
"""

import asyncio
import json

import pytest

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import (
    BatchListResponse,
    CreateBatchRequest,
)


@pytest.fixture
def service():
    """Create a FakeAIService instance for testing."""
    config = AppConfig(response_delay=0.0, debug=False)
    return FakeAIService(config)


@pytest.mark.asyncio
async def test_create_batch(service):
    """Test creating a new batch."""
    # Get a file ID from existing files
    file_id = service.files[0].id

    # Create batch request
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"test": "batch1"},
    )

    # Create batch
    batch = await service.create_batch(request)

    # Verify batch was created
    assert batch.id.startswith("batch_")
    assert batch.endpoint == "/v1/chat/completions"
    assert batch.input_file_id == file_id
    assert batch.completion_window == "24h"
    assert batch.status == "validating"
    assert batch.metadata == {"test": "batch1"}
    assert batch.request_counts.total == 0
    assert batch.request_counts.completed == 0
    assert batch.request_counts.failed == 0
    assert batch.created_at > 0
    assert batch.expires_at > batch.created_at

    # Verify batch is stored
    assert batch.id in service.batches
    assert batch.id in service.batch_tasks


@pytest.mark.asyncio
async def test_batch_processing_completion(service):
    """Test that batch processing completes successfully."""
    # Get a file ID
    file_id = service.files[0].id

    # Store sample input content
    sample_input = "\n".join(
        [
            json.dumps(
                {
                    "custom_id": f"req-{i}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "meta-llama/Llama-3.1-8B-Instruct",
                        "messages": [{"role": "user", "content": f"Test {i}"}],
                        "max_tokens": 10,
                    },
                }
            )
            for i in range(3)
        ]
    )
    service.batch_file_contents[file_id] = sample_input

    # Create batch
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch = await service.create_batch(request)

    # Wait for processing to complete (with timeout)
    for _ in range(50):  # Max 5 seconds
        await asyncio.sleep(0.1)
        updated_batch = await service.retrieve_batch(batch.id)
        if updated_batch.status == "completed":
            break
    else:
        pytest.fail("Batch did not complete within timeout")

    # Verify completion
    final_batch = await service.retrieve_batch(batch.id)
    assert final_batch.status == "completed"
    assert final_batch.in_progress_at is not None
    assert final_batch.finalizing_at is not None
    assert final_batch.completed_at is not None
    assert final_batch.request_counts.total == 3
    assert final_batch.request_counts.completed == 3
    assert final_batch.request_counts.failed == 0

    # Verify output file was created
    assert final_batch.output_file_id is not None
    output_file = next(
        (f for f in service.files if f.id == final_batch.output_file_id), None
    )
    assert output_file is not None
    assert output_file.purpose == "batch_output"
    assert output_file.status == "processed"

    # Verify output content
    output_content = service.batch_file_contents[final_batch.output_file_id]
    output_lines = output_content.strip().split("\n")
    assert len(output_lines) == 3

    # Parse first output line
    output_obj = json.loads(output_lines[0])
    assert "id" in output_obj
    assert "custom_id" in output_obj
    assert "response" in output_obj
    assert output_obj["error"] is None
    assert "choices" in output_obj["response"]


@pytest.mark.asyncio
async def test_batch_cancellation(service):
    """Test cancelling a batch."""
    # Get a file ID
    file_id = service.files[0].id

    # Create a batch with many requests to ensure it's still processing
    sample_input = "\n".join(
        [
            json.dumps(
                {
                    "custom_id": f"req-{i}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "meta-llama/Llama-3.1-8B-Instruct",
                        "messages": [{"role": "user", "content": f"Test {i}"}],
                    },
                }
            )
            for i in range(20)
        ]
    )
    service.batch_file_contents[file_id] = sample_input

    # Create batch
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch = await service.create_batch(request)

    # Wait a bit for it to start processing
    await asyncio.sleep(0.5)

    # Cancel the batch
    cancelled_batch = await service.cancel_batch(batch.id)

    # Verify cancellation
    assert cancelled_batch.status == "cancelled"
    assert cancelled_batch.cancelling_at is not None
    assert cancelled_batch.cancelled_at is not None


@pytest.mark.asyncio
async def test_batch_with_errors(service):
    """Test batch processing with some failed requests."""
    # Get a file ID
    file_id = service.files[0].id

    # Create input with both valid and invalid requests
    sample_input = "\n".join(
        [
            # Valid request
            json.dumps(
                {
                    "custom_id": "req-1",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "meta-llama/Llama-3.1-8B-Instruct",
                        "messages": [{"role": "user", "content": "Test"}],
                    },
                }
            ),
            # Invalid request (missing messages)
            json.dumps(
                {
                    "custom_id": "req-2",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "meta-llama/Llama-3.1-8B-Instruct",
                    },
                }
            ),
        ]
    )
    service.batch_file_contents[file_id] = sample_input

    # Create batch
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch = await service.create_batch(request)

    # Wait for completion
    for _ in range(50):
        await asyncio.sleep(0.1)
        updated_batch = await service.retrieve_batch(batch.id)
        if updated_batch.status in ["completed", "failed"]:
            break

    # Verify results
    final_batch = await service.retrieve_batch(batch.id)
    assert final_batch.request_counts.total == 2
    assert final_batch.request_counts.completed >= 1
    assert final_batch.request_counts.failed >= 1

    # Verify error file was created
    if final_batch.request_counts.failed > 0:
        assert final_batch.error_file_id is not None
        error_file = next(
            (f for f in service.files if f.id == final_batch.error_file_id), None
        )
        assert error_file is not None
        assert error_file.purpose == "batch_errors"


@pytest.mark.asyncio
async def test_retrieve_batch(service):
    """Test retrieving a batch by ID."""
    # Create a batch
    file_id = service.files[0].id
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch = await service.create_batch(request)

    # Retrieve it
    retrieved = await service.retrieve_batch(batch.id)

    # Verify
    assert retrieved.id == batch.id
    assert retrieved.endpoint == batch.endpoint
    assert retrieved.input_file_id == batch.input_file_id


@pytest.mark.asyncio
async def test_retrieve_nonexistent_batch(service):
    """Test retrieving a non-existent batch raises error."""
    with pytest.raises(ValueError, match="Batch not found"):
        await service.retrieve_batch("batch_nonexistent")


@pytest.mark.asyncio
async def test_list_batches_empty(service):
    """Test listing batches when none exist."""
    result = await service.list_batches()

    assert isinstance(result, BatchListResponse)
    assert result.data == []
    assert result.first_id is None
    assert result.last_id is None
    assert result.has_more is False


@pytest.mark.asyncio
async def test_list_batches(service):
    """Test listing batches."""
    # Create multiple batches
    file_id = service.files[0].id
    batches = []
    for i in range(3):
        request = CreateBatchRequest(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"index": str(i)},
        )
        batch = await service.create_batch(request)
        batches.append(batch)
        await asyncio.sleep(0.02)  # Ensure different timestamps

    # List all batches
    result = await service.list_batches(limit=10)

    # Verify
    assert len(result.data) == 3
    # Verify all batches are in the result
    result_ids = {b.id for b in result.data}
    created_ids = {b.id for b in batches}
    assert result_ids == created_ids
    assert result.has_more is False
    # Most recent should be first (last created)
    assert (
        result.data[0].created_at
        >= result.data[1].created_at
        >= result.data[2].created_at
    )


@pytest.mark.asyncio
async def test_list_batches_pagination(service):
    """Test batch listing with pagination."""
    # Create multiple batches
    file_id = service.files[0].id
    batches = []
    for i in range(5):
        request = CreateBatchRequest(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await service.create_batch(request)
        batches.append(batch)
        await asyncio.sleep(0.01)

    # List first page
    page1 = await service.list_batches(limit=2)
    assert len(page1.data) == 2
    assert page1.has_more is True

    # List second page
    page2 = await service.list_batches(limit=2, after=page1.last_id)
    assert len(page2.data) == 2
    assert page2.has_more is True

    # Verify no overlap
    page1_ids = {b.id for b in page1.data}
    page2_ids = {b.id for b in page2.data}
    assert len(page1_ids & page2_ids) == 0


@pytest.mark.asyncio
async def test_batch_embeddings_endpoint(service):
    """Test batch processing for embeddings endpoint."""
    # Get a file ID
    file_id = service.files[0].id

    # Create embeddings batch input
    sample_input = "\n".join(
        [
            json.dumps(
                {
                    "custom_id": f"emb-{i}",
                    "method": "POST",
                    "url": "/v1/embeddings",
                    "body": {
                        "model": "sentence-transformers/all-mpnet-base-v2",
                        "input": f"Sample text {i}",
                    },
                }
            )
            for i in range(2)
        ]
    )
    service.batch_file_contents[file_id] = sample_input

    # Create batch
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/embeddings",
        completion_window="24h",
    )
    batch = await service.create_batch(request)

    # Wait for completion
    for _ in range(50):
        await asyncio.sleep(0.1)
        updated_batch = await service.retrieve_batch(batch.id)
        if updated_batch.status == "completed":
            break

    # Verify
    final_batch = await service.retrieve_batch(batch.id)
    assert final_batch.status == "completed"
    assert final_batch.request_counts.completed == 2
    assert final_batch.output_file_id is not None

    # Verify output contains embeddings
    output_content = service.batch_file_contents[final_batch.output_file_id]
    output_line = json.loads(output_content.strip().split("\n")[0])
    assert "response" in output_line
    assert "data" in output_line["response"]
    assert "embedding" in output_line["response"]["data"][0]


@pytest.mark.asyncio
async def test_batch_request_counts(service):
    """Test that request counts are tracked correctly."""
    file_id = service.files[0].id

    # Create input with mix of valid and invalid
    sample_input = "\n".join(
        [
            json.dumps(
                {
                    "custom_id": f"req-{i}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "meta-llama/Llama-3.1-8B-Instruct",
                        "messages": (
                            [{"role": "user", "content": "Test"}] if i % 2 == 0 else []
                        ),  # Every other is invalid
                    },
                }
            )
            for i in range(4)
        ]
    )
    service.batch_file_contents[file_id] = sample_input

    # Create batch
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch = await service.create_batch(request)

    # Wait for completion
    for _ in range(50):
        await asyncio.sleep(0.1)
        updated_batch = await service.retrieve_batch(batch.id)
        if updated_batch.status in ["completed", "failed"]:
            break

    # Verify counts
    final_batch = await service.retrieve_batch(batch.id)
    assert final_batch.request_counts.total == 4
    assert final_batch.request_counts.completed + final_batch.request_counts.failed == 4


@pytest.mark.asyncio
async def test_batch_output_file_format(service):
    """Test that batch output files are properly formatted JSONL."""
    file_id = service.files[0].id

    # Simple valid input
    sample_input = json.dumps(
        {
            "custom_id": "test-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        }
    )
    service.batch_file_contents[file_id] = sample_input

    # Create and process batch
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch = await service.create_batch(request)

    # Wait for completion
    for _ in range(50):
        await asyncio.sleep(0.1)
        updated_batch = await service.retrieve_batch(batch.id)
        if updated_batch.status == "completed":
            break

    # Get output file
    final_batch = await service.retrieve_batch(batch.id)
    output_content = service.batch_file_contents[final_batch.output_file_id]

    # Verify format
    lines = output_content.strip().split("\n")
    assert len(lines) == 1  # One request = one output line

    # Parse and verify structure
    output_obj = json.loads(lines[0])
    assert "id" in output_obj
    assert "custom_id" in output_obj
    assert output_obj["custom_id"] == "test-1"
    assert "response" in output_obj
    assert isinstance(output_obj["response"], dict)


@pytest.mark.asyncio
async def test_create_batch_with_invalid_file(service):
    """Test that creating a batch with invalid file ID fails."""
    request = CreateBatchRequest(
        input_file_id="file_nonexistent",
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    with pytest.raises(ValueError, match="Input file not found"):
        await service.create_batch(request)


@pytest.mark.asyncio
async def test_batch_expiration_time(service):
    """Test that batch expiration time is set correctly."""
    file_id = service.files[0].id

    # Create batch with 24h window
    request = CreateBatchRequest(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch = await service.create_batch(request)

    # Verify expiration is 24 hours from creation
    expected_expiration = batch.created_at + (24 * 3600)
    assert batch.expires_at == expected_expiration


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
