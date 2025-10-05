"""
Tests for Solido RAG endpoint.
"""
#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import SolidoRagRequest


class TestSolidoRagEndpoint:
    """Test Solido RAG endpoint functionality."""

    @pytest.mark.asyncio
    async def test_basic_rag_request(self):
        """Test basic RAG request with single query."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = SolidoRagRequest(
            query="What is PVTMC?",
            filters={"family": "Solido", "tool": "SDE"},
            inference_model="meta-llama/Llama-3.1-70B-Instruct"
        )

        response = await service.create_solido_rag(request)

        assert "content" in response
        assert len(response["content"]) > 0
        assert "retrieved_docs" in response
        assert len(response["retrieved_docs"]) == 5  # default top_k
        assert "usage" in response
        assert response["usage"]["total_tokens"] > 0

    @pytest.mark.asyncio
    async def test_rag_with_list_query(self):
        """Test RAG with list of queries."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = SolidoRagRequest(
            query=["What is PVTMC?", "How to configure sweeps?"],
            filters={"family": "Solido", "tool": "SDE"},
            inference_model="meta-llama/Llama-3.1-70B-Instruct",
            top_k=3
        )

        response = await service.create_solido_rag(request)

        assert "content" in response
        assert len(response["retrieved_docs"]) == 3

    @pytest.mark.asyncio
    async def test_rag_document_metadata(self):
        """Test retrieved documents have correct metadata."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        filters = {"family": "Solido", "tool": "SDE", "version": "2024.2"}
        request = SolidoRagRequest(
            query="corner analysis",
            filters=filters,
            inference_model="meta-llama/Llama-3.1-70B-Instruct"
        )

        response = await service.create_solido_rag(request)

        # Check document structure
        for doc in response["retrieved_docs"]:
            assert "id" in doc
            assert "content" in doc
            assert "score" in doc
            assert "metadata" in doc
            assert "source" in doc

            # Check metadata matches filters
            assert doc["metadata"] == filters

            # Check score is valid
            assert 0.0 <= doc["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_rag_relevance_scores(self):
        """Test documents have decreasing relevance scores."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = SolidoRagRequest(
            query="simulation setup",
            filters={"family": "Solido"},
            top_k=5
        )

        response = await service.create_solido_rag(request)

        docs = response["retrieved_docs"]
        scores = [doc["score"] for doc in docs]

        # Scores should be in descending order
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

        # Top document should have highest score
        assert scores[0] >= 0.85

    @pytest.mark.asyncio
    async def test_rag_solido_content(self):
        """Test Solido-specific content generation."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        queries_and_keywords = [
            ("What is PVTMC?", "PVTMC"),
            ("How to configure sweeps?", "sweep"),
            ("Simulation setup", "simulation"),
        ]

        for query, keyword in queries_and_keywords:
            request = SolidoRagRequest(
                query=query,
                filters={"family": "Solido", "tool": "SDE"},
                top_k=3
            )

            response = await service.create_solido_rag(request)

            # At least one document should mention the keyword
            docs_text = " ".join([doc["content"] for doc in response["retrieved_docs"]])
            assert keyword.lower() in docs_text.lower()

    @pytest.mark.asyncio
    async def test_rag_generic_filters(self):
        """Test RAG with non-Solido filters."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = SolidoRagRequest(
            query="general question",
            filters={"category": "general", "language": "en"},
            top_k=3
        )

        response = await service.create_solido_rag(request)

        assert len(response["retrieved_docs"]) == 3
        # Should still generate documents, just generic content
        for doc in response["retrieved_docs"]:
            assert len(doc["content"]) > 0

    @pytest.mark.asyncio
    async def test_rag_no_filters(self):
        """Test RAG without filters."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = SolidoRagRequest(
            query="test query",
            inference_model="meta-llama/Llama-3.1-70B-Instruct"
        )

        response = await service.create_solido_rag(request)

        assert "content" in response
        assert len(response["retrieved_docs"]) > 0

    @pytest.mark.asyncio
    async def test_rag_custom_top_k(self):
        """Test RAG with custom top_k value."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        for k in [1, 3, 10, 20]:
            request = SolidoRagRequest(
                query="test",
                filters={"family": "Solido"},
                top_k=k
            )

            response = await service.create_solido_rag(request)
            assert len(response["retrieved_docs"]) == k

    @pytest.mark.asyncio
    async def test_rag_token_usage(self):
        """Test RAG includes proper token usage."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = SolidoRagRequest(
            query="detailed question about PVTMC corner verification",
            filters={"family": "Solido", "tool": "SDE"},
            top_k=5
        )

        response = await service.create_solido_rag(request)

        usage = response["usage"]
        assert usage["prompt_tokens"] > 0
        assert usage["completion_tokens"] > 0
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

        # Prompt tokens should include query and retrieved context
        assert usage["prompt_tokens"] > 50




if __name__ == "__main__":
    pytest.main([__file__, "-v"])
