#!/usr/bin/env python3
"""
Test script for FakeAI server metrics endpoints.

This script makes requests to the metrics endpoint and prints the output.
"""

import asyncio
import json
import time

import aiohttp


async def get_metrics(url="http://localhost:8000"):
    """Get metrics from the FakeAI server."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/metrics") as response:
            return await response.json()


def print_metrics(metrics):
    """Print metrics in a readable format."""
    print("FakeAI Server Metrics:")
    print("======================")

    for metric_type, endpoints in metrics.items():
        print(f"\n{metric_type.upper()}:")
        for endpoint, stats in endpoints.items():
            print(f"  {endpoint}:")
            for stat_name, stat_value in stats.items():
                if isinstance(stat_value, float):
                    print(f"    {stat_name}: {stat_value:.2f}")
                else:
                    print(f"    {stat_name}: {stat_value}")


async def test_metrics():
    """Generate traffic and check metrics."""
    base_url = "http://localhost:8000"

    # Make several requests to generate metrics
    print("Making requests to generate metrics...")

    async with aiohttp.ClientSession() as session:
        # Make a request to the chat completions endpoint (non-streaming)
        print("Testing chat completions endpoint...")
        data = {
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
            "max_tokens": 50,
            "temperature": 0.7,
            "stream": False,
        }
        async with session.post(
            f"{base_url}/v1/chat/completions",
            headers={"Authorization": "Bearer test_key"},
            json=data,
        ) as response:
            print(f"Chat completions response status: {response.status}")

        # Make a request to the chat completions endpoint (streaming)
        print("Testing chat completions streaming endpoint...")
        data["stream"] = True
        async with session.post(
            f"{base_url}/v1/chat/completions",
            headers={"Authorization": "Bearer test_key"},
            json=data,
        ) as response:
            print(f"Chat completions streaming response status: {response.status}")
            # Consume the stream
            async for line in response.content:
                if line and line.strip():
                    pass

        # Make a request to the completions endpoint
        print("Testing completions endpoint...")
        data = {
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "prompt": "Write a short poem about AI",
            "max_tokens": 50,
            "temperature": 0.7,
            "stream": False,
        }
        async with session.post(
            f"{base_url}/v1/completions",
            headers={"Authorization": "Bearer test_key"},
            json=data,
        ) as response:
            print(f"Completions response status: {response.status}")

        # Make a request to the embeddings endpoint
        print("Testing embeddings endpoint...")
        data = {
            "model": "sentence-transformers/all-mpnet-base-v2",
            "input": "The quick brown fox jumps over the lazy dog",
        }
        async with session.post(
            f"{base_url}/v1/embeddings",
            headers={"Authorization": "Bearer test_key"},
            json=data,
        ) as response:
            print(f"Embeddings response status: {response.status}")

    # Wait a moment for metrics to be updated
    print("Waiting for metrics to be updated...")
    await asyncio.sleep(2)

    # Get and print metrics
    metrics = await get_metrics()
    print_metrics(metrics)


if __name__ == "__main__":
    asyncio.run(test_metrics())
