#!/usr/bin/env python3
"""
Waterfall Chart Demonstration.

Shows how to use the FakeAI waterfall visualization system to
analyze request timing patterns.
"""

import asyncio
import time

from openai import OpenAI


async def main():
    """Run waterfall chart demo."""
    print("🎨 FakeAI Waterfall Chart Demo\n")
    print("=" * 60)

    # Create client pointing to FakeAI server
    # (Make sure server is running: fakeai server)
    client = OpenAI(
        api_key="demo-key",  # Any key works with default config
        base_url="http://localhost:8000",
    )

    print("\n📊 Generating sample requests for waterfall...\n")

    # Generate multiple requests with different patterns
    requests = [
        {"model": "gpt-4", "messages": [{"role": "user", "content": "Count to 5"}]},
        {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello!"}]},
        {"model": "gpt-4-turbo", "messages": [{"role": "user", "content": "Write a haiku"}]},
    ]

    # Send streaming requests
    for i, req in enumerate(requests):
        print(f"  {i+1}. Sending {req['model']} request...")
        try:
            stream = client.chat.completions.create(**req, stream=True)
            for chunk in stream:
                pass  # Consume stream
        except Exception as e:
            print(f"     Error: {e}")

        # Small delay between requests
        time.sleep(0.2)

    print("\n✅ Requests complete!\n")
    print("=" * 60)
    print("\n🎨 Waterfall Charts Available:\n")
    print("  📊 JSON Data:  http://localhost:8000/waterfall/data")
    print("  🎭 HTML Chart: http://localhost:8000/waterfall")
    print("\n" + "=" * 60)
    print("\n💡 Open the HTML chart in your browser to see:")
    print("   - Request timeline visualization")
    print("   - TTFT markers for each request")
    print("   - Token generation progress")
    print("   - Concurrent request overlap")
    print("\n🚀 Try it now: http://localhost:8000/waterfall\n")


if __name__ == "__main__":
    asyncio.run(main())
