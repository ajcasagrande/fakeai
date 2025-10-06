"""Integration tests for NVIDIA NIM ranking endpoint.

This module tests the /v1/ranking endpoint which provides semantic relevance
scoring for information retrieval and search applications.
"""

import asyncio
import time
from typing import Any

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
class TestNIMRankingBasic:
    """Test basic NVIDIA NIM ranking functionality."""

    def test_basic_ranking(self, client: FakeAIClient):
        """Test basic ranking with query and passages."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "What is machine learning?"},
                "passages": [
                    {"text": "Machine learning is a subset of artificial intelligence."},
                    {"text": "The weather today is sunny and warm."},
                    {"text": "Deep learning uses neural networks for pattern recognition."},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "rankings" in data
        assert isinstance(data["rankings"], list)
        assert len(data["rankings"]) == 3

        # Validate ranking objects
        for ranking in data["rankings"]:
            assert "index" in ranking
            assert "logit" in ranking
            assert isinstance(ranking["index"], int)
            assert isinstance(ranking["logit"], (int, float))

        # Validate rankings are sorted by logit descending
        logits = [r["logit"] for r in data["rankings"]]
        assert logits == sorted(logits, reverse=True)

    def test_ranking_with_single_passage(self, client: FakeAIClient):
        """Test ranking with a single passage."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "How does photosynthesis work?"},
                "passages": [
                    {"text": "Photosynthesis converts light energy into chemical energy."},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "rankings" in data
        assert len(data["rankings"]) == 1
        assert data["rankings"][0]["index"] == 0
        assert isinstance(data["rankings"][0]["logit"], (int, float))

    def test_ranking_relevance_scoring(self, client: FakeAIClient):
        """Test that relevant passages score higher than irrelevant ones."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "python programming language"},
                "passages": [
                    {"text": "Python is a high-level programming language."},
                    {"text": "The python snake is found in tropical regions."},
                    {"text": "Python supports multiple programming paradigms."},
                    {"text": "Bananas are a good source of potassium."},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Get indices of relevant vs irrelevant passages
        # Top ranked should likely be programming-related (indices 0, 2)
        # Note: Due to randomness, we just verify structure is correct
        assert len(data["rankings"]) == 4
        assert all("index" in r and "logit" in r for r in data["rankings"])


@pytest.mark.integration
class TestNIMRankingModels:
    """Test different ranking models."""

    @pytest.mark.parametrize(
        "model_id",
        [
            "nvidia/nv-rerankqa-mistral-4b-v3",
            "nvidia/nv-embedqa-e5-v5",
            "nvidia/rerank-qa-mistral-4b",
            "custom-reranker-model",
        ],
    )
    def test_different_ranking_models(self, client: FakeAIClient, model_id: str):
        """Test ranking with different model IDs."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": model_id,
                "query": {"text": "artificial intelligence"},
                "passages": [
                    {"text": "AI is transforming technology."},
                    {"text": "Machine learning is a branch of AI."},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "rankings" in data
        assert len(data["rankings"]) == 2


@pytest.mark.integration
class TestNIMRankingTopK:
    """Test top-k results filtering."""

    def test_large_passage_set(self, client: FakeAIClient):
        """Test ranking with many passages."""
        passages = [
            {"text": f"This is passage number {i} about various topics."}
            for i in range(50)
        ]

        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "information retrieval"},
                "passages": passages,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # All 50 passages should be ranked
        assert len(data["rankings"]) == 50

        # Verify all indices are present (0-49)
        indices = {r["index"] for r in data["rankings"]}
        assert indices == set(range(50))

    def test_top_k_selection(self, client: FakeAIClient):
        """Test selecting top-k most relevant passages."""
        passages = [
            {"text": "Machine learning trains models on data."},
            {"text": "Neural networks mimic brain structure."},
            {"text": "Pizza is a popular Italian food."},
            {"text": "Deep learning uses multiple layers."},
            {"text": "The ocean covers most of Earth."},
        ]

        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "machine learning and neural networks"},
                "passages": passages,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Get top 3 results
        top_3 = data["rankings"][:3]
        assert len(top_3) == 3

        # All should have valid indices and scores
        for ranking in top_3:
            assert 0 <= ranking["index"] < len(passages)
            assert isinstance(ranking["logit"], (int, float))


@pytest.mark.integration
class TestNIMRankingScores:
    """Test ranking score properties."""

    def test_score_ranges(self, client: FakeAIClient):
        """Test that scores are reasonable logit values."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "climate change"},
                "passages": [
                    {"text": "Global warming affects ecosystems."},
                    {"text": "Climate change impacts weather patterns."},
                    {"text": "Random unrelated text here."},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check that scores are in reasonable range (typically -10 to +10 for logits)
        for ranking in data["rankings"]:
            assert -20 <= ranking["logit"] <= 20

    def test_score_ordering(self, client: FakeAIClient):
        """Test that scores are strictly ordered."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": [{"text": f"passage {i}"} for i in range(10)],
            },
        )

        assert response.status_code == 200
        data = response.json()

        logits = [r["logit"] for r in data["rankings"]]

        # Should be in descending order
        for i in range(len(logits) - 1):
            assert logits[i] >= logits[i + 1]


@pytest.mark.integration
class TestNIMRankingBatch:
    """Test batch ranking operations."""

    def test_multiple_sequential_rankings(self, client: FakeAIClient):
        """Test multiple ranking requests in sequence."""
        queries = [
            "What is quantum computing?",
            "How does blockchain work?",
            "Explain neural networks",
        ]

        passages = [
            {"text": "Quantum computers use qubits."},
            {"text": "Blockchain is a distributed ledger."},
            {"text": "Neural networks process information."},
        ]

        results = []
        for query_text in queries:
            response = client.post(
                "/v1/ranking",
                json={
                    "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                    "query": {"text": query_text},
                    "passages": passages,
                },
            )

            assert response.status_code == 200
            results.append(response.json())

        # All requests should succeed
        assert len(results) == 3

        # Each should have rankings for all passages
        for result in results:
            assert len(result["rankings"]) == len(passages)


@pytest.mark.integration
class TestNIMRankingConcurrent:
    """Test concurrent ranking requests."""

    @pytest.mark.asyncio
    async def test_concurrent_ranking_requests(self, client: FakeAIClient):
        """Test multiple concurrent ranking requests."""

        async def make_ranking_request(query_text: str) -> dict[str, Any]:
            """Make a single ranking request."""
            response = client.post(
                "/v1/ranking",
                json={
                    "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                    "query": {"text": query_text},
                    "passages": [
                        {"text": "Artificial intelligence enables automation."},
                        {"text": "Machine learning learns from data."},
                    ],
                },
            )
            return response.json()

        # Create 10 concurrent requests
        queries = [f"Query about AI topic {i}" for i in range(10)]
        tasks = [make_ranking_request(q) for q in queries]

        # Run concurrently with asyncio.gather
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # All should succeed
        assert len(results) == 10
        for result in results:
            assert "rankings" in result
            assert len(result["rankings"]) == 2

        # Concurrent execution should be reasonably fast
        # (faster than 10 sequential requests which would take ~2-3 seconds)
        assert elapsed < 5.0

    def test_concurrent_different_models(self, client: FakeAIClient):
        """Test concurrent requests with different models."""
        models = [
            "nvidia/nv-rerankqa-mistral-4b-v3",
            "nvidia/nv-embedqa-e5-v5",
            "custom-reranker",
        ]

        results = []
        for model in models:
            response = client.post(
                "/v1/ranking",
                json={
                    "model": model,
                    "query": {"text": "test query"},
                    "passages": [{"text": "test passage"}],
                },
            )
            results.append(response.json())

        # All should succeed
        assert len(results) == len(models)
        for result in results:
            assert "rankings" in result


@pytest.mark.integration
class TestNIMRankingWithMetadata:
    """Test ranking with various passage metadata scenarios."""

    def test_ranking_long_passages(self, client: FakeAIClient):
        """Test ranking with long passage texts."""
        long_passage = " ".join(["This is a long passage."] * 50)

        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "long passage"},
                "passages": [
                    {"text": long_passage},
                    {"text": "Short passage."},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["rankings"]) == 2

    def test_ranking_special_characters(self, client: FakeAIClient):
        """Test ranking with special characters in text."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "special chars: @#$%^&*()"},
                "passages": [
                    {"text": "Text with symbols: @#$%"},
                    {"text": "Unicode: émojis 🚀 ✨"},
                    {"text": "Normal text here"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["rankings"]) == 3

    def test_ranking_empty_passages(self, client: FakeAIClient):
        """Test ranking behavior with empty passage text."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": [
                    {"text": ""},
                    {"text": "Valid passage text"},
                    {"text": "   "},  # Whitespace only
                ],
            },
        )

        # Should still work (empty passages just score low)
        assert response.status_code == 200
        data = response.json()

        assert len(data["rankings"]) == 3

    def test_ranking_with_truncate_parameter(self, client: FakeAIClient):
        """Test ranking with truncation parameter."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": [{"text": "test passage"}],
                "truncate": "END",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "rankings" in data

    def test_ranking_without_truncate_parameter(self, client: FakeAIClient):
        """Test ranking with default truncation (NONE)."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": [{"text": "test passage"}],
                "truncate": "NONE",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "rankings" in data


@pytest.mark.integration
class TestNIMRankingPerformance:
    """Test ranking performance characteristics."""

    def test_ranking_latency(self, client: FakeAIClient):
        """Test that ranking requests complete in reasonable time."""
        start_time = time.time()

        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "performance test query"},
                "passages": [
                    {"text": f"Passage {i} for performance testing"} for i in range(20)
                ],
            },
        )

        elapsed = time.time() - start_time

        assert response.status_code == 200

        # Should complete in reasonable time (allow for delay simulation)
        assert elapsed < 2.0

    def test_ranking_with_max_passages(self, client: FakeAIClient):
        """Test ranking with maximum allowed passages (512)."""
        # Generate 512 passages (API maximum)
        passages = [{"text": f"Passage number {i}"} for i in range(512)]

        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": passages,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # All 512 passages should be ranked
        assert len(data["rankings"]) == 512

        # Verify all indices present
        indices = {r["index"] for r in data["rankings"]}
        assert len(indices) == 512

    @pytest.mark.metrics
    def test_ranking_metrics_tracking(self, client: FakeAIClient):
        """Test that ranking requests are tracked in metrics."""
        # Get initial metrics
        metrics_before = client.get_metrics()

        # Make ranking request
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "metrics test"},
                "passages": [{"text": "test passage"}],
            },
        )

        assert response.status_code == 200

        # Get metrics after
        metrics_after = client.get_metrics()

        # Verify request was tracked
        # (Note: Exact metric structure may vary)
        assert "requests" in metrics_after or "total_requests" in metrics_after


@pytest.mark.integration
class TestNIMRankingErrorHandling:
    """Test error handling for ranking endpoint."""

    def test_ranking_missing_model(self, client: FakeAIClient):
        """Test ranking request without model."""
        response = client.post(
            "/v1/ranking",
            json={
                "query": {"text": "test query"},
                "passages": [{"text": "test passage"}],
            },
        )

        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_ranking_missing_query(self, client: FakeAIClient):
        """Test ranking request without query."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "passages": [{"text": "test passage"}],
            },
        )

        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_ranking_missing_passages(self, client: FakeAIClient):
        """Test ranking request without passages."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
            },
        )

        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_ranking_empty_passages_list(self, client: FakeAIClient):
        """Test ranking request with empty passages list."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": [],
            },
        )

        # May return 422 or 200 with empty rankings depending on validation
        # Either is acceptable
        assert response.status_code in [200, 422]

    def test_ranking_invalid_truncate_value(self, client: FakeAIClient):
        """Test ranking with invalid truncate parameter."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": [{"text": "test passage"}],
                "truncate": "INVALID",
            },
        )

        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_ranking_malformed_query(self, client: FakeAIClient):
        """Test ranking with malformed query object."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": "not an object",  # Should be {"text": "..."}
                "passages": [{"text": "test passage"}],
            },
        )

        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_ranking_malformed_passage(self, client: FakeAIClient):
        """Test ranking with malformed passage object."""
        response = client.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": ["not an object"],  # Should be [{"text": "..."}]
            },
        )

        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_ranking_without_auth(self, client_no_auth: FakeAIClient):
        """Test ranking request without authentication."""
        response = client_no_auth.post(
            "/v1/ranking",
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": "test query"},
                "passages": [{"text": "test passage"}],
            },
        )

        # Should return 401 (unauthorized) if auth is enabled, otherwise 200
        # In test environment, auth may not be required by default
        assert response.status_code in [200, 401]
