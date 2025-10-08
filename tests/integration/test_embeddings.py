"""
Integration tests for /v1/embeddings endpoint.

This module tests the embeddings endpoint with TestClient including:
- Single and batch embeddings
- L2 normalization verification
- Custom dimensions support
- Response format compliance
- Error handling
- Token tracking
"""

#  SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest


@pytest.mark.integration
class TestEmbeddingsIntegration:
    """Integration tests for /v1/embeddings endpoint."""

    def test_single_embedding_returns_200(self, client_no_auth):
        """Single embedding request should return 200 OK."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Hello world",
            },
        )

        assert response.status_code == 200

    def test_single_embedding_response_format(self, client_no_auth):
        """Single embedding response should match OpenAI format."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Hello world",
            },
        )

        data = response.json()

        # Top-level fields
        assert data["object"] == "list"
        assert "data" in data
        assert "model" in data
        assert "usage" in data
        assert data["model"] == "text-embedding-ada-002"

        # Data array
        assert len(data["data"]) == 1
        assert data["data"][0]["object"] == "embedding"
        assert data["data"][0]["index"] == 0
        assert "embedding" in data["data"][0]

        # Usage fields
        assert data["usage"]["prompt_tokens"] > 0
        assert data["usage"]["completion_tokens"] == 0
        assert data["usage"]["total_tokens"] == data["usage"]["prompt_tokens"]

    def test_single_embedding_default_dimensions(self, client_no_auth):
        """Single embedding should have default 1536 dimensions."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
            },
        )

        data = response.json()
        embedding = data["data"][0]["embedding"]

        assert len(embedding) == 1536

    def test_single_embedding_l2_normalized(self, client_no_auth):
        """Single embedding should be L2 normalized (unit vector)."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test normalization",
            },
        )

        data = response.json()
        embedding = data["data"][0]["embedding"]

        # Calculate L2 norm
        norm = np.linalg.norm(embedding)

        # Should be approximately 1.0 (unit vector)
        assert abs(norm - 1.0) < 0.001, f"Expected norm ~1.0, got {norm}"

    def test_batch_embeddings_returns_200(self, client_no_auth):
        """Batch embedding request should return 200 OK."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": ["First text", "Second text", "Third text"],
            },
        )

        assert response.status_code == 200

    def test_batch_embeddings_correct_count(self, client_no_auth):
        """Batch embeddings should return correct number of embeddings."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"],
            },
        )

        data = response.json()

        assert len(data["data"]) == 5

    def test_batch_embeddings_correct_indices(self, client_no_auth):
        """Batch embeddings should have correct index ordering."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": ["First", "Second", "Third"],
            },
        )

        data = response.json()

        assert data["data"][0]["index"] == 0
        assert data["data"][1]["index"] == 1
        assert data["data"][2]["index"] == 2

    def test_batch_embeddings_all_normalized(self, client_no_auth):
        """All embeddings in batch should be L2 normalized."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": [
                    "First text",
                    "Second text",
                    "Third text",
                    "Fourth text",
                ],
            },
        )

        data = response.json()

        for i, embedding_obj in enumerate(data["data"]):
            embedding = embedding_obj["embedding"]
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 0.001, f"Embedding {i} norm {norm} != 1.0"

    def test_custom_dimensions_256(self, client_no_auth):
        """Custom dimensions of 256 should work."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
                "dimensions": 256,
            },
        )

        data = response.json()
        embedding = data["data"][0]["embedding"]

        assert len(embedding) == 256

    def test_custom_dimensions_512(self, client_no_auth):
        """Custom dimensions of 512 should work."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
                "dimensions": 512,
            },
        )

        data = response.json()
        embedding = data["data"][0]["embedding"]

        assert len(embedding) == 512

    def test_custom_dimensions_3072(self, client_no_auth):
        """Custom dimensions of 3072 should work."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
                "dimensions": 3072,
            },
        )

        data = response.json()
        embedding = data["data"][0]["embedding"]

        assert len(embedding) == 3072

    def test_custom_dimensions_normalized(self, client_no_auth):
        """Custom dimension embeddings should also be L2 normalized."""
        dimensions_to_test = [128, 256, 512, 1024, 2048]

        for dims in dimensions_to_test:
            response = client_no_auth.post(
                "/v1/embeddings",
                json={
                    "model": "text-embedding-ada-002",
                    "input": "Test",
                    "dimensions": dims,
                },
            )

            data = response.json()
            embedding = data["data"][0]["embedding"]
            norm = np.linalg.norm(embedding)

            assert abs(norm - 1.0) < 0.001, f"Dims {dims}: norm {norm} != 1.0"

    def test_batch_with_custom_dimensions(self, client_no_auth):
        """Batch embeddings with custom dimensions should work."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": ["Text 1", "Text 2", "Text 3"],
                "dimensions": 768,
            },
        )

        data = response.json()

        assert len(data["data"]) == 3
        for embedding_obj in data["data"]:
            assert len(embedding_obj["embedding"]) == 768

    def test_embedding_consistency(self, client_no_auth):
        """Same input should produce consistent embeddings."""
        input_text = "Consistency test"

        response1 = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": input_text,
            },
        )

        response2 = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": input_text,
            },
        )

        data1 = response1.json()
        data2 = response2.json()

        embedding1 = data1["data"][0]["embedding"]
        embedding2 = data2["data"][0]["embedding"]

        # Should be identical (deterministic based on hash)
        assert embedding1 == embedding2

    def test_embedding_uniqueness(self, client_no_auth):
        """Different inputs should produce different embeddings."""
        response1 = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "First text",
            },
        )

        response2 = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Second text",
            },
        )

        data1 = response1.json()
        data2 = response2.json()

        embedding1 = data1["data"][0]["embedding"]
        embedding2 = data2["data"][0]["embedding"]

        # Should be different
        assert embedding1 != embedding2

    def test_empty_string_input(self, client_no_auth):
        """Empty string input should work."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "",
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1

    def test_long_text_input(self, client_no_auth):
        """Long text input should work."""
        long_text = "This is a test. " * 100  # 400 words

        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": long_text,
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert data["usage"]["prompt_tokens"] > 100

    def test_unicode_input(self, client_no_auth):
        """Unicode text should work."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Hello 世界 🌍 Привет мир",
            },
        )

        assert response.status_code == 200

    def test_special_characters_input(self, client_no_auth):
        """Special characters should work."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            },
        )

        assert response.status_code == 200

    def test_token_ids_input_single(self, client_no_auth):
        """Token IDs as input should work (single sequence)."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": [100, 200, 300, 400],
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1

    def test_token_ids_input_multiple(self, client_no_auth):
        """Token IDs as input should work (multiple sequences)."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": [[100, 200], [300, 400, 500], [600]],
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 3

    def test_large_batch_performance(self, client_no_auth):
        """Large batch should process efficiently."""
        large_batch = [f"Test sentence number {i}" for i in range(50)]

        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": large_batch,
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 50

    def test_different_models_work(self, client_no_auth):
        """Different model names should work."""
        models = [
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
            "sentence-transformers/all-mpnet-base-v2",
        ]

        for model in models:
            response = client_no_auth.post(
                "/v1/embeddings",
                json={
                    "model": model,
                    "input": "Test",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == model

    def test_encoding_format_base64(self, client_no_auth):
        """Encoding format base64 should work."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
                "encoding_format": "base64",
            },
        )

        assert response.status_code == 200

        data = response.json()
        # With base64, embedding should be a string
        assert isinstance(data["data"][0]["embedding"], str)

    def test_encoding_format_float(self, client_no_auth):
        """Encoding format float should work (default)."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
                "encoding_format": "float",
            },
        )

        assert response.status_code == 200

        data = response.json()
        # With float, embedding should be a list
        assert isinstance(data["data"][0]["embedding"], list)

    def test_dimensions_validation_too_large(self, client_no_auth):
        """Dimensions above 3072 should be rejected."""
        # Note: This should raise an error during processing
        # The service validates dimensions in create_embedding method
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
                "dimensions": 4000,
            },
        )

        # Should return 400 or 422 or 500 (validation error)
        assert response.status_code in [400, 422, 500]

    def test_response_does_not_have_id(self, client_no_auth):
        """Response should NOT have an ID field (per OpenAI spec)."""
        # Note: OpenAI embeddings response does not include 'id' field
        # Only chat completions have 'id' field
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
            },
        )

        data = response.json()

        # Embeddings response doesn't have ID (unlike chat completions)
        assert "id" not in data

    def test_response_does_not_have_created(self, client_no_auth):
        """Response should NOT have a created timestamp (per OpenAI spec)."""
        # Note: OpenAI embeddings response does not include 'created' field
        # Only chat completions have 'created' field
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Test",
            },
        )

        data = response.json()

        # Embeddings response doesn't have created timestamp
        assert "created" not in data

    def test_usage_tracking_accuracy(self, client_no_auth):
        """Usage tracking should be reasonably accurate."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "This is a test message with multiple words",
            },
        )

        data = response.json()

        # Should have reasonable token count
        assert data["usage"]["prompt_tokens"] > 5
        assert data["usage"]["prompt_tokens"] < 20  # Shouldn't be crazy

    def test_batch_usage_tracking(self, client_no_auth):
        """Batch usage should sum all inputs."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": ["Text 1", "Text 2", "Text 3"],
            },
        )

        data = response.json()

        # Should have usage for all inputs
        assert data["usage"]["prompt_tokens"] > 3  # At least one token per input

    @pytest.mark.slow
    def test_normalization_across_dimensions(self, client_no_auth):
        """L2 normalization should work across all dimension sizes."""
        test_cases = [
            (128, "Test 1"),
            (256, "Test 2"),
            (512, "Test 3"),
            (768, "Test 4"),
            (1024, "Test 5"),
            (1536, "Test 6"),
            (2048, "Test 7"),
            (3072, "Test 8"),
        ]

        for dims, text in test_cases:
            response = client_no_auth.post(
                "/v1/embeddings",
                json={
                    "model": "text-embedding-ada-002",
                    "input": text,
                    "dimensions": dims,
                },
            )

            data = response.json()
            embedding = data["data"][0]["embedding"]

            # Verify dimension
            assert len(embedding) == dims

            # Verify L2 normalization
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 0.001, f"{dims}D: norm {norm} != 1.0"

    def test_batch_normalization_stress_test(self, client_no_auth):
        """Stress test: all embeddings in large batch should be normalized."""
        large_batch = [f"Test text number {i} with unique content" for i in range(20)]

        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": large_batch,
            },
        )

        data = response.json()

        assert len(data["data"]) == 20

        # Check all are normalized
        for i, embedding_obj in enumerate(data["data"]):
            embedding = embedding_obj["embedding"]
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 0.001, f"Item {i}: norm {norm} != 1.0"
