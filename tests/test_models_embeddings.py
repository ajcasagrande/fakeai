"""
Tests for models refactoring - Embeddings module.

This test suite verifies the embeddings models module including:
- EmbeddingRequest with various input types
- Embedding response structure
- EmbeddingsUsageResponse
- Dimension validation
- Encoding format support
- Backward compatibility with fakeai.models package
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError


class TestImportsFromModelsPackage:
    """Test that embeddings models can be imported from the models package."""

    def test_import_embeddings_models_from_package(self):
        """Test importing embeddings models from fakeai.models package."""
        from fakeai.models import (
            Embedding,
            EmbeddingRequest,
            EmbeddingResponse,
            EmbeddingsUsageResponse,
        )

        # Verify classes are imported correctly
        assert EmbeddingRequest is not None
        assert Embedding is not None
        assert EmbeddingResponse is not None
        assert EmbeddingsUsageResponse is not None


class TestImportsFromEmbeddingsModule:
    """Test that models can be imported from the embeddings module."""

    def test_import_from_embeddings_module(self):
        """Test importing from fakeai.models.embeddings module."""
        from fakeai.models.embeddings import (
            Embedding,
            EmbeddingRequest,
            EmbeddingResponse,
            EmbeddingsUsageResponse,
        )

        # Verify classes are imported correctly
        assert EmbeddingRequest is not None
        assert Embedding is not None
        assert EmbeddingResponse is not None
        assert EmbeddingsUsageResponse is not None


class TestBackwardCompatibility:
    """Test that imports from different paths reference the same classes."""

    def test_embeddings_models_reference_same_class(self):
        """Test that embeddings models imported from different paths are the same class."""
        from fakeai.models import EmbeddingRequest as EmbeddingRequestFromPackage
        from fakeai.models.embeddings import (
            EmbeddingRequest as EmbeddingRequestFromModule,
        )

        # Verify they reference the same class
        assert EmbeddingRequestFromPackage is EmbeddingRequestFromModule

    def test_all_embeddings_models_reference_same_class(self):
        """Test that all embeddings models reference the same classes."""
        from fakeai.models import (
            Embedding,
            EmbeddingRequest,
            EmbeddingResponse,
            EmbeddingsUsageResponse,
        )
        from fakeai.models.embeddings import Embedding as EmbeddingModule
        from fakeai.models.embeddings import EmbeddingRequest as EmbeddingRequestModule
        from fakeai.models.embeddings import (
            EmbeddingResponse as EmbeddingResponseModule,
        )
        from fakeai.models.embeddings import (
            EmbeddingsUsageResponse as EmbeddingsUsageResponseModule,
        )

        # Verify all classes reference the same objects
        assert EmbeddingRequest is EmbeddingRequestModule
        assert Embedding is EmbeddingModule
        assert EmbeddingResponse is EmbeddingResponseModule
        assert EmbeddingsUsageResponse is EmbeddingsUsageResponseModule


class TestEmbeddingRequestInstantiation:
    """Test EmbeddingRequest instantiation with various input types."""

    def test_embedding_request_single_string(self):
        """Test EmbeddingRequest with single string input."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="The quick brown fox jumps over the lazy dog",
        )

        assert request.model == "text-embedding-ada-002"
        assert request.input == "The quick brown fox jumps over the lazy dog"
        assert request.user is None
        assert request.encoding_format == "float"
        assert request.dimensions is None

    def test_embedding_request_list(self):
        """Test EmbeddingRequest with list of strings input."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input=["First sentence", "Second sentence", "Third sentence"],
        )

        assert request.model == "text-embedding-ada-002"
        assert len(request.input) == 3
        assert request.input[0] == "First sentence"
        assert request.input[1] == "Second sentence"
        assert request.input[2] == "Third sentence"

    def test_embedding_request_with_user(self):
        """Test EmbeddingRequest with user identifier."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test input",
            user="user-12345",
        )

        assert request.user == "user-12345"

    def test_embedding_request_with_base64_encoding(self):
        """Test EmbeddingRequest with base64 encoding format."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test input",
            encoding_format="base64",
        )

        assert request.encoding_format == "base64"

    def test_embedding_request_with_dimensions(self):
        """Test EmbeddingRequest with custom dimensions."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-3-large",
            input="Test input",
            dimensions=256,
        )

        assert request.dimensions == 256

    def test_embedding_request_with_token_ids(self):
        """Test EmbeddingRequest with token IDs as input."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input=[1234, 5678, 9012],
        )

        assert request.input == [1234, 5678, 9012]

    def test_embedding_request_with_token_id_lists(self):
        """Test EmbeddingRequest with multiple token ID lists."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input=[[1234, 5678], [9012, 3456]],
        )

        assert len(request.input) == 2
        assert request.input[0] == [1234, 5678]
        assert request.input[1] == [9012, 3456]


class TestEmbeddingInstantiation:
    """Test Embedding model instantiation."""

    def test_embedding_basic(self):
        """Test basic Embedding instantiation."""
        from fakeai.models import Embedding

        embedding = Embedding(
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            index=0,
        )

        assert embedding.object == "embedding"
        assert embedding.embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert embedding.index == 0
        assert len(embedding.embedding) == 5

    def test_embedding_with_large_vector(self):
        """Test Embedding with large vector (1536 dimensions)."""
        from fakeai.models import Embedding

        # Create a 1536-dimensional vector (typical for text-embedding-ada-002)
        vector = [0.001 * i for i in range(1536)]
        embedding = Embedding(embedding=vector, index=0)

        assert len(embedding.embedding) == 1536
        assert embedding.embedding[0] == 0.0
        assert abs(embedding.embedding[1535] - 1.535) < 0.0001

    def test_embedding_with_different_indices(self):
        """Test Embedding with different index values."""
        from fakeai.models import Embedding

        embedding1 = Embedding(embedding=[0.1, 0.2], index=0)
        embedding2 = Embedding(embedding=[0.3, 0.4], index=1)
        embedding3 = Embedding(embedding=[0.5, 0.6], index=2)

        assert embedding1.index == 0
        assert embedding2.index == 1
        assert embedding3.index == 2


class TestEmbeddingResponseStructure:
    """Test EmbeddingResponse structure and instantiation."""

    def test_embedding_response_structure(self):
        """Test complete EmbeddingResponse structure."""
        from fakeai.models import Embedding, EmbeddingResponse, Usage

        embeddings = [
            Embedding(embedding=[0.1, 0.2, 0.3], index=0),
            Embedding(embedding=[0.4, 0.5, 0.6], index=1),
        ]

        usage = Usage(
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10,
        )

        response = EmbeddingResponse(
            data=embeddings,
            model="text-embedding-ada-002",
            usage=usage,
        )

        assert response.object == "list"
        assert len(response.data) == 2
        assert response.model == "text-embedding-ada-002"
        assert response.usage.prompt_tokens == 10
        assert response.usage.total_tokens == 10

    def test_embedding_response_single_result(self):
        """Test EmbeddingResponse with single result."""
        from fakeai.models import Embedding, EmbeddingResponse, Usage

        embedding = Embedding(
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            index=0,
        )

        usage = Usage(
            prompt_tokens=5,
            completion_tokens=0,
            total_tokens=5,
        )

        response = EmbeddingResponse(
            data=[embedding],
            model="text-embedding-ada-002",
            usage=usage,
        )

        assert len(response.data) == 1
        assert response.data[0].index == 0
        assert len(response.data[0].embedding) == 5

    def test_embedding_response_multiple_results(self):
        """Test EmbeddingResponse with multiple results."""
        from fakeai.models import Embedding, EmbeddingResponse, Usage

        embeddings = [Embedding(embedding=[0.1] * 1536, index=i) for i in range(10)]

        usage = Usage(
            prompt_tokens=100,
            completion_tokens=0,
            total_tokens=100,
        )

        response = EmbeddingResponse(
            data=embeddings,
            model="text-embedding-ada-002",
            usage=usage,
        )

        assert len(response.data) == 10
        for i, emb in enumerate(response.data):
            assert emb.index == i
            assert len(emb.embedding) == 1536


class TestDimensionValidation:
    """Test dimension validation for embeddings."""

    def test_dimension_validation_positive(self):
        """Test that positive dimensions are accepted."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-3-large",
            input="Test",
            dimensions=256,
        )
        assert request.dimensions == 256

        request = EmbeddingRequest(
            model="text-embedding-3-large",
            input="Test",
            dimensions=1536,
        )
        assert request.dimensions == 1536

        request = EmbeddingRequest(
            model="text-embedding-3-large",
            input="Test",
            dimensions=3072,
        )
        assert request.dimensions == 3072

    def test_dimension_validation_none_allowed(self):
        """Test that None dimensions are allowed (use default)."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test",
            dimensions=None,
        )
        assert request.dimensions is None

    def test_dimension_validation_invalid_type(self):
        """Test that invalid dimension types raise ValidationError."""
        from fakeai.models import EmbeddingRequest

        # String should raise ValidationError
        with pytest.raises(ValidationError):
            EmbeddingRequest(
                model="text-embedding-3-large",
                input="Test",
                dimensions="invalid",  # Non-numeric string
            )

        # Float with fractional part should raise ValidationError
        with pytest.raises(ValidationError):
            EmbeddingRequest(
                model="text-embedding-3-large",
                input="Test",
                dimensions=256.5,  # Float with fractional part not allowed
            )


class TestEncodingFormatSupport:
    """Test encoding format support."""

    def test_encoding_format_float(self):
        """Test float encoding format (default)."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test",
            encoding_format="float",
        )
        assert request.encoding_format == "float"

    def test_encoding_format_base64(self):
        """Test base64 encoding format."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test",
            encoding_format="base64",
        )
        assert request.encoding_format == "base64"

    def test_encoding_format_default(self):
        """Test default encoding format is float."""
        from fakeai.models import EmbeddingRequest

        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test",
        )
        assert request.encoding_format == "float"

    def test_encoding_format_invalid(self):
        """Test that invalid encoding formats raise ValidationError."""
        from fakeai.models import EmbeddingRequest

        with pytest.raises(ValidationError):
            EmbeddingRequest(
                model="text-embedding-ada-002",
                input="Test",
                encoding_format="invalid",
            )

        with pytest.raises(ValidationError):
            EmbeddingRequest(
                model="text-embedding-ada-002",
                input="Test",
                encoding_format="hex",
            )


class TestEmbeddingsUsageResponse:
    """Test EmbeddingsUsageResponse model."""

    def test_embeddings_usage_response_basic(self):
        """Test basic EmbeddingsUsageResponse instantiation."""
        from fakeai.models import EmbeddingsUsageResponse

        response = EmbeddingsUsageResponse(
            data=[],
            has_more=False,
        )

        assert response.object == "page"
        assert response.data == []
        assert response.has_more is False
        assert response.next_page is None

    def test_embeddings_usage_response_with_pagination(self):
        """Test EmbeddingsUsageResponse with pagination."""
        from fakeai.models import EmbeddingsUsageResponse

        response = EmbeddingsUsageResponse(
            data=[{"count": 100}, {"count": 200}],
            has_more=True,
            next_page="/v1/organization/usage/embeddings?page=2",
        )

        assert response.has_more is True
        assert response.next_page == "/v1/organization/usage/embeddings?page=2"
        assert len(response.data) == 2

    def test_embeddings_usage_response_with_data(self):
        """Test EmbeddingsUsageResponse with usage data."""
        from fakeai.models import EmbeddingsUsageResponse

        usage_data = [
            {
                "aggregation_timestamp": 1234567890,
                "n_requests": 100,
                "operation": "embedding",
                "snapshot_id": "snap-123",
            },
            {
                "aggregation_timestamp": 1234567900,
                "n_requests": 150,
                "operation": "embedding",
                "snapshot_id": "snap-124",
            },
        ]

        response = EmbeddingsUsageResponse(
            data=usage_data,
            has_more=False,
        )

        assert len(response.data) == 2
        assert response.data[0]["n_requests"] == 100
        assert response.data[1]["n_requests"] == 150


class TestUsageTracking:
    """Test usage tracking integration with embeddings."""

    def test_usage_tracking_in_response(self):
        """Test that usage tracking is properly integrated."""
        from fakeai.models import Embedding, EmbeddingResponse, Usage

        usage = Usage(
            prompt_tokens=50,
            completion_tokens=0,
            total_tokens=50,
        )

        embedding = Embedding(embedding=[0.1] * 1536, index=0)
        response = EmbeddingResponse(
            data=[embedding],
            model="text-embedding-ada-002",
            usage=usage,
        )

        # Verify usage is accessible and correct
        assert response.usage.prompt_tokens == 50
        assert response.usage.completion_tokens == 0
        assert response.usage.total_tokens == 50

    def test_usage_tracking_with_details(self):
        """Test usage tracking with token details."""
        from fakeai.models import (
            CompletionTokensDetails,
            Embedding,
            EmbeddingResponse,
            PromptTokensDetails,
            Usage,
        )

        prompt_details = PromptTokensDetails(
            cached_tokens=10,
            audio_tokens=0,
        )

        completion_details = CompletionTokensDetails(
            reasoning_tokens=0,
            audio_tokens=0,
            accepted_prediction_tokens=0,
            rejected_prediction_tokens=0,
        )

        usage = Usage(
            prompt_tokens=50,
            completion_tokens=0,
            total_tokens=50,
            prompt_tokens_details=prompt_details,
            completion_tokens_details=completion_details,
        )

        embedding = Embedding(embedding=[0.1] * 1536, index=0)
        response = EmbeddingResponse(
            data=[embedding],
            model="text-embedding-ada-002",
            usage=usage,
        )

        assert response.usage.prompt_tokens_details.cached_tokens == 10
        assert response.usage.completion_tokens_details.reasoning_tokens == 0


class TestModelValidation:
    """Test model validation."""

    def test_embedding_request_missing_model(self):
        """Test that missing model raises ValidationError."""
        from fakeai.models import EmbeddingRequest

        with pytest.raises(ValidationError):
            EmbeddingRequest(input="Test")

    def test_embedding_request_missing_input(self):
        """Test that missing input raises ValidationError."""
        from fakeai.models import EmbeddingRequest

        with pytest.raises(ValidationError):
            EmbeddingRequest(model="text-embedding-ada-002")

    def test_embedding_missing_fields(self):
        """Test that missing required fields raise ValidationError."""
        from fakeai.models import Embedding

        with pytest.raises(ValidationError):
            Embedding(index=0)  # Missing embedding

        with pytest.raises(ValidationError):
            Embedding(embedding=[0.1, 0.2])  # Missing index

    def test_embedding_response_missing_fields(self):
        """Test that missing required fields raise ValidationError."""
        from fakeai.models import Embedding, EmbeddingResponse, Usage

        embedding = Embedding(embedding=[0.1, 0.2], index=0)
        usage = Usage(prompt_tokens=5, completion_tokens=0, total_tokens=5)

        with pytest.raises(ValidationError):
            EmbeddingResponse(data=[embedding], usage=usage)  # Missing model

        with pytest.raises(ValidationError):
            EmbeddingResponse(model="test", usage=usage)  # Missing data

        with pytest.raises(ValidationError):
            EmbeddingResponse(data=[embedding], model="test")  # Missing usage


class TestModuleStructure:
    """Test the module structure and organization."""

    def test_embeddings_module_exports(self):
        """Test that embeddings module has correct exports."""
        import fakeai.models.embeddings as embeddings_module

        # Check that expected classes are available
        assert hasattr(embeddings_module, "EmbeddingRequest")
        assert hasattr(embeddings_module, "Embedding")
        assert hasattr(embeddings_module, "EmbeddingResponse")
        assert hasattr(embeddings_module, "EmbeddingsUsageResponse")

    def test_package_init_exports_embeddings(self):
        """Test that package __init__ exports embeddings models."""
        import fakeai.models as models_package

        # Check __all__ exists
        assert hasattr(models_package, "__all__")

        # Check all embeddings exports are in __all__
        expected_exports = [
            "EmbeddingRequest",
            "Embedding",
            "EmbeddingResponse",
            "EmbeddingsUsageResponse",
        ]

        for export in expected_exports:
            assert export in models_package.__all__, f"{export} not in __all__"
            assert hasattr(models_package, export), f"{export} not available in package"
