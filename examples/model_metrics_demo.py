#!/usr/bin/env python3
"""
Per-Model Metrics Demo

Demonstrates the new per-model metrics tracking functionality including:
- Tracking requests by model
- Cost estimation
- Model comparison
- Prometheus export

Usage:
    python examples/model_metrics_demo.py
"""

import json
import time

import requests

BASE_URL = "http://localhost:8000"
API_KEY = "test-key"

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def make_chat_request(model: str, prompt: str):
    """Make a chat completion request."""
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
        },
    )
    return response.json()


def make_embedding_request(model: str, text: str):
    """Make an embedding request."""
    response = requests.post(
        f"{BASE_URL}/v1/embeddings",
        headers=headers,
        json={"model": model, "input": text},
    )
    return response.json()


def get_model_metrics(model: str):
    """Get metrics for a specific model."""
    response = requests.get(f"{BASE_URL}/metrics/by-model/{model}")
    return response.json()


def get_all_model_metrics():
    """Get metrics for all models."""
    response = requests.get(f"{BASE_URL}/metrics/by-model")
    return response.json()


def compare_models(model1: str, model2: str):
    """Compare two models."""
    response = requests.get(
        f"{BASE_URL}/metrics/compare", params={"model1": model1, "model2": model2}
    )
    return response.json()


def get_model_ranking(metric: str = "request_count"):
    """Get model ranking by metric."""
    response = requests.get(
        f"{BASE_URL}/metrics/ranking", params={"metric": metric, "limit": 10}
    )
    return response.json()


def get_costs():
    """Get cost breakdown by model."""
    response = requests.get(f"{BASE_URL}/metrics/costs")
    return response.json()


def get_prometheus_metrics():
    """Get Prometheus metrics."""
    response = requests.get(f"{BASE_URL}/metrics/by-model/prometheus")
    return response.text


def main():
    print("=" * 80)
    print("Per-Model Metrics Demo")
    print("=" * 80)
    print()

    # 1. Make requests to different models
    print("1. Making requests to different models...")
    print("-" * 80)

    models = ["gpt-4", "gpt-3.5-turbo", "openai/gpt-oss-120b"]
    for model in models:
        print(f"   Requesting {model}...")
        for i in range(3):
            make_chat_request(model, f"Hello! This is test {i+1}")
            time.sleep(0.1)

    print("   Done!")
    print()

    # 2. Make embedding requests
    print("2. Making embedding requests...")
    print("-" * 80)
    for i in range(2):
        make_embedding_request("text-embedding-ada-002", "Test embedding text")
        time.sleep(0.1)
    print("   Done!")
    print()

    # 3. Get metrics for a specific model
    print("3. Metrics for gpt-4:")
    print("-" * 80)
    gpt4_metrics = get_model_metrics("gpt-4")
    print(f"   Request count: {gpt4_metrics['request_count']}")
    print(f"   Total tokens: {gpt4_metrics['tokens']['total']}")
    print(f"   Average latency: {gpt4_metrics['latency']['avg_ms']:.2f}ms")
    print(f"   Total cost: ${gpt4_metrics['cost']['total_usd']:.6f}")
    print(f"   Cost per request: ${gpt4_metrics['cost']['per_request_usd']:.6f}")
    print()

    # 4. Get all model metrics
    print("4. Metrics for all models:")
    print("-" * 80)
    all_metrics = get_all_model_metrics()
    for model_id, metrics in all_metrics.items():
        print(f"   {model_id}:")
        print(f"      Requests: {metrics['request_count']}")
        print(f"      Tokens: {metrics['tokens']['total']}")
        print(f"      Cost: ${metrics['cost']['total_usd']:.6f}")
    print()

    # 5. Compare two models
    print("5. Compare gpt-4 vs gpt-3.5-turbo:")
    print("-" * 80)
    comparison = compare_models("gpt-4", "gpt-3.5-turbo")
    print(f"   Request count:")
    print(f"      gpt-4: {comparison['comparison']['request_count']['model1']}")
    print(f"      gpt-3.5-turbo: {comparison['comparison']['request_count']['model2']}")
    print(f"      Delta: {comparison['comparison']['request_count']['delta']:.0f}")
    print()
    print(f"   Average latency:")
    print(f"      gpt-4: {comparison['comparison']['avg_latency_ms']['model1']:.2f}ms")
    print(
        f"      gpt-3.5-turbo: {comparison['comparison']['avg_latency_ms']['model2']:.2f}ms"
    )
    print(f"      Winner: {comparison['winner']['latency']}")
    print()
    print(f"   Total cost:")
    print(f"      gpt-4: ${comparison['comparison']['total_cost_usd']['model1']:.6f}")
    print(
        f"      gpt-3.5-turbo: ${comparison['comparison']['total_cost_usd']['model2']:.6f}"
    )
    print(f"      Winner: {comparison['winner']['cost_efficiency']}")
    print()

    # 6. Get model ranking
    print("6. Model ranking by request count:")
    print("-" * 80)
    ranking = get_model_ranking("request_count")
    for i, model_stats in enumerate(ranking[:5], 1):
        print(
            f"   {i}. {model_stats['model']}: {model_stats['request_count']} requests"
        )
    print()

    # 7. Get cost breakdown
    print("7. Cost breakdown by model:")
    print("-" * 80)
    costs = get_costs()
    print(f"   Total cost: ${costs['total_cost_usd']:.6f}")
    print("   By model:")
    for model_id, cost in sorted(
        costs["costs_by_model"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"      {model_id}: ${cost:.6f}")
    print()

    # 8. Show Prometheus metrics sample
    print("8. Prometheus metrics (sample):")
    print("-" * 80)
    prometheus = get_prometheus_metrics()
    lines = prometheus.split("\n")
    for line in lines[:20]:  # Show first 20 lines
        if line and not line.startswith("#"):
            print(f"   {line}")
    print("   ...")
    print()

    print("=" * 80)
    print("Demo complete!")
    print("=" * 80)
    print()
    print("Available endpoints:")
    print("  - GET /metrics/by-model           - All model metrics")
    print("  - GET /metrics/by-model/{model}   - Specific model metrics")
    print("  - GET /metrics/compare?model1=X&model2=Y - Compare models")
    print("  - GET /metrics/ranking?metric=X   - Model ranking")
    print("  - GET /metrics/costs              - Cost breakdown")
    print("  - GET /metrics/by-model/prometheus - Prometheus format")
    print("  - GET /metrics/multi-dimensional  - 2D metrics")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to FakeAI server at http://localhost:8000")
        print("Please start the server first: python -m fakeai server")
    except Exception as e:
        print(f"Error: {e}")
