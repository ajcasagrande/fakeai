#!/usr/bin/env python3
"""
Example demonstrating Solido RAG (Retrieval-Augmented Generation) endpoint.

This example shows how to use the Solido RAG API for:
- Document retrieval with metadata filters
- Context-augmented generation
- Solido Design Environment documentation queries
"""
import asyncio
import json

from fakeai import AppConfig, FakeAIService
from fakeai.models import SolidoRagRequest


async def example_pvtmc_query():
    """Example querying about PVTMC verification."""
    print("=" * 70)
    print("Example 1: PVTMC Corner Verification Query")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = SolidoRagRequest(
        query="What is PVTMC and how does it verify worst-case corners?",
        filters={"family": "Solido", "tool": "SDE"},
        inference_model="meta-llama/Llama-3.1-70B-Instruct",
        top_k=3,
    )

    response = await service.create_solido_rag(request)

    print(f"\nGenerated Answer:")
    print(f"  {response['content']}\n")

    print(f"Retrieved Documents ({len(response['retrieved_docs'])}):")
    for i, doc in enumerate(response["retrieved_docs"], 1):
        print(f"\n  [{i}] Score: {doc['score']:.3f}")
        print(f"      Source: {doc['source']}")
        print(f"      Content: {doc['content'][:100]}...")

    print(f"\nToken Usage:")
    print(f"  - Prompt: {response['usage']['prompt_tokens']}")
    print(f"  - Completion: {response['usage']['completion_tokens']}")
    print(f"  - Total: {response['usage']['total_tokens']}")
    print()


async def example_sweep_configuration():
    """Example querying about sweep configuration."""
    print("=" * 70)
    print("Example 2: Sweep Configuration Query")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = SolidoRagRequest(
        query="How do I configure variable sweeps and group them?",
        filters={"family": "Solido", "tool": "SDE", "version": "2024.2"},
        inference_model="meta-llama/Llama-3.1-70B-Instruct",
        top_k=5,
    )

    response = await service.create_solido_rag(request)

    print(f"\nGenerated Answer:")
    print(f"  {response['content']}\n")

    print(f"Top 3 Retrieved Documents:")
    for i, doc in enumerate(response["retrieved_docs"][:3], 1):
        print(f"\n  [{i}] {doc['source']} (score: {doc['score']:.3f})")
        print(f"      {doc['content'][:150]}...")

    print()


async def example_multiple_queries():
    """Example with multiple queries in array format."""
    print("=" * 70)
    print("Example 3: Multiple Queries (Array Format)")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = SolidoRagRequest(
        query=[
            "What is simulation setup?",
            "How to configure test parameters?",
            "What are corner groups?",
        ],
        filters={"family": "Solido", "tool": "SDE"},
        inference_model="meta-llama/Llama-3.1-70B-Instruct",
        top_k=4,
    )

    response = await service.create_solido_rag(request)

    print(f"\nQueries Combined:")
    print(f"  {' '.join(request.query)}\n")

    print(f"Generated Answer:")
    print(f"  {response['content']}\n")

    print(f"Retrieved Documents: {len(response['retrieved_docs'])}")
    print(f"Top document score: {response['retrieved_docs'][0]['score']:.3f}")
    print()


async def example_generic_rag():
    """Example with generic (non-Solido) filters."""
    print("=" * 70)
    print("Example 4: Generic RAG Query")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = SolidoRagRequest(
        query="What are best practices for IC design?",
        filters={"category": "design", "domain": "analog"},
        inference_model="meta-llama/Llama-3.1-70B-Instruct",
        top_k=3,
    )

    response = await service.create_solido_rag(request)

    print(f"\nGenerated Answer:")
    print(f"  {response['content']}\n")

    print(f"Retrieved: {len(response['retrieved_docs'])} documents")
    print(f"Token usage: {response['usage']['total_tokens']} total tokens")
    print()


async def main():
    """Run all Solido RAG examples."""
    await example_pvtmc_query()
    await example_sweep_configuration()
    await example_multiple_queries()
    await example_generic_rag()

    print("=" * 70)
    print("All Solido RAG examples completed successfully! ✅")
    print("=" * 70)
    print()
    print("Solido RAG Endpoint: POST /rag/api/prompt")
    print()
    print("Request Format:")
    print(
        json.dumps(
            {
                "query": "your question or [array, of, queries]",
                "filters": {"family": "Solido", "tool": "SDE"},
                "inference_model": "meta-llama/Llama-3.1-70B-Instruct",
                "top_k": 5,
            },
            indent=2,
        )
    )
    print()
    print("Response Format:")
    print(
        json.dumps(
            {
                "content": "generated answer with RAG context...",
                "retrieved_docs": [
                    {
                        "id": "doc-abc123",
                        "content": "document content...",
                        "score": 0.95,
                        "source": "Solido_SDE_User_Guide_p100",
                    }
                ],
                "usage": {
                    "prompt_tokens": 450,
                    "completion_tokens": 120,
                    "total_tokens": 570,
                },
            },
            indent=2,
        )
    )
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
