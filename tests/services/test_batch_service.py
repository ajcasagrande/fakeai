"""
Tests for batch service.

This module contains comprehensive tests for the BatchService class,
including batch creation, lifecycle management, request processing,
cancellation, error handling, and metrics integration.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock

import pytest

from fakeai.batch_metrics import BatchMetricsTracker
from fakeai.config import AppConfig
from fakeai.file_manager import FileManager, FileNotFoundError
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    BatchListResponse,
    ChatCompletionResponse,
    CreateBatchRequest,
    EmbeddingResponse,
)
from fakeai.models_registry.registry import ModelRegistry
from fakeai.services.batch_service import BatchService


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig(
        response_delay=0.0,  # No delay for tests
    )


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
        return ChatCompletionResponse(
            id="chatcmpl-123",
            model=request.model,
            choices=[],
            created=int(time.time()),
            object="chat.completion",
        )

    mock.create_chat_completion = AsyncMock(side_effect=mock_chat_completion)

    # Mock create_embedding
    async def mock_embedding(request):
        return EmbeddingResponse(
            data=[],
            model=request.model,
            object="list",
            usage={"prompt_tokens": 10, "total_tokens": 10},
        )

    mock.create_embedding = AsyncMock(side_effect=mock_embedding)

    return mock


class TestBatchServiceInit:
    """Tests for batch service initialization."""

    @pytest.mark.asyncio
    async def test_init(self, batch_service):
        """Test batch service initialization."""
        assert batch_service is not None
        assert batch_service.batches == {}
        assert batch_service._processing_tasks == {}
        assert batch_service._batch_file_contents == {}
        assert batch_service._parent_service is None

    @pytest.mark.asyncio
    async def test_set_parent_service(self, batch_service, parent_service_mock):
        """Test setting parent service."""
        batch_service.set_parent_service(parent_service_mock)
        assert batch_service._parent_service == parent_service_mock


class TestBatchCreation:
    """Tests for batch creation."""

    @pytest.mark.asyncio
    async def test_create_batch_success(self, batch_service, file_manager):
        """Test successful batch creation."""
        # Create input file
        input_file = await file_manager.upload_file(
            file_content=b'{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": []}}',
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        batch = await batch_service.create_batch(request)

        # Verify batch
        assert batch.id.startswith("batch_")
        assert batch.endpoint == "/v1/chat/completions"
        assert batch.input_file_id == input_file.id
        assert batch.status == "validating"
        assert batch.request_counts.total == 0
        assert batch.completion_window == "24h"

        # Verify batch is stored
        assert batch.id in batch_service.batches

        # Verify background task is created
        assert batch.id in batch_service._processing_tasks

    @pytest.mark.asyncio
    async def test_create_batch_file_not_found(self, batch_service):
        """Test batch creation with non-existent input file."""
        request = CreateBatchRequest(
            input_file_id="file-nonexistent",
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        with pytest.raises((ValueError, FileNotFoundError)):
            await batch_service.create_batch(request)

    @pytest.mark.asyncio
    async def test_create_batch_with_metadata(self, batch_service, file_manager):
        """Test batch creation with metadata."""
        # Create input file
        input_file = await file_manager.upload_file(
            file_content=b'{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": []}}',
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batch with metadata
        metadata = {"user_id": "user-123", "project": "test-project"}
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata=metadata,
        )

        batch = await batch_service.create_batch(request)

        # Verify metadata
        assert batch.metadata == metadata


class TestBatchRetrieval:
    """Tests for batch retrieval."""

    @pytest.mark.asyncio
    async def test_retrieve_batch_success(self, batch_service, file_manager):
        """Test successful batch retrieval."""
        # Create input file
        input_file = await file_manager.upload_file(
            file_content=b'{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": []}}',
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Retrieve batch
        retrieved = await batch_service.retrieve_batch(batch.id)

        # Verify
        assert retrieved.id == batch.id
        assert retrieved.endpoint == batch.endpoint

    @pytest.mark.asyncio
    async def test_retrieve_batch_not_found(self, batch_service):
        """Test batch retrieval with non-existent ID."""
        with pytest.raises(ValueError, match="Batch not found"):
            await batch_service.retrieve_batch("batch_nonexistent")


class TestBatchCancellation:
    """Tests for batch cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_batch_in_progress(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test cancelling a batch that is in progress."""
        # Set parent service
        batch_service.set_parent_service(parent_service_mock)

        # Create input file with sample data
        input_content = "\n".join(
            [
                json.dumps(
                    {
                        "custom_id": "req-1",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {"model": "gpt-3.5-turbo", "messages": []},
                    }
                ),
            ]
        )
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Wait a bit for processing to start
        await asyncio.sleep(0.1)

        # Cancel batch
        cancelled_batch = await batch_service.cancel_batch(batch.id)

        # Verify cancellation
        assert cancelled_batch.status == "cancelled"
        assert cancelled_batch.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_cancel_batch_not_found(self, batch_service):
        """Test cancelling non-existent batch."""
        with pytest.raises(ValueError, match="Batch not found"):
            await batch_service.cancel_batch("batch_nonexistent")

    @pytest.mark.asyncio
    async def test_cancel_completed_batch(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test that cancelling a completed batch does nothing."""
        # Set parent service
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

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Wait for completion
        await asyncio.sleep(1.0)

        # Try to cancel completed batch
        result = await batch_service.cancel_batch(batch.id)

        # Verify it stays completed
        assert result.status == "completed"


class TestBatchListing:
    """Tests for batch listing."""

    @pytest.mark.asyncio
    async def test_list_batches_empty(self, batch_service):
        """Test listing batches when none exist."""
        result = await batch_service.list_batches()

        assert isinstance(result, BatchListResponse)
        assert result.data == []
        assert result.has_more is False
        assert result.first_id is None
        assert result.last_id is None

    @pytest.mark.asyncio
    async def test_list_batches_multiple(self, batch_service, file_manager):
        """Test listing multiple batches."""
        # Create input file
        input_file = await file_manager.upload_file(
            file_content=b'{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": []}}',
            filename="input.jsonl",
            purpose="batch",
        )

        # Create multiple batches
        batches = []
        for i in range(3):
            request = CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            batch = await batch_service.create_batch(request)
            batches.append(batch)
            await asyncio.sleep(0.01)  # Ensure different timestamps

        # List batches
        result = await batch_service.list_batches()

        # Verify
        assert len(result.data) == 3
        assert result.has_more is False
        # Batches should be in reverse chronological order
        assert result.data[0].id == batches[-1].id
        assert result.data[-1].id == batches[0].id

    @pytest.mark.asyncio
    async def test_list_batches_with_limit(self, batch_service, file_manager):
        """Test listing batches with limit."""
        # Create input file
        input_file = await file_manager.upload_file(
            file_content=b'{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": []}}',
            filename="input.jsonl",
            purpose="batch",
        )

        # Create multiple batches
        for _ in range(5):
            request = CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            await batch_service.create_batch(request)
            await asyncio.sleep(0.01)

        # List with limit
        result = await batch_service.list_batches(limit=3)

        # Verify
        assert len(result.data) == 3
        assert result.has_more is True

    @pytest.mark.asyncio
    async def test_list_batches_with_pagination(self, batch_service, file_manager):
        """Test batch listing with pagination cursor."""
        # Create input file
        input_file = await file_manager.upload_file(
            file_content=b'{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": []}}',
            filename="input.jsonl",
            purpose="batch",
        )

        # Create multiple batches
        for _ in range(5):
            request = CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            await batch_service.create_batch(request)
            await asyncio.sleep(0.01)

        # Get first page
        page1 = await batch_service.list_batches(limit=2)
        assert len(page1.data) == 2

        # Get second page
        page2 = await batch_service.list_batches(limit=2, after=page1.last_id)
        assert len(page2.data) == 2
        # Verify no overlap
        page1_ids = {b.id for b in page1.data}
        page2_ids = {b.id for b in page2.data}
        assert len(page1_ids & page2_ids) == 0

    @pytest.mark.asyncio
    async def test_list_batches_invalid_limit(self, batch_service):
        """Test listing batches with invalid limit."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
            await batch_service.list_batches(limit=0)

        with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
            await batch_service.list_batches(limit=101)


class TestBatchProcessing:
    """Tests for batch processing."""

    @pytest.mark.asyncio
    async def test_process_batch_chat_completions(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test processing batch with chat completions."""
        # Set parent service
        batch_service.set_parent_service(parent_service_mock)

        # Create input file with chat completion requests
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
            for i in range(3)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Wait for processing to complete
        await asyncio.sleep(1.0)

        # Retrieve batch
        completed_batch = await batch_service.retrieve_batch(batch.id)

        # Verify completion
        assert completed_batch.status == "completed"
        assert completed_batch.request_counts.total == 3
        assert completed_batch.request_counts.completed == 3
        assert completed_batch.request_counts.failed == 0
        assert completed_batch.output_file_id is not None

    @pytest.mark.asyncio
    async def test_process_batch_embeddings(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test processing batch with embeddings."""
        # Set parent service
        batch_service.set_parent_service(parent_service_mock)

        # Create input file with embedding requests
        requests = [
            {
                "custom_id": f"req-{i}",
                "method": "POST",
                "url": "/v1/embeddings",
                "body": {"model": "text-embedding-ada-002", "input": f"Text {i}"},
            }
            for i in range(2)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/embeddings",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Wait for processing
        await asyncio.sleep(1.0)

        # Verify
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.request_counts.completed == 2


class TestBatchErrorHandling:
    """Tests for batch error handling."""

    @pytest.mark.asyncio
    async def test_process_batch_with_errors(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test batch processing with some failed requests."""
        # Set parent service
        batch_service.set_parent_service(parent_service_mock)

        # Mock to fail on second request
        call_count = [0]

        async def mock_chat_with_error(request):
            call_count[0] += 1
            if call_count[0] == 2:
                raise ValueError("Simulated error")
            return ChatCompletionResponse(
                id="chatcmpl-123",
                model=request.model,
                choices=[],
                created=int(time.time()),
                object="chat.completion",
            )

        parent_service_mock.create_chat_completion = AsyncMock(
            side_effect=mock_chat_with_error
        )

        # Create input file
        requests = [
            {
                "custom_id": f"req-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-3.5-turbo", "messages": []},
            }
            for i in range(3)
        ]
        input_content = "\n".join([json.dumps(req) for req in requests])
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Wait for processing
        await asyncio.sleep(1.0)

        # Verify
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        assert completed_batch.request_counts.total == 3
        assert completed_batch.request_counts.completed == 2
        assert completed_batch.request_counts.failed == 1
        assert completed_batch.error_file_id is not None

    @pytest.mark.asyncio
    async def test_process_batch_invalid_json(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test batch processing with invalid JSON input."""
        # Set parent service
        batch_service.set_parent_service(parent_service_mock)

        # Create input file with invalid JSON
        input_content = '{"custom_id": "req-1", "method": "POST"}\n{invalid json\n{"custom_id": "req-2", "method": "POST"}'
        input_file = await file_manager.upload_file(
            file_content=input_content.encode("utf-8"),
            filename="input.jsonl",
            purpose="batch",
        )

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Wait for processing
        await asyncio.sleep(1.0)

        # Verify - only valid lines are processed
        completed_batch = await batch_service.retrieve_batch(batch.id)
        assert completed_batch.status == "completed"
        # Should have 2 valid requests, invalid line is skipped
        assert completed_batch.request_counts.total == 2


class TestBatchMetricsIntegration:
    """Tests for batch metrics integration."""

    @pytest.mark.asyncio
    async def test_metrics_tracking(
        self, batch_service, file_manager, parent_service_mock, batch_metrics
    ):
        """Test that batch metrics are tracked correctly."""
        # Set parent service
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

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Wait for processing
        await asyncio.sleep(1.0)

        # Verify metrics
        stats = batch_service.get_batch_stats(batch.id)
        assert stats is not None
        assert stats["batch_id"] == batch.id
        assert stats["status"] == "completed"
        assert stats["requests"]["processed"] > 0

    @pytest.mark.asyncio
    async def test_aggregate_metrics(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test aggregate batch metrics."""
        # Set parent service
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

        # Create multiple batches
        for _ in range(2):
            request = CreateBatchRequest(
                input_file_id=input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            await batch_service.create_batch(request)

        # Wait for processing
        await asyncio.sleep(1.5)

        # Get aggregate stats
        all_stats = batch_service.get_all_batches_stats()
        assert all_stats is not None
        assert all_stats["summary"]["total_batches_completed"] == 2
        assert all_stats["summary"]["total_requests_processed"] > 0


class TestBatchFileOperations:
    """Tests for batch file operations."""

    @pytest.mark.asyncio
    async def test_get_batch_file_content(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test getting batch file content."""
        # Set parent service
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

        # Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)

        # Wait for processing
        await asyncio.sleep(1.0)

        # Get completed batch
        completed_batch = await batch_service.retrieve_batch(batch.id)

        # Get output file content
        output_content = batch_service.get_batch_file_content(
            completed_batch.output_file_id
        )
        assert output_content is not None
        assert len(output_content) > 0

        # Verify it's valid JSONL
        lines = output_content.strip().split("\n")
        for line in lines:
            data = json.loads(line)
            assert "id" in data
            assert "custom_id" in data
            assert "response" in data or "error" in data


class TestBatchLifecycle:
    """Tests for complete batch lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_batch_lifecycle(
        self, batch_service, file_manager, parent_service_mock
    ):
        """Test complete batch lifecycle from creation to completion."""
        # Set parent service
        batch_service.set_parent_service(parent_service_mock)

        # Create input file
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

        # 1. Create batch
        request = CreateBatchRequest(
            input_file_id=input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch = await batch_service.create_batch(request)
        assert batch.status == "validating"

        # 2. Check early status (should be in progress or validating)
        await asyncio.sleep(0.2)
        early_batch = await batch_service.retrieve_batch(batch.id)
        assert early_batch.status in ["validating", "in_progress", "finalizing"]

        # 3. Wait for completion
        await asyncio.sleep(1.0)

        # 4. Verify final state
        final_batch = await batch_service.retrieve_batch(batch.id)
        assert final_batch.status == "completed"
        assert final_batch.completed_at is not None
        assert final_batch.request_counts.total == 3
        assert final_batch.request_counts.completed == 3
        assert final_batch.output_file_id is not None

        # 5. Verify output file exists and has content
        output_content = batch_service.get_batch_file_content(
            final_batch.output_file_id
        )
        assert output_content is not None
        output_lines = output_content.strip().split("\n")
        assert len(output_lines) == 3

        # 6. Verify each output line is valid
        for line in output_lines:
            data = json.loads(line)
            assert data["custom_id"].startswith("req-")
            assert data["response"] is not None
