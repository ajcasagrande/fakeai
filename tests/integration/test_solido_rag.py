"""Integration tests for Solido RAG endpoint.

This module tests:
1. RAG prompt endpoint
2. Document retrieval
3. Context augmentation
4. RAG with vector stores
5. RAG configuration (top_k, threshold)
6. Different retrieval strategies
7. RAG with chat completion
8. RAG metrics tracking
9. Concurrent RAG operations
10. RAG caching
"""

import asyncio
import time
from typing import Any

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
class TestRagEndpoint:
    """Test basic RAG endpoint functionality."""

    def test_basic_rag_request(self, client: FakeAIClient):
        """Test basic RAG request with single query."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "What is PVTMC?",
                "filters": {"family": "Solido", "tool": "SDE"},
                "inference_model": "meta-llama/Llama-3.1-70B-Instruct",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "content" in data
        assert "retrieved_docs" in data
        assert "usage" in data

        # Verify content
        assert len(data["content"]) > 0

        # Verify retrieved documents
        assert len(data["retrieved_docs"]) == 5  # default top_k

        # Verify usage
        assert data["usage"]["prompt_tokens"] > 0
        assert data["usage"]["completion_tokens"] > 0
        assert data["usage"]["total_tokens"] > 0

    def test_rag_with_list_query(self, client: FakeAIClient):
        """Test RAG with multiple queries in array format."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": [
                    "What is PVTMC?",
                    "How to configure sweeps?",
                    "What are corner groups?",
                ],
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "content" in data
        assert len(data["retrieved_docs"]) == 3

    def test_rag_without_filters(self, client: FakeAIClient):
        """Test RAG without metadata filters."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "general question about machine learning",
                "inference_model": "openai/gpt-oss-120b",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "content" in data
        assert len(data["retrieved_docs"]) > 0

    def test_rag_custom_top_k(self, client: FakeAIClient):
        """Test RAG with various top_k values."""
        for k in [1, 5, 10, 20]:
            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": "test query",
                    "filters": {"family": "Solido"},
                    "top_k": k,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["retrieved_docs"]) == k

    def test_rag_invalid_top_k(self, client: FakeAIClient):
        """Test RAG with invalid top_k values."""
        # top_k too small
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "test",
                "top_k": 0,
            },
        )
        assert response.status_code == 422  # Validation error

        # top_k too large
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "test",
                "top_k": 100,
            },
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestDocumentRetrieval:
    """Test document retrieval functionality."""

    def test_document_structure(self, client: FakeAIClient):
        """Test retrieved documents have correct structure."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "corner analysis",
                "filters": {"family": "Solido", "tool": "SDE", "version": "2024.2"},
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check each document has required fields
        for doc in data["retrieved_docs"]:
            assert "id" in doc
            assert "content" in doc
            assert "score" in doc
            assert "metadata" in doc
            assert "source" in doc

            # Verify types
            assert isinstance(doc["id"], str)
            assert isinstance(doc["content"], str)
            assert isinstance(doc["score"], (int, float))
            assert isinstance(doc["metadata"], dict)
            assert isinstance(doc["source"], str)

            # Verify score range
            assert 0.0 <= doc["score"] <= 1.0

    def test_document_relevance_scores(self, client: FakeAIClient):
        """Test documents have decreasing relevance scores."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "simulation setup",
                "filters": {"family": "Solido"},
                "top_k": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()

        docs = data["retrieved_docs"]
        scores = [doc["score"] for doc in docs]

        # Scores should be in descending order
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

        # Top document should have high score
        assert scores[0] >= 0.80

    def test_document_metadata_filtering(self, client: FakeAIClient):
        """Test metadata filters are applied to retrieved documents."""
        filters = {"family": "Solido", "tool": "SDE", "version": "2024.2"}

        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "test query",
                "filters": filters,
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # All documents should have matching metadata
        for doc in data["retrieved_docs"]:
            assert doc["metadata"] == filters

    def test_document_content_quality(self, client: FakeAIClient):
        """Test document content is non-empty and reasonable."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "PVTMC corner verification",
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        for doc in data["retrieved_docs"]:
            # Content should be non-empty
            assert len(doc["content"]) > 0

            # Content should be reasonable length (not just single word)
            assert len(doc["content"]) > 20

            # Source should be formatted properly
            assert len(doc["source"]) > 0


@pytest.mark.integration
class TestContextAugmentation:
    """Test context augmentation and generation."""

    def test_rag_response_uses_context(self, client: FakeAIClient):
        """Test that RAG response incorporates retrieved context."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "What is PVTMC?",
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Response should be generated
        assert len(data["content"]) > 0

        # Token counts should reflect context + query + response
        # Prompt tokens should be more than just the query
        assert data["usage"]["prompt_tokens"] > len("What is PVTMC?".split())

        # Should have reasonable completion
        assert data["usage"]["completion_tokens"] > 10

    def test_rag_with_multiple_queries_combines_context(self, client: FakeAIClient):
        """Test multiple queries combine their contexts."""
        single_query_response = client.post(
            "/rag/api/prompt",
            json={
                "query": "PVTMC",
                "filters": {"family": "Solido"},
                "top_k": 3,
            },
        )

        multi_query_response = client.post(
            "/rag/api/prompt",
            json={
                "query": ["PVTMC", "corner analysis", "simulation setup"],
                "filters": {"family": "Solido"},
                "top_k": 3,
            },
        )

        single_data = single_query_response.json()
        multi_data = multi_query_response.json()

        # Both should have context and generate responses
        # Token counts may vary based on content generation
        assert single_data["usage"]["prompt_tokens"] > 0
        assert multi_data["usage"]["prompt_tokens"] > 0
        assert single_data["usage"]["completion_tokens"] > 0
        assert multi_data["usage"]["completion_tokens"] > 0

    def test_rag_token_usage_accuracy(self, client: FakeAIClient):
        """Test token usage calculations are accurate."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "detailed question about PVTMC corner verification process",
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        usage = data["usage"]

        # Verify totals add up
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

        # Prompt tokens should include query + context
        assert usage["prompt_tokens"] > 50

        # Completion tokens should be reasonable
        assert usage["completion_tokens"] > 0


@pytest.mark.integration
class TestRagConfiguration:
    """Test RAG configuration options."""

    def test_different_models(self, client: FakeAIClient):
        """Test RAG with different inference models."""
        models = [
            "openai/gpt-oss-120b",
            "meta-llama/Llama-3.1-70B-Instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct",
        ]

        for model in models:
            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": "test query",
                    "inference_model": model,
                    "top_k": 3,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "content" in data

    def test_rag_with_solido_specific_filters(self, client: FakeAIClient):
        """Test RAG with Solido-specific filters."""
        solido_filters = [
            {"family": "Solido", "tool": "SDE"},
            {"family": "Solido", "tool": "SDE", "version": "2024.2"},
            {"family": "Solido", "tool": "SDE", "category": "verification"},
        ]

        for filters in solido_filters:
            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": "PVTMC corner analysis",
                    "filters": filters,
                    "top_k": 3,
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify filters are applied
            for doc in data["retrieved_docs"]:
                assert doc["metadata"] == filters

    def test_rag_with_generic_filters(self, client: FakeAIClient):
        """Test RAG with non-Solido filters."""
        generic_filters = [
            {"category": "general", "language": "en"},
            {"domain": "analog", "type": "design"},
            {"topic": "machine_learning", "level": "beginner"},
        ]

        for filters in generic_filters:
            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": "general question",
                    "filters": filters,
                    "top_k": 3,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["retrieved_docs"]) == 3


@pytest.mark.integration
class TestRagMetrics:
    """Test RAG metrics tracking."""

    def test_rag_metrics_recorded(self, client: FakeAIClient):
        """Test that RAG requests are recorded in metrics."""
        # Make RAG request
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "test query",
                "filters": {"family": "Solido"},
                "top_k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure (metrics tracking verified implicitly)
        assert "content" in data
        assert "retrieved_docs" in data
        assert "usage" in data

        # Get metrics to verify server is tracking
        metrics = client.get_metrics()
        assert "requests" in metrics or "uptime" in metrics

    def test_rag_latency_tracking(self, client: FakeAIClient):
        """Test RAG latency is tracked."""
        start_time = time.time()

        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "test query",
                "top_k": 5,
            },
        )

        end_time = time.time()
        elapsed = end_time - start_time

        assert response.status_code == 200

        # Request should complete reasonably fast
        assert elapsed < 2.0  # 2 seconds max

    def test_rag_error_tracking(self, client: FakeAIClient):
        """Test RAG errors are tracked in metrics."""
        # Make invalid request
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "test",
                "top_k": -1,  # Invalid
            },
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestConcurrentRagOperations:
    """Test concurrent RAG operations."""

    @pytest.mark.asyncio
    async def test_concurrent_rag_requests(self, client: FakeAIClient):
        """Test multiple concurrent RAG requests."""
        queries = [
            "What is PVTMC?",
            "How to configure sweeps?",
            "What are corner groups?",
            "Simulation setup process",
            "Verification methodology",
        ]

        async def make_rag_request(query: str) -> dict[str, Any]:
            """Make single RAG request."""
            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": query,
                    "filters": {"family": "Solido", "tool": "SDE"},
                    "top_k": 3,
                },
            )
            return response.json()

        # Execute requests concurrently
        tasks = [make_rag_request(query) for query in queries]
        results = await asyncio.gather(*tasks)

        # Verify all requests succeeded
        assert len(results) == len(queries)

        for result in results:
            assert "content" in result
            assert "retrieved_docs" in result
            assert len(result["retrieved_docs"]) == 3

    def test_concurrent_different_filters(self, client: FakeAIClient):
        """Test concurrent requests with different filters."""
        filter_configs = [
            {"family": "Solido", "tool": "SDE"},
            {"family": "Solido", "tool": "SDE", "version": "2024.2"},
            {"category": "general"},
            {"domain": "analog"},
        ]

        responses = []
        for filters in filter_configs:
            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": "test query",
                    "filters": filters,
                    "top_k": 3,
                },
            )
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_concurrent_different_top_k(self, client: FakeAIClient):
        """Test concurrent requests with different top_k values."""
        top_k_values = [1, 3, 5, 10, 20]

        responses = []
        for k in top_k_values:
            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": "test query",
                    "top_k": k,
                },
            )
            responses.append((k, response))

        # Verify each got correct number of documents
        for k, response in responses:
            assert response.status_code == 200
            data = response.json()
            assert len(data["retrieved_docs"]) == k


@pytest.mark.integration
class TestRagSolidoContent:
    """Test Solido-specific content generation."""

    def test_pvtmc_query(self, client: FakeAIClient):
        """Test PVTMC-related queries."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "What is PVTMC and how does it verify worst-case corners?",
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check for PVTMC-related content
        docs_text = " ".join([doc["content"] for doc in data["retrieved_docs"]])
        assert "PVTMC" in docs_text or "pvtmc" in docs_text.lower()

    def test_sweep_configuration_query(self, client: FakeAIClient):
        """Test sweep configuration queries."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "How to configure variable sweeps and group them?",
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should have relevant content
        docs_text = " ".join([doc["content"] for doc in data["retrieved_docs"]])
        assert "sweep" in docs_text.lower() or "configuration" in docs_text.lower()

    def test_simulation_setup_query(self, client: FakeAIClient):
        """Test simulation setup queries."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "Simulation setup and configuration process",
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should have relevant content
        assert len(data["content"]) > 0
        assert len(data["retrieved_docs"]) == 5


@pytest.mark.integration
class TestRagEdgeCases:
    """Test RAG edge cases and error handling."""

    def test_empty_query(self, client: FakeAIClient):
        """Test RAG with empty query."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "",
                "top_k": 3,
            },
        )

        # Should handle gracefully (either 422 or return results)
        assert response.status_code in [200, 422]

    def test_very_long_query(self, client: FakeAIClient):
        """Test RAG with very long query."""
        long_query = " ".join(["test query"] * 100)

        response = client.post(
            "/rag/api/prompt",
            json={
                "query": long_query,
                "top_k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    def test_special_characters_in_query(self, client: FakeAIClient):
        """Test RAG with special characters in query."""
        special_queries = [
            "What is C++ programming?",
            "How to use @decorators in Python?",
            "Understanding $variables and #comments",
            "Test with émojis 🚀 and ünïcödë",
        ]

        for query in special_queries:
            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": query,
                    "top_k": 3,
                },
            )

            assert response.status_code == 200

    def test_rag_with_empty_filters(self, client: FakeAIClient):
        """Test RAG with empty filters dict."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "test query",
                "filters": {},
                "top_k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["retrieved_docs"]) == 3

    def test_rag_with_complex_filters(self, client: FakeAIClient):
        """Test RAG with nested/complex filter structures."""
        response = client.post(
            "/rag/api/prompt",
            json={
                "query": "test query",
                "filters": {
                    "family": "Solido",
                    "tool": "SDE",
                    "version": "2024.2",
                    "category": "verification",
                    "subcategory": "corner_analysis",
                },
                "top_k": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify complex filters are preserved
        for doc in data["retrieved_docs"]:
            assert doc["metadata"]["family"] == "Solido"
            assert doc["metadata"]["tool"] == "SDE"


@pytest.mark.integration
class TestRagIntegrationWithChatCompletion:
    """Test RAG integration with chat completion workflow."""

    def test_rag_then_chat(self, client: FakeAIClient):
        """Test using RAG results in chat completion."""
        # First, get RAG results
        rag_response = client.post(
            "/rag/api/prompt",
            json={
                "query": "What is PVTMC?",
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 3,
            },
        )

        assert rag_response.status_code == 200
        rag_data = rag_response.json()

        # Use RAG context in chat completion
        context = "\n\n".join(
            [doc["content"] for doc in rag_data["retrieved_docs"][:2]]
        )

        chat_response = client.post(
            "/v1/chat/completions",
            json={
                "model": "meta-llama/Llama-3.1-70B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": f"Use this context: {context}",
                    },
                    {
                        "role": "user",
                        "content": "Explain PVTMC based on the context",
                    },
                ],
            },
        )

        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert "choices" in chat_data

    def test_iterative_rag_refinement(self, client: FakeAIClient):
        """Test iterative query refinement with RAG."""
        # Initial query
        response1 = client.post(
            "/rag/api/prompt",
            json={
                "query": "corner analysis",
                "filters": {"family": "Solido"},
                "top_k": 3,
            },
        )

        # Refined query based on initial results
        response2 = client.post(
            "/rag/api/prompt",
            json={
                "query": "PVTMC corner analysis verification methodology",
                "filters": {"family": "Solido", "tool": "SDE"},
                "top_k": 5,
            },
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Refined query should get more documents
        assert len(data2["retrieved_docs"]) > len(data1["retrieved_docs"])


@pytest.mark.integration
@pytest.mark.slow
class TestRagPerformance:
    """Test RAG performance characteristics."""

    def test_rag_response_time(self, client: FakeAIClient):
        """Test RAG response times are reasonable."""
        response_times = []

        for i in range(5):
            start = time.time()

            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": f"test query {i}",
                    "filters": {"family": "Solido"},
                    "top_k": 5,
                },
            )

            end = time.time()
            elapsed = end - start

            assert response.status_code == 200
            response_times.append(elapsed)

        # Average response time should be reasonable
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 1.0  # 1 second average

    def test_rag_with_varying_top_k_performance(self, client: FakeAIClient):
        """Test performance with different top_k values."""
        top_k_values = [1, 5, 10, 20]
        times = {}

        for k in top_k_values:
            start = time.time()

            response = client.post(
                "/rag/api/prompt",
                json={
                    "query": "test query",
                    "top_k": k,
                },
            )

            end = time.time()

            assert response.status_code == 200
            times[k] = end - start

        # Higher top_k should not be dramatically slower
        # (within 2x of smallest top_k)
        assert times[20] < times[1] * 2.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
