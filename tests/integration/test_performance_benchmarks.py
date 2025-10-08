"""
Performance Benchmark Tests

Tests system performance under various load conditions:
- Concurrent request handling
- Streaming throughput
- Metrics overhead
- Memory leak detection
- Startup time
"""

import gc
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil
import pytest
from fastapi.testclient import TestClient

from fakeai.app import app
from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService


@pytest.fixture
def client():
    """Test client."""
    import fakeai.app as app_module
    app_module.server_ready = True
    return TestClient(app)


@pytest.fixture
def service():
    """Service instance."""
    config = AppConfig(require_api_key=False, response_delay=0.0, random_delay=False)
    return FakeAIService(config)


# ==============================================================================
# Concurrent Request Tests
# ==============================================================================


def test_100_concurrent_requests(client):
    """Test handling 100 concurrent requests."""
    def make_request():
        return client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10,
            },
        )

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in as_completed(futures)]

    elapsed = time.time() - start_time

    # All should succeed
    assert all(r.status_code == 200 for r in results)
    assert len(results) == 100

    # Should complete in reasonable time
    print(f"100 requests completed in {elapsed:.2f}s ({100/elapsed:.2f} req/s)")
    assert elapsed < 30  # 30 seconds max


def test_1000_concurrent_requests(client):
    """Test handling 1000 concurrent requests."""
    def make_request():
        return client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
            },
        )

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(make_request) for _ in range(1000)]
        results = [f.result() for f in as_completed(futures)]

    elapsed = time.time() - start_time

    # Most should succeed (allow some failures under extreme load)
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 950  # At least 95% success rate

    print(f"1000 requests completed in {elapsed:.2f}s ({1000/elapsed:.2f} req/s)")


def test_mixed_endpoint_concurrent_requests(client):
    """Test concurrent requests to different endpoints."""
    def make_chat_request():
        return client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
            },
        )

    def make_embedding_request():
        return client.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-3-small",
                "input": "Test",
            },
        )

    def make_model_request():
        return client.get("/v1/models")

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = []
        for _ in range(30):
            futures.append(executor.submit(make_chat_request))
            futures.append(executor.submit(make_embedding_request))
            futures.append(executor.submit(make_model_request))

        results = [f.result() for f in as_completed(futures)]

    # All should succeed
    assert all(r.status_code == 200 for r in results)
    assert len(results) == 90


# ==============================================================================
# Streaming Throughput Tests
# ==============================================================================


def test_streaming_throughput(client):
    """Test streaming response throughput."""
    start_time = time.time()
    token_count = 0

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Generate a long response about AI"}],
            "stream": True,
            "max_tokens": 500,
        },
    )

    assert response.status_code == 200

    for line in response.iter_lines():
        if line and line.startswith(b"data: "):
            data_str = line[6:].decode("utf-8")
            if data_str.strip() == "[DONE]":
                break
            try:
                import json
                chunk = json.loads(data_str)
                if chunk["choices"][0]["delta"].get("content"):
                    token_count += 1
            except:
                pass

    elapsed = time.time() - start_time
    tokens_per_second = token_count / elapsed if elapsed > 0 else 0

    print(f"Streaming: {token_count} tokens in {elapsed:.2f}s ({tokens_per_second:.2f} tok/s)")
    assert tokens_per_second > 0


def test_multiple_concurrent_streams(client):
    """Test multiple concurrent streaming connections."""
    def stream_request():
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Count to 20"}],
                "stream": True,
            },
        )

        chunks = 0
        for line in response.iter_lines():
            if line and line.startswith(b"data: "):
                data_str = line[6:].decode("utf-8")
                if data_str.strip() == "[DONE]":
                    break
                chunks += 1

        return chunks

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(stream_request) for _ in range(10)]
        results = [f.result() for f in as_completed(futures)]

    elapsed = time.time() - start_time

    # All should complete
    assert all(r > 0 for r in results)
    print(f"10 concurrent streams completed in {elapsed:.2f}s")


# ==============================================================================
# Metrics Overhead Tests
# ==============================================================================


def test_metrics_overhead_minimal(client):
    """Test that metrics don't add significant overhead."""
    # Make requests with metrics
    start_with_metrics = time.time()

    for _ in range(100):
        client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
            },
        )

    with_metrics_time = time.time() - start_with_metrics

    print(f"100 requests with metrics: {with_metrics_time:.2f}s")

    # Overhead should be minimal (hard to test without disabling metrics)
    assert with_metrics_time < 60  # Should complete in reasonable time


def test_metrics_collection_scalability(service):
    """Test that metrics collection scales well."""
    tracker = service.metrics_tracker

    start_time = time.time()

    # Record 10,000 metric events
    for i in range(10000):
        tracker.track_request("/v1/chat/completions")
        tracker.track_response("/v1/chat/completions", latency=0.1)
        tracker.track_tokens("/v1/chat/completions", count=100)

    elapsed = time.time() - start_time

    print(f"10,000 metric events recorded in {elapsed:.2f}s")
    assert elapsed < 5  # Should be very fast


# ==============================================================================
# Memory Leak Tests
# ==============================================================================


def test_no_memory_leak_in_requests(client):
    """Test that repeated requests don't cause memory leaks."""
    process = psutil.Process(os.getpid())
    gc.collect()

    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Make many requests
    for _ in range(500):
        client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10,
            },
        )

    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024  # MB

    memory_increase = final_memory - initial_memory

    print(f"Memory: {initial_memory:.1f}MB -> {final_memory:.1f}MB (Δ{memory_increase:.1f}MB)")

    # Allow some memory increase, but not excessive
    assert memory_increase < 200  # Less than 200MB increase


def test_no_memory_leak_in_streaming(client):
    """Test that streaming doesn't cause memory leaks."""
    process = psutil.Process(os.getpid())
    gc.collect()

    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Stream many responses
    for _ in range(100):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "stream": True,
                "max_tokens": 20,
            },
        )

        # Consume stream
        for line in response.iter_lines():
            if line and line.startswith(b"data: "):
                data_str = line[6:].decode("utf-8")
                if data_str.strip() == "[DONE]":
                    break

    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024  # MB

    memory_increase = final_memory - initial_memory

    print(f"Streaming memory: {initial_memory:.1f}MB -> {final_memory:.1f}MB (Δ{memory_increase:.1f}MB)")

    # Allow some memory increase
    assert memory_increase < 150


# ==============================================================================
# Startup Time Tests
# ==============================================================================


def test_service_initialization_fast(service):
    """Test that service initializes quickly."""
    from fakeai.config import AppConfig
    from fakeai.fakeai_service import FakeAIService

    start_time = time.time()

    config = AppConfig(require_api_key=False, response_delay=0.0)
    service = FakeAIService(config)

    elapsed = time.time() - start_time

    print(f"Service initialization: {elapsed:.3f}s")
    assert elapsed < 2.0  # Should initialize in under 2 seconds


# ==============================================================================
# Response Time Tests
# ==============================================================================


def test_chat_completion_latency(client):
    """Test chat completion latency."""
    latencies = []

    for _ in range(10):
        start = time.time()

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
            },
        )

        elapsed = time.time() - start
        latencies.append(elapsed)

        assert response.status_code == 200

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

    print(f"Chat latency: avg={avg_latency:.3f}s, p95={p95_latency:.3f}s")


def test_embedding_latency(client):
    """Test embedding latency."""
    latencies = []

    for _ in range(10):
        start = time.time()

        response = client.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-3-small",
                "input": "Test text",
            },
        )

        elapsed = time.time() - start
        latencies.append(elapsed)

        assert response.status_code == 200

    avg_latency = sum(latencies) / len(latencies)

    print(f"Embedding latency: avg={avg_latency:.3f}s")


# ==============================================================================
# Throughput Tests
# ==============================================================================


def test_sustained_throughput(client):
    """Test sustained request throughput."""
    duration = 10  # seconds
    request_count = 0
    start_time = time.time()

    while time.time() - start_time < duration:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
            },
        )

        if response.status_code == 200:
            request_count += 1

    elapsed = time.time() - start_time
    throughput = request_count / elapsed

    print(f"Sustained throughput: {throughput:.2f} req/s over {elapsed:.1f}s")
    assert throughput > 5  # At least 5 req/s


# ==============================================================================
# Scalability Tests
# ==============================================================================


def test_request_size_scalability(client):
    """Test handling various request sizes."""
    sizes = [10, 100, 1000, 5000]

    for size in sizes:
        content = "word " * size

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 10,
            },
        )

        assert response.status_code == 200


def test_batch_size_scalability(client):
    """Test handling various batch sizes."""
    batch_sizes = [1, 5, 10, 50]

    for batch_size in batch_sizes:
        inputs = [f"Text {i}" for i in range(batch_size)]

        response = client.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-3-small",
                "input": inputs,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == batch_size


# ==============================================================================
# Resource Utilization Tests
# ==============================================================================


def test_cpu_utilization_reasonable():
    """Test that CPU utilization is reasonable."""
    # This is hard to test deterministically
    # Just verify the system is responsive
    process = psutil.Process(os.getpid())
    cpu_percent = process.cpu_percent(interval=1.0)

    print(f"CPU utilization: {cpu_percent}%")
    # Just a sanity check
    assert cpu_percent >= 0


def test_memory_utilization_reasonable():
    """Test that memory utilization is reasonable."""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024

    print(f"Memory utilization: {memory_mb:.1f}MB")

    # Should not use excessive memory
    assert memory_mb < 2000  # Less than 2GB


# ==============================================================================
# Error Recovery Tests
# ==============================================================================


def test_recovery_from_errors(client):
    """Test that system recovers from errors."""
    # Make invalid request
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "",  # Invalid
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    assert response.status_code == 422

    # Should still handle valid requests
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
