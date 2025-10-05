#!/usr/bin/env python3
"""
Example demonstrating usage tracking and billing API.

This script shows how to:
1. Make various API calls (chat, embeddings, images)
2. Query usage data aggregated by time buckets
3. Query cost data with billing breakdowns
"""

import asyncio
import time
from openai import OpenAI


async def main():
    """Run usage tracking demonstration."""
    # Initialize OpenAI client pointing to FakeAI
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1",
    )

    print("=" * 70)
    print("Usage Tracking and Billing API Demo")
    print("=" * 70)
    print()

    # Record start time for querying
    start_time = int(time.time())

    # 1. Make some chat completion requests
    print("1. Creating chat completions...")
    for i in range(3):
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": f"This is test message {i+1}"}
            ],
            # Include metadata for tracking
            extra_body={
                "metadata": {"project_id": "proj-demo"},
                "user": "user-demo",
            },
        )
        print(f"   - Chat completion {i+1}: {response.usage.total_tokens} tokens")

    print()

    # 2. Make embedding requests
    print("2. Creating embeddings...")
    for i in range(2):
        response = client.embeddings.create(
            model="sentence-transformers/all-mpnet-base-v2",
            input=f"Sample text for embedding {i+1}",
        )
        print(f"   - Embedding {i+1}: {response.usage.total_tokens} tokens")

    print()

    # 3. Make image generation request
    print("3. Generating images...")
    response = client.images.generate(
        model="stabilityai/stable-diffusion-2-1",
        prompt="A beautiful sunset",
        n=2,
    )
    print(f"   - Generated {len(response.data)} images")

    print()

    # Wait a moment to ensure all tracking is complete
    await asyncio.sleep(1)

    # Record end time
    end_time = int(time.time()) + 10

    print("=" * 70)
    print("Querying Usage Data")
    print("=" * 70)
    print()

    # 4. Query completions usage
    print("4. Completions Usage:")
    response = client.get(
        f"http://localhost:8000/v1/organization/usage/completions?start_time={start_time}&end_time={end_time}&bucket_width=1h"
    )
    if response.status_code == 200:
        usage_data = response.json()
        for bucket in usage_data.get("data", []):
            for result in bucket.get("results", []):
                print(f"   - Input tokens: {result['input_tokens']}")
                print(f"   - Output tokens: {result['output_tokens']}")
                print(f"   - Requests: {result['num_model_requests']}")
    print()

    # 5. Query embeddings usage
    print("5. Embeddings Usage:")
    response = client.get(
        f"http://localhost:8000/v1/organization/usage/embeddings?start_time={start_time}&end_time={end_time}&bucket_width=1h"
    )
    if response.status_code == 200:
        usage_data = response.json()
        for bucket in usage_data.get("data", []):
            for result in bucket.get("results", []):
                print(f"   - Input tokens: {result['input_tokens']}")
                print(f"   - Requests: {result['num_model_requests']}")
    print()

    # 6. Query costs
    print("6. Cost Breakdown:")
    response = client.get(
        f"http://localhost:8000/v1/organization/costs?start_time={start_time}&end_time={end_time}&bucket_width=1h"
    )
    if response.status_code == 200:
        cost_data = response.json()
        total_cost = 0.0
        for bucket in cost_data.get("data", []):
            print(f"   Time bucket: {bucket['start_time']} - {bucket['end_time']}")
            for result in bucket.get("results", []):
                line_item = result["line_item"]
                cost = result["amount"]["value"]
                total_cost += cost
                print(f"     - {line_item}: ${cost:.6f}")
        print(f"   Total estimated cost: ${total_cost:.6f}")
    print()

    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    print("\nMake sure the FakeAI server is running on http://localhost:8000\n")
    print("Start it with: python run_server.py\n")
    input("Press Enter to continue...")

    asyncio.run(main())
