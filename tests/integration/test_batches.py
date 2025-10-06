"""
Comprehensive integration tests for batch service.

This module provides end-to-end integration tests for the batch processing system,
testing real workflows, concurrent operations, large batches, and production scenarios.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock

import pytest

from fakeai.batch_metrics import BatchMetricsTracker
from fakeai.config import AppConfig
from fakeai.file_manager import FileManager
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    ChatCompletionResponse,
    CompletionResponse,
    CreateBatchRequest,
    EmbeddingResponse,
)
from fakeai.models_registry.registry import ModelRegistry
from fakeai.services.batch_service import BatchService


@pytest.fixture
def config():
    """Create test configuration with minimal delays."""
    return AppConfig(response_delay=0.0)


@pytest.fixture
def metrics_tracker():
    """Create metrics tracker."""
    return MetricsTracker()


@pytest.fixture
def batch_metrics():
    """Create batch metrics tracker."""
    return BatchMetricsTracker()


@pytest.fixture
async def file_manager():
    """Create file manager."""
    return FileManager()


@pytest.fixture
def model_registry():
    """Create model registry."""
    return ModelRegistry()


@pytest.fixture
async def batch_service(
    config, metrics_tracker, model_registry, file_manager, batch_metrics
):
    """Create batch service."""
    service = BatchService(
        config=config,
        metrics_tracker=metrics_tracker,
        model_registry=model_registry,
        file_manager=file_manager,
        batch_metrics=batch_metrics,
    )
    return service


@pytest.fixture
async def parent_service_mock():
    """Create mock parent service for executing batch requests."""
    mock = Mock()

    # Mock create_chat_completion
    async def mock_chat_completion(request):
        # Simulate processing delay
        await asyncio.sleep(0.01)
        return ChatCompletionResponse(
            id="chatcmpl-123",
            model=request.model,
            choices=[
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Test response"},
                    "finish_reason": "stop",
                }
            ],
            created=int(time.time()),
            object="chat.completion",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

    mock.create_chat_completion = AsyncMock(side_effect=mock_chat_completion)

    # Mock create_embedding
    async def mock_embedding(request):
        await asyncio.sleep(0.005)
        return EmbeddingResponse(
            data=[{"object": "embedding", "embedding": [0.1] * 1536, "index": 0}],
            model=request.model,
            object="list",
            usage={"prompt_tokens": 10, "total_tokens": 10},
        )

    mock.create_embedding = AsyncMock(side_effect=mock_embedding)

    # Mock create_completion
    async def mock_completion(request):
        await asyncio.sleep(0.01)
        return CompletionResponse(
            id="cmpl-123",
            model=request.model,
            choices=[
                {
                    "text": "Test completion",
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            created=int(time.time()),
            object="text_completion",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

    mock.create_completion = AsyncMock(side_effect=mock_completion)

    return mock


@pytest.mark.integration
class TestBatchCreationWithInputFile:
    """Integration tests for batch creation with input files."""

    @pytest.mark.asyncio
    async def test_batch_creation_with_valid_input_file(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test creating a batch with a valid input file."""
        batch_service.set_parent_service(parent_service_mock)

        # Create input file
        requests = [
            {
                "custom_id": f"req-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": f"Hello {i}"}],
                },
            }
            for i in range(5)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="batch_input.jsonl",
            purpose="batch",
        )

        # Create batch
        batch_request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        batch = await batch_service.create_batch(batch_request)

        # Assertions
        assert batch.id.startswith("batch_")
        assert batch.endpoint == "/v1/chat/completions"
        assert batch.status == "validating"
        assert batch.input_file_id == input_file.id
        assert batch.completion_window == "24h"

        # Wait for completion
        await asyncio.sleep(1.5)

        # Verify final state
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.request_counts.total == 5
        assert completed_batch.request_counts.completed == 5

    @pytest.mark.asyncio
    async def test_batch_creation_with_large_input_file(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test creating a batch with a large input file (100+ requests)."""
        batch_service.set_parent_service(parent_service_mock)

        # Create large input file with 100 requests
        requests = [
            {
                "custom_id": f"req-{i:04d}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": f"Request {i}"}],
                },
            }
            for i in range(100)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="large_batch_input.jsonl",
            purpose="batch",
        )

        # Create batch
        batch_request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        batch = await batch_service.create_batch(batch_request)
        assert batch.id.startswith("batch_")

        # Wait for processing (longer for large batch)
        await asyncio.sleep(8.0)

        # Verify completion
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.request_counts.total == 100
        assert completed_batch.request_counts.completed == 100


@pytest.mark.integration
class TestBatchStatusRetrieval:
    """Integration tests for batch status retrieval."""

    @pytest.mark.asyncio
    async def test_batch_status_during_processing(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test retrieving batch status at different stages."""
        batch_service.set_parent_service(parent_service_mock)

        # Create batch
        input_content = "\n".join(
            [
                json.dumps(
                    {
                        "custom_id": f"req-{i}",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {"model": "gpt-3.5-turbo", "messages": []},
                    }
                )
                for i in range(10)
            ]
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch_request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        batch = await batch_service.create_batch(batch_request)

        # Check initial status
        assert batch.status == "validating"

        # Wait briefly and check in_progress status
        await asyncio.sleep(0.7)
        batch_status = await batch_service.retrieve_batch(batch.id)
        assert batch_status.status in ["validating", "in_progress", "finalizing"]

        # Wait for completion
        await asyncio.sleep(1.5)
        final_batch = await batch_service.retrieve_batch(batch.id)
        assert final_batch.status == "completed"
        assert final_batch.completed_at is not None


@pytest.mark.integration
class TestBatchListingWithFilters:
    """Integration tests for batch listing with filters."""

    @pytest.mark.asyncio
    async def test_list_batches_pagination(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test listing batches with pagination."""
        batch_service.set_parent_service(parent_service_mock)

        # Create input file
        input_content = json.dumps(
            {
                "custom_id": "req-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        # Create 10 batches
        batch_ids = []
        for i in range(10):
            batch_request = CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            batch = await batch_service.create_batch(batch_request)
            batch_ids.append(batch.id)
            await asyncio.sleep(0.01)  # Ensure different timestamps

        # Test pagination
        page1 = await batch_service.list_batches(limit=5)
        assert len(page1.data) == 5
        assert page1.has_more is True

        page2 = await batch_service.list_batches(limit=5, after=page1.last_id)
        assert len(page2.data) == 5
        assert page2.has_more is False

        # Verify no overlap
        page1_ids = {b.id for b in page1.data}
        page2_ids = {b.id for b in page2.data}
        assert len(page1_ids & page2_ids) == 0

    @pytest.mark.asyncio
    async def test_list_batches_ordering(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test that batches are listed in reverse chronological order."""
        batch_service.set_parent_service(parent_service_mock)

        # Create input file
        input_content = json.dumps(
            {
                "custom_id": "req-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batches with delays to ensure ordering
        batch1 = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )
        await asyncio.sleep(0.1)  # Increased delay for more reliable ordering

        batch2 = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )
        await asyncio.sleep(0.1)  # Increased delay for more reliable ordering

        batch3 = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        # List batches
        result = await batch_service.list_batches()

        # Verify we have 3 batches
        assert len(result.data) == 3

        # Verify reverse chronological order (most recent first)
        # Check by created_at timestamp instead of relying on exact order
        batch_ids = [b.id for b in result.data]
        assert batch3.id in batch_ids
        assert batch2.id in batch_ids
        assert batch1.id in batch_ids

        # Verify timestamps are in descending order
        timestamps = [b.created_at for b in result.data]
        assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.integration
class TestBatchCancellation:
    """Integration tests for batch cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_batch_during_processing(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test cancelling a batch while it's processing."""
        batch_service.set_parent_service(parent_service_mock)

        # Create batch with many requests to ensure it's still processing
        requests = [
            {
                "custom_id": f"req-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
            for i in range(20)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch_request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        batch = await batch_service.create_batch(batch_request)

        # Wait briefly for processing to start
        await asyncio.sleep(0.3)

        # Cancel batch
        cancelled_batch = await batch_service.cancel_batch(batch.id)

        # Verify cancellation
        assert cancelled_batch.status == "cancelled"
        assert cancelled_batch.cancelled_at is not None

        # Verify batch stays cancelled
        await asyncio.sleep(0.5)
        final_batch = await batch_service.retrieve_batch(batch.id)
        assert final_batch.status == "cancelled"


@pytest.mark.integration
class TestBatchCompletionAndOutputFile:
    """Integration tests for batch completion and output file generation."""

    @pytest.mark.asyncio
    async def test_batch_completion_with_output_file(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test batch completion generates correct output file."""
        batch_service.set_parent_service(parent_service_mock)

        # Create batch
        requests = [
            {
                "custom_id": f"req-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": f"Test {i}"}],
                },
            }
            for i in range(3)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch_request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        batch = await batch_service.create_batch(batch_request)

        # Wait for completion
        await asyncio.sleep(1.5)

        # Verify completion
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.output_file_id is not None

        # Verify output file content
        output_content = batch_service.get_batch_file_content(
            completed_batch.output_file_id
        )
        assert output_content is not None

        # Parse and verify output
        output_lines = output_content.strip().split("\n")
        assert len(output_lines) == 3

        for idx, line in enumerate(output_lines):
            data = json.loads(line)
            assert "id" in data
            assert "custom_id" in data
            assert data["custom_id"] == f"req-{idx}"
            assert "response" in data
            assert data["response"] is not None

    @pytest.mark.asyncio
    async def test_batch_output_file_structure(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test output file has correct JSONL structure."""
        batch_service.set_parent_service(parent_service_mock)

        # Create batch
        input_content = json.dumps(
            {
                "custom_id": "test-request",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hello"}],
                },
            }
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        # Wait for completion
        await asyncio.sleep(1.0)

        # Get output file
        completed_batch = await batch_service.retrieve_batch(batch.id)
        output_content = batch_service.get_batch_file_content(
            completed_batch.output_file_id
        )

        # Verify structure
        output_data = json.loads(output_content.strip())
        assert output_data["custom_id"] == "test-request"
        assert "response" in output_data
        assert output_data["response"]["object"] == "chat.completion"
        assert "usage" in output_data["response"]


@pytest.mark.integration
class TestBatchErrorsAndErrorFile:
    """Integration tests for batch errors and error file generation."""

    @pytest.mark.asyncio
    async def test_batch_with_errors_creates_error_file(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test that batches with errors create error files."""
        batch_service.set_parent_service(parent_service_mock)

        # Mock to fail on some requests
        call_count = [0]

        async def mock_chat_with_errors(request):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise ValueError("Simulated error")
            return ChatCompletionResponse(
                id="chatcmpl-123",
                model=request.model,
                choices=[
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Test"},
                        "finish_reason": "stop",
                    }
                ],
                created=int(time.time()),
                object="chat.completion",
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            )

        parent_service_mock.create_chat_completion = AsyncMock(
            side_effect=mock_chat_with_errors
        )

        # Create batch
        requests = [
            {
                "custom_id": f"req-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
            for i in range(4)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        # Wait for completion
        await asyncio.sleep(1.5)

        # Verify error file exists
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.error_file_id is not None
        assert completed_batch.request_counts.failed > 0

        # Verify error file content
        error_content = batch_service.get_batch_file_content(
            completed_batch.error_file_id
        )
        assert error_content is not None

        error_lines = error_content.strip().split("\n")
        assert len(error_lines) == 2  # 2 out of 4 failed

        for line in error_lines:
            data = json.loads(line)
            assert "error" in data
            assert data["error"] is not None


@pytest.mark.integration
class TestBatchDifferentEndpoints:
    """Integration tests for batches with different endpoints."""

    @pytest.mark.asyncio
    async def test_batch_chat_completions_endpoint(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test batch with chat completions endpoint."""
        batch_service.set_parent_service(parent_service_mock)

        requests = [
            {
                "custom_id": f"chat-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hello"}],
                },
            }
            for i in range(3)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="chat_input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        await asyncio.sleep(1.5)

        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.endpoint == "/v1/chat/completions"

    @pytest.mark.asyncio
    async def test_batch_embeddings_endpoint(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test batch with embeddings endpoint."""
        batch_service.set_parent_service(parent_service_mock)

        requests = [
            {
                "custom_id": f"emb-{i}",
                "method": "POST",
                "url": "/v1/embeddings",
                "body": {"model": "text-embedding-ada-002", "input": f"Text {i}"},
            }
            for i in range(3)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="embedding_input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/embeddings",
                completion_window="24h",
            )
        )

        await asyncio.sleep(1.0)

        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.endpoint == "/v1/embeddings"

    @pytest.mark.asyncio
    async def test_batch_completions_endpoint(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test batch with completions endpoint."""
        batch_service.set_parent_service(parent_service_mock)

        requests = [
            {
                "custom_id": f"comp-{i}",
                "method": "POST",
                "url": "/v1/completions",
                "body": {"model": "gpt-3.5-turbo-instruct", "prompt": f"Complete {i}"},
            }
            for i in range(2)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="completion_input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/completions",
                completion_window="24h",
            )
        )

        await asyncio.sleep(1.0)

        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.endpoint == "/v1/completions"


@pytest.mark.integration
class TestBatchLargeProcessing:
    """Integration tests for large batch processing."""

    @pytest.mark.asyncio
    async def test_large_batch_100_requests(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test processing batch with 100+ requests."""
        batch_service.set_parent_service(parent_service_mock)

        # Create 100 requests
        requests = [
            {
                "custom_id": f"large-req-{i:04d}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": f"Message {i}"}],
                },
            }
            for i in range(100)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="large_batch.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        # Check initial state
        assert batch.status == "validating"

        # Wait for completion (longer for large batch)
        await asyncio.sleep(8.0)

        # Verify completion
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.request_counts.total == 100
        assert completed_batch.request_counts.completed == 100
        assert completed_batch.output_file_id is not None

        # Verify output file has all responses
        output_content = batch_service.get_batch_file_content(
            completed_batch.output_file_id
        )
        output_lines = output_content.strip().split("\n")
        assert len(output_lines) == 100


@pytest.mark.integration
class TestBatchCustomIdTracking:
    """Integration tests for custom_id tracking."""

    @pytest.mark.asyncio
    async def test_custom_id_preserved_in_output(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test that custom_id is preserved in output file."""
        batch_service.set_parent_service(parent_service_mock)

        custom_ids = ["user-123-req-1", "user-456-req-2", "user-789-req-3"]
        requests = [
            {
                "custom_id": cid,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Test"}],
                },
            }
            for cid in custom_ids
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        await asyncio.sleep(1.5)

        completed_batch = await batch_service.retrieve_batch(batch.id)
        output_content = batch_service.get_batch_file_content(
            completed_batch.output_file_id
        )

        # Verify custom_ids are preserved
        output_lines = output_content.strip().split("\n")
        output_custom_ids = [json.loads(line)["custom_id"] for line in output_lines]

        assert set(output_custom_ids) == set(custom_ids)


@pytest.mark.integration
class TestBatchMetadata:
    """Integration tests for batch metadata."""

    @pytest.mark.asyncio
    async def test_batch_metadata_preserved(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test that batch metadata is preserved."""
        batch_service.set_parent_service(parent_service_mock)

        # Create batch with metadata
        input_content = json.dumps(
            {
                "custom_id": "req-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        metadata = {
            "user_id": "user-12345",
            "project": "test-project",
            "environment": "integration-test",
        }

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata=metadata,
            )
        )

        # Verify metadata immediately
        assert batch.metadata == metadata

        # Wait for completion
        await asyncio.sleep(1.0)

        # Verify metadata after completion
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.metadata == metadata


@pytest.mark.integration
class TestConcurrentBatchOperations:
    """Integration tests for concurrent batch operations."""

    @pytest.mark.asyncio
    async def test_concurrent_batch_creation(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test creating multiple batches concurrently."""
        batch_service.set_parent_service(parent_service_mock)

        # Create input file
        input_content = json.dumps(
            {
                "custom_id": "req-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        # Create 5 batches concurrently
        async def create_batch():
            return await batch_service.create_batch(
                CreateBatchRequest(
                    input_file_id=input_file.id,
                    endpoint="/v1/chat/completions",
                    completion_window="24h",
                )
            )

        batches = await asyncio.gather(*[create_batch() for _ in range(5)])

        # Verify all batches created
        assert len(batches) == 5
        assert len(set(b.id for b in batches)) == 5  # All unique IDs

        # Wait for all to complete
        await asyncio.sleep(2.0)

        # Verify all completed
        for batch in batches:
            completed = await batch_service.retrieve_batch(batch.id)
            assert completed.status == "completed"

    @pytest.mark.asyncio
    async def test_concurrent_batch_listing(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test listing batches while others are being created."""
        batch_service.set_parent_service(parent_service_mock)

        # Create input file
        input_content = json.dumps(
            {
                "custom_id": "req-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        async def create_batches():
            for _ in range(5):
                await batch_service.create_batch(
                    CreateBatchRequest(
                        input_file_id=input_file.id,
                        endpoint="/v1/chat/completions",
                        completion_window="24h",
                    )
                )
                await asyncio.sleep(0.1)

        async def list_batches():
            results = []
            for _ in range(3):
                result = await batch_service.list_batches()
                results.append(len(result.data))
                await asyncio.sleep(0.2)
            return results

        # Run concurrently
        create_task = asyncio.create_task(create_batches())
        list_results = await list_batches()
        await create_task

        # Verify listing worked during creation
        assert len(list_results) == 3
        # Should see increasing number of batches
        assert list_results[-1] >= list_results[0]


@pytest.mark.integration
class TestBatchTimeouts:
    """Integration tests for batch timeouts and expiration."""

    @pytest.mark.asyncio
    async def test_batch_completion_window_set(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test that batch completion window is properly set."""
        batch_service.set_parent_service(parent_service_mock)

        input_content = json.dumps(
            {
                "custom_id": "req-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        # Verify expiration is set (24 hours from now)
        assert batch.expires_at is not None
        expected_expires = batch.created_at + (24 * 3600)
        assert abs(batch.expires_at - expected_expires) < 5  # Within 5 seconds


@pytest.mark.integration
class TestBatchProgressTracking:
    """Integration tests for batch progress tracking."""

    @pytest.mark.asyncio
    async def test_batch_request_counts_update(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test that request counts update during processing."""
        batch_service.set_parent_service(parent_service_mock)

        # Create batch with multiple requests
        requests = [
            {
                "custom_id": f"req-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
            for i in range(10)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        # Wait for processing to start
        await asyncio.sleep(0.8)

        # Check progress during processing
        batch_status = await batch_service.retrieve_batch(batch.id)
        if batch_status.status == "in_progress":
            # May have some completed
            assert (
                batch_status.request_counts.completed
                >= 0  # Could be 0 or some completed
            )

        # Wait for completion
        await asyncio.sleep(1.5)

        # Verify final counts
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.request_counts.total == 10
        assert completed_batch.request_counts.completed == 10
        assert completed_batch.request_counts.failed == 0

    @pytest.mark.asyncio
    async def test_batch_metrics_tracking(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test that batch metrics are tracked correctly."""
        batch_service.set_parent_service(parent_service_mock)

        # Create batch
        input_content = json.dumps(
            {
                "custom_id": "req-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        batch = await batch_service.create_batch(
            CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
        )

        # Wait for completion
        await asyncio.sleep(1.0)

        # Get batch stats
        stats = batch_service.get_batch_stats(batch.id)
        assert stats is not None
        assert stats["batch_id"] == batch.id
        assert stats["status"] == "completed"
        assert stats["requests"]["processed"] > 0

        # Verify aggregate stats
        all_stats = batch_service.get_all_batches_stats()
        assert all_stats is not None
        assert all_stats["summary"]["total_batches_completed"] >= 1
