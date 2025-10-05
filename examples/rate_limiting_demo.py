#!/usr/bin/env python3
"""
Demo script showing rate limiting functionality in FakeAI.

This script demonstrates:
1. Configuring rate limiting tiers
2. Making requests within limits
3. Triggering rate limit errors
4. Inspecting rate limit headers
"""

import os
import time

from openai import OpenAI, RateLimitError


def demo_rate_limiting():
    """Demonstrate rate limiting with different tiers."""

    print("=" * 70)
    print("FakeAI Rate Limiting Demo")
    print("=" * 70)
    print()

    # Configure to use local FakeAI server
    # Note: Make sure to start the server with:
    # FAKEAI_RATE_LIMIT_ENABLED=true FAKEAI_REQUIRE_API_KEY=true \
    # FAKEAI_API_KEYS=test-key FAKEAI_RATE_LIMIT_TIER=free \
    # python run_server.py

    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1",
    )

    print("1. Testing rate limits with 'free' tier (60 RPM, 10K TPM)")
    print("-" * 70)

    # Make some requests to see headers
    for i in range(3):
        try:
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.1-8B-Instruct",
                messages=[{"role": "user", "content": f"Hello {i+1}"}],
            )

            print(f"\nRequest {i+1} successful:")
            print(f"  Response: {response.choices[0].message.content[:50]}...")

            # Note: Headers are available on the underlying httpx response
            # In a real implementation, you'd access them via the raw response

        except RateLimitError as e:
            print(f"\nRequest {i+1} RATE LIMITED!")
            print(f"  Error: {e}")
            break

    print("\n" + "=" * 70)
    print("2. Simulating rate limit exhaustion")
    print("-" * 70)

    # If using free tier with only 2 RPM override, this would trigger rate limit
    print("\nTo test rate limit exhaustion:")
    print("1. Start server with FAKEAI_RATE_LIMIT_RPM=2")
    print("2. Make 3+ requests quickly")
    print("3. Observe 429 error with Retry-After header")

    print("\n" + "=" * 70)
    print("3. Rate limit headers (available in HTTP response)")
    print("-" * 70)

    print("\nHeaders included in every response:")
    print("  x-ratelimit-limit-requests:     Maximum requests per minute")
    print("  x-ratelimit-limit-tokens:       Maximum tokens per minute")
    print("  x-ratelimit-remaining-requests: Requests remaining in window")
    print("  x-ratelimit-remaining-tokens:   Tokens remaining in window")
    print("  x-ratelimit-reset-requests:     Unix timestamp for request reset")
    print("  x-ratelimit-reset-tokens:       Unix timestamp for token reset")

    print("\n" + "=" * 70)
    print("4. Different rate limit tiers")
    print("-" * 70)

    tiers = {
        "free": "60 RPM, 10K TPM",
        "tier-1": "500 RPM, 30K TPM",
        "tier-2": "5,000 RPM, 450K TPM",
        "tier-3": "10,000 RPM, 1M TPM",
        "tier-4": "30,000 RPM, 5M TPM",
        "tier-5": "100,000 RPM, 15M TPM",
    }

    print("\nAvailable tiers (configure with FAKEAI_RATE_LIMIT_TIER):")
    for tier, limits in tiers.items():
        print(f"  {tier:10s}: {limits}")

    print("\n" + "=" * 70)
    print("5. Custom rate limits")
    print("-" * 70)

    print("\nOverride tier limits with environment variables:")
    print("  FAKEAI_RATE_LIMIT_RPM=1000    # Custom requests per minute")
    print("  FAKEAI_RATE_LIMIT_TPM=50000   # Custom tokens per minute")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


def demo_rate_limit_error():
    """Demonstrate how to handle rate limit errors."""

    print("\n" + "=" * 70)
    print("Rate Limit Error Handling Example")
    print("=" * 70)

    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1",
    )

    print("\nMaking requests with automatic retry on rate limit...")

    for i in range(5):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="meta-llama/Llama-3.1-8B-Instruct",
                    messages=[{"role": "user", "content": f"Request {i+1}"}],
                )

                print(f"Request {i+1}: Success")
                break

            except RateLimitError as e:
                if attempt < max_retries - 1:
                    # Extract retry_after from error if available
                    retry_after = 1  # Default to 1 second
                    print(f"Request {i+1}: Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                else:
                    print(f"Request {i+1}: Failed after {max_retries} attempts")
                    raise


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SETUP INSTRUCTIONS")
    print("=" * 70)
    print("\nTo run this demo, start the FakeAI server with rate limiting enabled:")
    print()
    print("  export FAKEAI_RATE_LIMIT_ENABLED=true")
    print("  export FAKEAI_REQUIRE_API_KEY=true")
    print("  export FAKEAI_API_KEYS=test-key")
    print("  export FAKEAI_RATE_LIMIT_TIER=free")
    print("  python run_server.py")
    print()
    print("Then run this script in another terminal:")
    print("  python examples/rate_limiting_demo.py")
    print()
    input("Press Enter to continue with the demo (make sure server is running)...")
    print()

    try:
        demo_rate_limiting()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure the FakeAI server is running with rate limiting enabled!")
        print("See setup instructions above.")
