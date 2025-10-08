"""
Tests for KV cache-aware TTFT speedup functionality.

These tests verify that KV cache hits significantly reduce Time To First Token (TTFT)
in streaming responses, simulating the performance benefits of AI-Dynamo's KV cache reuse.
"""

import time

import pytest

from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role


@pytest.mark.asyncio
async def test_full_cache_hit_reduces_ttft():
    """Test that 100% cache hit dramatically reduces TTFT (80% reduction)."""
    # Configure service with known TTFT baseline
    config = AppConfig(
        ttft_ms=1000.0,  # 1 second baseline
        ttft_variance_percent=0.0,  # No variance for predictable testing
        itl_ms=10.0,
        itl_variance_percent=0.0,
    )
    service = FakeAIService(config)

    # First request - no cache hit (cold start)
    request1 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="What is machine learning?")],
        stream=True,
        max_tokens=10,
    )

    start1 = time.time()
    chunks1 = []
    first_token_received = False
    async for chunk in service.create_chat_completion_stream(request1):
        chunks1.append(chunk)
        if (
            not first_token_received and len(chunks1) == 2
        ):  # After role chunk + first content chunk
            ttft1 = time.time() - start1
            first_token_received = True
        # Continue consuming to complete the stream and populate cache

    # Second request - same prompt (should hit cache)
    request2 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="What is machine learning?")],
        stream=True,
        max_tokens=10,
    )

    start2 = time.time()
    chunks2 = []
    first_token_received2 = False
    async for chunk in service.create_chat_completion_stream(request2):
        chunks2.append(chunk)
        if (
            not first_token_received2 and len(chunks2) == 2
        ):  # After role chunk + first content chunk
            ttft2 = time.time() - start2
            first_token_received2 = True

    # Verify TTFT speedup
    # 100% cache hit should reduce TTFT by ~80%
    # So TTFT2 should be ~20% of TTFT1
    speedup_ratio = ttft1 / ttft2
    print(f"TTFT1 (no cache): {ttft1:.3f}s")
    print(f"TTFT2 (full cache): {ttft2:.3f}s")
    print(f"Speedup ratio: {speedup_ratio:.2f}x")

    # With 80% reduction, we expect ~5x speedup (1.0 / 0.2 = 5.0)
    # Allow some tolerance for timing variance
    assert speedup_ratio > 3.0, f"Expected >3x speedup, got {speedup_ratio:.2f}x"
    assert ttft2 < 0.5, f"Expected TTFT2 < 0.5s with cache hit, got {ttft2:.3f}s"


@pytest.mark.asyncio
async def test_partial_cache_hit_scales_reduction():
    """Test that partial cache hits provide proportional TTFT reduction."""
    config = AppConfig(
        ttft_ms=1000.0,
        ttft_variance_percent=0.0,
        itl_ms=10.0,
    )
    service = FakeAIService(config)

    # First request - establish cache with a longer prompt
    request1 = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            Message(
                role=Role.USER,
                content="The quick brown fox jumps over the lazy dog and runs away quickly",
            )
        ],
        stream=True,
        max_tokens=10,
    )

    first_token_received1 = False
    async for chunk in service.create_chat_completion_stream(request1):
        if not first_token_received1 and len([c for c in [chunk]]) == 1:
            first_token_received1 = True
        # Complete the stream to populate cache

    # Second request - partial overlap at start
    request2 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="The quick brown fox jumps")],
        stream=True,
        max_tokens=10,
    )

    start2 = time.time()
    chunks2 = []
    first_token_received2 = False
    async for chunk in service.create_chat_completion_stream(request2):
        chunks2.append(chunk)
        if not first_token_received2 and len(chunks2) == 2:
            ttft2 = time.time() - start2
            first_token_received2 = True

    # Third request - no cache (completely different)
    request3 = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            Message(
                role=Role.USER, content="Python programming language basics explained"
            )
        ],
        stream=True,
        max_tokens=10,
    )

    start3 = time.time()
    chunks3 = []
    first_token_received3 = False
    async for chunk in service.create_chat_completion_stream(request3):
        chunks3.append(chunk)
        if not first_token_received3 and len(chunks3) == 2:
            ttft3 = time.time() - start3
            first_token_received3 = True

    # TTFT2 (partial cache) should be faster than TTFT3 (no cache)
    speedup_ratio = ttft3 / ttft2
    print(f"TTFT2 (partial cache): {ttft2:.3f}s")
    print(f"TTFT3 (no cache): {ttft3:.3f}s")
    print(f"Speedup ratio (partial vs no cache): {speedup_ratio:.2f}x")

    # Expect modest speedup for partial cache hit compared to no cache
    assert speedup_ratio > 1.2, f"Expected >1.2x speedup, got {speedup_ratio:.2f}x"
    assert ttft2 < ttft3, "TTFT should be faster with partial cache hit than no cache"


@pytest.mark.asyncio
async def test_no_cache_hit_normal_ttft():
    """Test that requests with no cache hit use baseline TTFT."""
    config = AppConfig(
        ttft_ms=500.0,
        ttft_variance_percent=10.0,  # Allow 10% variance
        itl_ms=10.0,
    )
    service = FakeAIService(config)

    # Completely different prompts (no cache hits)
    prompts = [
        "What is quantum mechanics?",
        "How do airplanes fly?",
        "Explain photosynthesis",
    ]

    ttfts = []
    for prompt in prompts:
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[Message(role=Role.USER, content=prompt)],
            stream=True,
            max_tokens=10,
        )

        start = time.time()
        chunks = []
        async for chunk in service.create_chat_completion_stream(request):
            chunks.append(chunk)
            if len(chunks) == 2:  # After role + first content
                ttft = time.time() - start
                ttfts.append(ttft)
                break

    # All TTFTs should be similar (within variance range)
    avg_ttft = sum(ttfts) / len(ttfts)
    print(f"TTFTs (no cache): {[f'{t:.3f}' for t in ttfts]}")
    print(f"Average TTFT: {avg_ttft:.3f}s")

    # Should be close to baseline (500ms ± 10%)
    assert 0.4 < avg_ttft < 0.6, f"Expected TTFT ~0.5s, got {avg_ttft:.3f}s"

    # Variance should be small (all within 20% of mean)
    for ttft in ttfts:
        assert (
            abs(ttft - avg_ttft) / avg_ttft < 0.2
        ), f"TTFT {ttft:.3f}s deviates too much from mean {avg_ttft:.3f}s"


@pytest.mark.asyncio
async def test_speedup_tracked_in_metrics():
    """Test that cache speedup is properly tracked in KV cache metrics."""
    config = AppConfig(
        ttft_ms=1000.0,
        ttft_variance_percent=0.0,
    )
    service = FakeAIService(config)

    # Make requests with varying cache hits
    requests = [
        # First request - no cache
        Message(role=Role.USER, content="Python programming language"),
        # Second request - same content (full cache hit)
        Message(role=Role.USER, content="Python programming language"),
        # Third request - different content (no cache)
        Message(role=Role.USER, content="JavaScript web development"),
    ]

    for msg in requests:
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[msg],
            stream=True,
            max_tokens=10,
        )

        # Consume stream to trigger metrics recording
        async for _ in service.create_chat_completion_stream(request):
            pass

    # Check metrics
    stats = service.kv_cache_metrics.get_stats()
    speedup_stats = stats.get("speedup_stats", {})

    print(f"Cache hit rate: {stats['cache_hit_rate']}%")
    print(f"Speedup stats: {speedup_stats}")

    # Should have speedup records
    assert speedup_stats, "Expected speedup stats to be present"
    assert (
        speedup_stats["total_speedup_records"] >= 3
    ), f"Expected at least 3 speedup records, got {speedup_stats['total_speedup_records']}"

    # Average speedup ratio should be > 1.0 (we had cache hits)
    assert (
        speedup_stats["avg_speedup_ratio"] >= 1.0
    ), f"Expected avg speedup >= 1.0x, got {speedup_stats['avg_speedup_ratio']:.2f}x"

    # Baseline TTFT should match config
    assert (
        speedup_stats["avg_baseline_ttft_ms"] == 1000.0
    ), f"Expected baseline 1000ms, got {speedup_stats['avg_baseline_ttft_ms']}ms"


@pytest.mark.asyncio
async def test_streaming_and_nonstreaming():
    """Test that both streaming and non-streaming benefit from cache (via routing)."""
    config = AppConfig(
        ttft_ms=1000.0,
        ttft_variance_percent=0.0,
    )
    service = FakeAIService(config)

    # First request - streaming (establishes cache)
    request1 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Machine learning basics")],
        stream=True,
        max_tokens=10,
    )

    start_stream = time.time()
    chunks = []
    async for chunk in service.create_chat_completion_stream(request1):
        chunks.append(chunk)
        if len(chunks) == 2:
            ttft_stream = time.time() - start_stream
            break

    # Complete the stream
    async for _ in service.create_chat_completion_stream(request1):
        pass

    # Second request - same content but non-streaming
    # Non-streaming doesn't have TTFT delay but benefits from KV cache routing
    request2 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Machine learning basics")],
        stream=False,
        max_tokens=10,
    )

    start_nonstream = time.time()
    response = await service.create_chat_completion(request2)
    duration_nonstream = time.time() - start_nonstream

    # Third request - streaming again (should be faster due to cache)
    request3 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Machine learning basics")],
        stream=True,
        max_tokens=10,
    )

    start_stream2 = time.time()
    chunks2 = []
    async for chunk in service.create_chat_completion_stream(request3):
        chunks2.append(chunk)
        if len(chunks2) == 2:
            ttft_stream2 = time.time() - start_stream2
            break

    print(f"First stream TTFT: {ttft_stream:.3f}s")
    print(f"Non-stream duration: {duration_nonstream:.3f}s")
    print(f"Second stream TTFT: {ttft_stream2:.3f}s")

    # Second streaming request should be faster
    speedup = ttft_stream / ttft_stream2
    assert speedup > 2.0, f"Expected >2x speedup on cached stream, got {speedup:.2f}x"

    # Check that cache metrics recorded both streaming requests
    stats = service.kv_cache_metrics.get_stats()
    assert stats["total_cache_hits"] >= 1, "Expected at least one cache hit"


@pytest.mark.asyncio
async def test_cache_hit_ratio_calculation():
    """Test that cache hit ratio is calculated correctly for speedup."""
    config = AppConfig(
        ttft_ms=1000.0,
        ttft_variance_percent=0.0,
    )
    service = FakeAIService(config)

    # Request with long prompt to establish cache
    long_prompt = (
        "Artificial intelligence machine learning deep learning neural networks " * 10
    )
    request1 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content=long_prompt)],
        stream=True,
        max_tokens=10,
    )

    # Consume first request
    async for _ in service.create_chat_completion_stream(request1):
        pass

    # Second request - same prompt (100% cache hit)
    request2 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content=long_prompt)],
        stream=True,
        max_tokens=10,
    )

    start = time.time()
    chunks = []
    async for chunk in service.create_chat_completion_stream(request2):
        chunks.append(chunk)
        if len(chunks) == 2:
            ttft = time.time() - start
            break

    # Check speedup stats
    stats = service.kv_cache_metrics.get_stats()
    speedup_stats = stats["speedup_stats"]

    print(f"TTFT with 100% cache: {ttft:.3f}s")
    print(f"Average cache hit ratio: {speedup_stats['avg_cache_hit_ratio']:.1f}%")
    print(f"Average speedup ratio: {speedup_stats['avg_speedup_ratio']:.2f}x")

    # For the second request, cache hit ratio should be high
    # (Note: might not be exactly 100% due to tokenization, but should be >=50%)
    assert (
        speedup_stats["avg_cache_hit_ratio"] >= 50.0
    ), f"Expected cache hit ratio >=50%, got {speedup_stats['avg_cache_hit_ratio']:.1f}%"

    # Speedup should correlate with cache hit ratio
    assert (
        speedup_stats["avg_speedup_ratio"] > 1.5
    ), f"Expected speedup >1.5x with high cache hit, got {speedup_stats['avg_speedup_ratio']:.2f}x"


@pytest.mark.asyncio
async def test_different_models_same_cache_benefits():
    """Test that different models can benefit from same cache (via shared KV cache router)."""
    config = AppConfig(
        ttft_ms=1000.0,
        ttft_variance_percent=0.0,
    )
    service = FakeAIService(config)

    # First request with one model
    request1 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Climate change effects")],
        stream=True,
        max_tokens=10,
    )

    start1 = time.time()
    chunks1 = []
    async for chunk in service.create_chat_completion_stream(request1):
        chunks1.append(chunk)
        if len(chunks1) == 2:
            ttft1 = time.time() - start1
            break

    # Complete first request
    async for _ in service.create_chat_completion_stream(request1):
        pass

    # Second request with different model but same content
    request2 = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[Message(role=Role.USER, content="Climate change effects")],
        stream=True,
        max_tokens=10,
    )

    start2 = time.time()
    chunks2 = []
    async for chunk in service.create_chat_completion_stream(request2):
        chunks2.append(chunk)
        if len(chunks2) == 2:
            ttft2 = time.time() - start2
            break

    print(f"TTFT1 (gpt-4): {ttft1:.3f}s")
    print(f"TTFT2 (gpt-3.5-turbo): {ttft2:.3f}s")

    # Different models share KV cache, so should see speedup
    speedup = ttft1 / ttft2
    assert speedup > 2.0, f"Expected >2x speedup across models, got {speedup:.2f}x"


@pytest.mark.asyncio
async def test_variance_still_applied_with_cache():
    """Test that TTFT variance is still applied even with cache hits."""
    config = AppConfig(
        ttft_ms=1000.0,
        ttft_variance_percent=20.0,  # 20% variance
    )
    service = FakeAIService(config)

    # Establish cache
    request1 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Renewable energy sources")],
        stream=True,
        max_tokens=10,
    )

    async for _ in service.create_chat_completion_stream(request1):
        pass

    # Make multiple requests with same prompt to observe variance
    ttfts = []
    for _ in range(5):
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[Message(role=Role.USER, content="Renewable energy sources")],
            stream=True,
            max_tokens=10,
        )

        start = time.time()
        chunks = []
        async for chunk in service.create_chat_completion_stream(request):
            chunks.append(chunk)
            if len(chunks) == 2:
                ttft = time.time() - start
                ttfts.append(ttft)
                break

    print(f"TTFTs with cache and variance: {[f'{t:.3f}' for t in ttfts]}")

    # All should be fast (due to cache) but with variance
    avg_ttft = sum(ttfts) / len(ttfts)
    assert avg_ttft < 0.5, f"Expected avg TTFT < 0.5s with cache, got {avg_ttft:.3f}s"

    # Should see variance (not all identical)
    min_ttft = min(ttfts)
    max_ttft = max(ttfts)
    variance_range = (max_ttft - min_ttft) / avg_ttft

    print(f"Variance range: {variance_range:.2%}")
    assert variance_range > 0.1, "Expected to see some variance in TTFT with 20% config"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
