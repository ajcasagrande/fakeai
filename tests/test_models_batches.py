"""
Tests for batch processing models.

This test suite verifies the batch processing models in fakeai.models.batches:
- BatchRequestCounts: Request count tracking
- Batch: Main batch object with lifecycle states
- CreateBatchRequest: Batch creation request
- BatchListResponse: Batch listing response
- BatchRequest: Individual batch request
- BatchOutputResponse: Individual batch output response

Tests cover:
- Model instantiation and validation
- Lifecycle state transitions
- Request count tracking
- Timestamp management
- Error handling
- JSONL file format compatibility
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError


class TestImportsFromBatchesModule:
    """Test that all batch models can be imported from the batches module."""

    def test_import_from_batches_module(self):
        """Test importing from fakeai.models.batches module."""
        from fakeai.models.batches import (
            Batch,
            BatchListResponse,
            BatchOutputResponse,
            BatchRequest,
            BatchRequestCounts,
            CreateBatchRequest,
        )

        # Verify classes are imported correctly
        assert BatchRequestCounts is not None
        assert Batch is not None
        assert CreateBatchRequest is not None
        assert BatchListResponse is not None
        assert BatchRequest is not None
        assert BatchOutputResponse is not None

    def test_import_from_models_package(self):
        """Test importing batch models from fakeai.models package."""
        from fakeai.models import (
            Batch,
            BatchListResponse,
            BatchOutputResponse,
            BatchRequest,
            BatchRequestCounts,
            CreateBatchRequest,
        )

        # Verify classes are imported correctly
        assert BatchRequestCounts is not None
        assert Batch is not None
        assert CreateBatchRequest is not None
        assert BatchListResponse is not None
        assert BatchRequest is not None
        assert BatchOutputResponse is not None


class TestBackwardCompatibility:
    """Test that imports from different paths reference the same classes."""

    def test_batch_models_reference_same_class(self):
        """Test that batch models imported from different paths are the same class."""
        from fakeai.models import Batch as BatchFromPackage
        from fakeai.models.batches import Batch as BatchFromBatches

        # Verify they reference the same class
        assert BatchFromPackage is BatchFromBatches

    def test_all_batch_models_reference_same_class(self):
        """Test that all batch models reference the same classes."""
        from fakeai.models import (
            Batch,
            BatchListResponse,
            BatchOutputResponse,
            BatchRequest,
            BatchRequestCounts,
            CreateBatchRequest,
        )
        from fakeai.models.batches import Batch as BatchBase
        from fakeai.models.batches import BatchListResponse as BatchListResponseBase
        from fakeai.models.batches import BatchOutputResponse as BatchOutputResponseBase
        from fakeai.models.batches import BatchRequest as BatchRequestBase
        from fakeai.models.batches import BatchRequestCounts as BatchRequestCountsBase
        from fakeai.models.batches import CreateBatchRequest as CreateBatchRequestBase

        # Verify all classes reference the same objects
        assert BatchRequestCounts is BatchRequestCountsBase
        assert Batch is BatchBase
        assert CreateBatchRequest is CreateBatchRequestBase
        assert BatchListResponse is BatchListResponseBase
        assert BatchRequest is BatchRequestBase
        assert BatchOutputResponse is BatchOutputResponseBase


class TestBatchRequestCounts:
    """Test BatchRequestCounts model."""

    def test_batch_request_counts_creation(self):
        """Test creating a BatchRequestCounts object."""
        from fakeai.models import BatchRequestCounts

        counts = BatchRequestCounts(total=100, completed=75, failed=5)

        assert counts.total == 100
        assert counts.completed == 75
        assert counts.failed == 5

    def test_batch_request_counts_defaults(self):
        """Test BatchRequestCounts with default values."""
        from fakeai.models import BatchRequestCounts

        counts = BatchRequestCounts(total=50)

        assert counts.total == 50
        assert counts.completed == 0
        assert counts.failed == 0

    def test_batch_request_counts_validation(self):
        """Test BatchRequestCounts validation."""
        from fakeai.models import BatchRequestCounts

        # Missing required field should raise ValidationError
        with pytest.raises(ValidationError):
            BatchRequestCounts(completed=10, failed=5)

        # Invalid type should raise ValidationError
        with pytest.raises(ValidationError):
            BatchRequestCounts(total="invalid", completed=10)


class TestBatch:
    """Test Batch model."""

    def test_batch_creation(self):
        """Test creating a Batch object."""
        from fakeai.models import Batch, BatchRequestCounts

        counts = BatchRequestCounts(total=10, completed=8, failed=2)
        batch = Batch(
            id="batch_abc123",
            endpoint="/v1/chat/completions",
            input_file_id="file-abc123",
            completion_window="24h",
            status="completed",
            created_at=1234567890,
            request_counts=counts,
        )

        assert batch.id == "batch_abc123"
        assert batch.object == "batch"
        assert batch.endpoint == "/v1/chat/completions"
        assert batch.input_file_id == "file-abc123"
        assert batch.completion_window == "24h"
        assert batch.status == "completed"
        assert batch.created_at == 1234567890
        assert batch.request_counts.total == 10
        assert batch.request_counts.completed == 8
        assert batch.request_counts.failed == 2

    def test_batch_with_all_timestamps(self):
        """Test Batch with all lifecycle timestamps."""
        from fakeai.models import Batch, BatchRequestCounts

        counts = BatchRequestCounts(total=5, completed=5)
        batch = Batch(
            id="batch_xyz789",
            endpoint="/v1/chat/completions",
            input_file_id="file-xyz789",
            completion_window="24h",
            status="completed",
            created_at=1000,
            in_progress_at=1100,
            finalizing_at=1200,
            completed_at=1300,
            output_file_id="file-output-xyz789",
            request_counts=counts,
        )

        assert batch.created_at == 1000
        assert batch.in_progress_at == 1100
        assert batch.finalizing_at == 1200
        assert batch.completed_at == 1300
        assert batch.output_file_id == "file-output-xyz789"

    def test_batch_states(self):
        """Test all valid batch states."""
        from fakeai.models import Batch, BatchRequestCounts

        valid_states = [
            "validating",
            "failed",
            "in_progress",
            "finalizing",
            "completed",
            "expired",
            "cancelling",
            "cancelled",
        ]

        counts = BatchRequestCounts(total=1)
        for state in valid_states:
            batch = Batch(
                id=f"batch_{state}",
                endpoint="/v1/chat/completions",
                input_file_id="file-123",
                completion_window="24h",
                status=state,
                created_at=1234567890,
                request_counts=counts,
            )
            assert batch.status == state

    def test_batch_with_errors(self):
        """Test Batch with error information."""
        from fakeai.models import Batch, BatchRequestCounts

        error_info = {
            "object": "error",
            "message": "Validation failed",
            "type": "invalid_request_error",
            "code": "invalid_input",
        }

        counts = BatchRequestCounts(total=10, failed=10)
        batch = Batch(
            id="batch_error",
            endpoint="/v1/chat/completions",
            input_file_id="file-error",
            completion_window="24h",
            status="failed",
            created_at=1234567890,
            failed_at=1234567900,
            errors=error_info,
            error_file_id="file-errors-123",
            request_counts=counts,
        )

        assert batch.status == "failed"
        assert batch.errors is not None
        assert batch.errors["message"] == "Validation failed"
        assert batch.error_file_id == "file-errors-123"
        assert batch.failed_at == 1234567900

    def test_batch_with_metadata(self):
        """Test Batch with metadata."""
        from fakeai.models import Batch, BatchRequestCounts

        metadata = {"user_id": "user123", "project": "test-project", "version": "1.0"}

        counts = BatchRequestCounts(total=5)
        batch = Batch(
            id="batch_meta",
            endpoint="/v1/chat/completions",
            input_file_id="file-meta",
            completion_window="24h",
            status="in_progress",
            created_at=1234567890,
            request_counts=counts,
            metadata=metadata,
        )

        assert batch.metadata is not None
        assert batch.metadata["user_id"] == "user123"
        assert batch.metadata["project"] == "test-project"

    def test_batch_validation(self):
        """Test Batch validation."""
        from fakeai.models import Batch, BatchRequestCounts

        counts = BatchRequestCounts(total=1)

        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            Batch(endpoint="/v1/chat/completions", status="in_progress")

        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            Batch(
                id="batch_invalid",
                endpoint="/v1/chat/completions",
                input_file_id="file-123",
                completion_window="24h",
                status="invalid_status",
                created_at=1234567890,
                request_counts=counts,
            )

    def test_batch_cancelled_state(self):
        """Test Batch in cancelled state with timestamps."""
        from fakeai.models import Batch, BatchRequestCounts

        counts = BatchRequestCounts(total=100, completed=50)
        batch = Batch(
            id="batch_cancel",
            endpoint="/v1/chat/completions",
            input_file_id="file-cancel",
            completion_window="24h",
            status="cancelled",
            created_at=1000,
            in_progress_at=1100,
            cancelling_at=1200,
            cancelled_at=1250,
            request_counts=counts,
        )

        assert batch.status == "cancelled"
        assert batch.cancelling_at == 1200
        assert batch.cancelled_at == 1250
        assert batch.request_counts.completed == 50

    def test_batch_expired_state(self):
        """Test Batch in expired state."""
        from fakeai.models import Batch, BatchRequestCounts

        counts = BatchRequestCounts(total=10, completed=5)
        batch = Batch(
            id="batch_expired",
            endpoint="/v1/chat/completions",
            input_file_id="file-expired",
            completion_window="24h",
            status="expired",
            created_at=1000,
            expires_at=1500,
            expired_at=1600,
            request_counts=counts,
        )

        assert batch.status == "expired"
        assert batch.expires_at == 1500
        assert batch.expired_at == 1600


class TestCreateBatchRequest:
    """Test CreateBatchRequest model."""

    def test_create_batch_request_creation(self):
        """Test creating a CreateBatchRequest object."""
        from fakeai.models import CreateBatchRequest

        request = CreateBatchRequest(
            input_file_id="file-abc123",
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        assert request.input_file_id == "file-abc123"
        assert request.endpoint == "/v1/chat/completions"
        assert request.completion_window == "24h"
        assert request.metadata is None

    def test_create_batch_request_with_metadata(self):
        """Test CreateBatchRequest with metadata."""
        from fakeai.models import CreateBatchRequest

        metadata = {"user_id": "user123", "experiment": "test-exp"}
        request = CreateBatchRequest(
            input_file_id="file-xyz789",
            endpoint="/v1/embeddings",
            completion_window="24h",
            metadata=metadata,
        )

        assert request.metadata is not None
        assert request.metadata["user_id"] == "user123"
        assert request.metadata["experiment"] == "test-exp"

    def test_create_batch_request_validation(self):
        """Test CreateBatchRequest validation."""
        from fakeai.models import CreateBatchRequest

        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            CreateBatchRequest(endpoint="/v1/chat/completions")

        with pytest.raises(ValidationError):
            CreateBatchRequest(input_file_id="file-123")


class TestBatchListResponse:
    """Test BatchListResponse model."""

    def test_batch_list_response_creation(self):
        """Test creating a BatchListResponse object."""
        from fakeai.models import Batch, BatchListResponse, BatchRequestCounts

        counts1 = BatchRequestCounts(total=10, completed=10)
        batch1 = Batch(
            id="batch_1",
            endpoint="/v1/chat/completions",
            input_file_id="file-1",
            completion_window="24h",
            status="completed",
            created_at=1000,
            request_counts=counts1,
        )

        counts2 = BatchRequestCounts(total=5, completed=3)
        batch2 = Batch(
            id="batch_2",
            endpoint="/v1/embeddings",
            input_file_id="file-2",
            completion_window="24h",
            status="in_progress",
            created_at=2000,
            request_counts=counts2,
        )

        response = BatchListResponse(
            data=[batch1, batch2],
            first_id="batch_1",
            last_id="batch_2",
            has_more=False,
        )

        assert response.object == "list"
        assert len(response.data) == 2
        assert response.data[0].id == "batch_1"
        assert response.data[1].id == "batch_2"
        assert response.first_id == "batch_1"
        assert response.last_id == "batch_2"
        assert response.has_more is False

    def test_batch_list_response_empty(self):
        """Test BatchListResponse with empty data."""
        from fakeai.models import BatchListResponse

        response = BatchListResponse(data=[])

        assert response.object == "list"
        assert len(response.data) == 0
        assert response.first_id is None
        assert response.last_id is None
        assert response.has_more is False

    def test_batch_list_response_with_pagination(self):
        """Test BatchListResponse with pagination."""
        from fakeai.models import Batch, BatchListResponse, BatchRequestCounts

        batches = []
        for i in range(20):
            counts = BatchRequestCounts(total=i + 1)
            batch = Batch(
                id=f"batch_{i}",
                endpoint="/v1/chat/completions",
                input_file_id=f"file-{i}",
                completion_window="24h",
                status="completed",
                created_at=1000 + i,
                request_counts=counts,
            )
            batches.append(batch)

        response = BatchListResponse(
            data=batches[:10],
            first_id="batch_0",
            last_id="batch_9",
            has_more=True,
        )

        assert len(response.data) == 10
        assert response.has_more is True


class TestBatchRequest:
    """Test BatchRequest model."""

    def test_batch_request_creation(self):
        """Test creating a BatchRequest object."""
        from fakeai.models import BatchRequest

        body = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100,
        }

        request = BatchRequest(
            custom_id="request-1",
            method="POST",
            url="/v1/chat/completions",
            body=body,
        )

        assert request.custom_id == "request-1"
        assert request.method == "POST"
        assert request.url == "/v1/chat/completions"
        assert request.body["model"] == "gpt-4"
        assert request.body["messages"][0]["content"] == "Hello"

    def test_batch_request_embeddings(self):
        """Test BatchRequest for embeddings endpoint."""
        from fakeai.models import BatchRequest

        body = {
            "model": "text-embedding-ada-002",
            "input": "Sample text to embed",
        }

        request = BatchRequest(
            custom_id="embed-1",
            method="POST",
            url="/v1/embeddings",
            body=body,
        )

        assert request.custom_id == "embed-1"
        assert request.url == "/v1/embeddings"
        assert request.body["model"] == "text-embedding-ada-002"

    def test_batch_request_validation(self):
        """Test BatchRequest validation."""
        from fakeai.models import BatchRequest

        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            BatchRequest(custom_id="req-1", method="POST")

        # Invalid method should raise ValidationError (only POST allowed)
        with pytest.raises(ValidationError):
            BatchRequest(
                custom_id="req-1",
                method="GET",
                url="/v1/chat/completions",
                body={},
            )


class TestBatchOutputResponse:
    """Test BatchOutputResponse model."""

    def test_batch_output_response_success(self):
        """Test creating a successful BatchOutputResponse object."""
        from fakeai.models import BatchOutputResponse

        response_data = {
            "id": "chatcmpl-abc123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help?",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }

        output = BatchOutputResponse(
            id="batch_req_abc123",
            custom_id="request-1",
            response=response_data,
        )

        assert output.id == "batch_req_abc123"
        assert output.custom_id == "request-1"
        assert output.response is not None
        assert output.response["model"] == "gpt-4"
        assert output.error is None

    def test_batch_output_response_error(self):
        """Test creating a failed BatchOutputResponse object."""
        from fakeai.models import BatchOutputResponse

        error_data = {
            "message": "Invalid API key",
            "type": "authentication_error",
            "code": "invalid_api_key",
        }

        output = BatchOutputResponse(
            id="batch_req_error",
            custom_id="request-error",
            error=error_data,
        )

        assert output.id == "batch_req_error"
        assert output.custom_id == "request-error"
        assert output.response is None
        assert output.error is not None
        assert output.error["message"] == "Invalid API key"
        assert output.error["type"] == "authentication_error"

    def test_batch_output_response_validation(self):
        """Test BatchOutputResponse validation."""
        from fakeai.models import BatchOutputResponse

        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            BatchOutputResponse(custom_id="req-1")

        # Valid with only required fields
        output = BatchOutputResponse(id="batch_req_1", custom_id="req-1")
        assert output.response is None
        assert output.error is None


class TestModuleStructure:
    """Test the module structure and organization."""

    def test_batches_module_exports(self):
        """Test that batches module has correct exports."""
        import fakeai.models.batches as batches_module

        # Check that expected classes are available
        assert hasattr(batches_module, "BatchRequestCounts")
        assert hasattr(batches_module, "Batch")
        assert hasattr(batches_module, "CreateBatchRequest")
        assert hasattr(batches_module, "BatchListResponse")
        assert hasattr(batches_module, "BatchRequest")
        assert hasattr(batches_module, "BatchOutputResponse")

        # Check __all__ exists and contains expected exports
        assert hasattr(batches_module, "__all__")
        expected_exports = [
            "BatchRequestCounts",
            "Batch",
            "CreateBatchRequest",
            "BatchListResponse",
            "BatchRequest",
            "BatchOutputResponse",
        ]
        for export in expected_exports:
            assert export in batches_module.__all__

    def test_package_init_exports(self):
        """Test that package __init__ has batch model exports."""
        import fakeai.models as models_package

        # Check __all__ exists
        assert hasattr(models_package, "__all__")

        # Check all expected batch exports are in __all__
        expected_exports = [
            "BatchRequestCounts",
            "Batch",
            "CreateBatchRequest",
            "BatchListResponse",
            "BatchRequest",
            "BatchOutputResponse",
        ]

        for export in expected_exports:
            assert export in models_package.__all__, f"{export} not in __all__"
            assert hasattr(models_package, export), f"{export} not available in package"
