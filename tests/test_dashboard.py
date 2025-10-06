#!/usr/bin/env python3
"""
Quick test script to verify dashboard endpoints are working.

Run this to check if all required endpoints return valid data.
"""
import asyncio
import json

import aiohttp


async def check_endpoint(session, url, name):
    """Check if endpoint returns valid data."""
    try:
        print(f"Testing {name}...")
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
            if response.status == 200:
                # Try to parse as JSON
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = await response.json()
                    print(f"  ✅ {name}: OK (returned {len(json.dumps(data))} bytes)")
                    return True
                elif content_type.startswith("text/plain"):
                    # Prometheus format
                    await response.text()
                    print(f"  ✅ {name}: OK (Prometheus format)")
                    return True
                else:
                    print(f"  ⚠️  {name}: Returned non-JSON data")
                    return False
            else:
                print(f"  ❌ {name}: Failed (status {response.status})")
                return False

    except aiohttp.ClientConnectorError:
        print(f"  ❌ {name}: Connection failed (is server running?)")
        return False
    except asyncio.TimeoutError:
        print(f"  ❌ {name}: Timeout")
        return False
    except Exception as e:
        print(f"  ❌ {name}: Error - {e}")
        return False


async def main():
    """Test all dashboard endpoints."""
    base_url = "http://localhost:8000"

    print("=" * 60)
    print("FakeAI Dashboard Endpoint Test")
    print("=" * 60)
    print()

    # Test all required endpoints
    endpoints = [
        ("/metrics", "Core Metrics"),
        ("/kv-cache/metrics", "KV Cache Metrics"),
        ("/dcgm/metrics/json", "DCGM GPU Metrics (JSON)"),
        ("/dynamo/metrics/json", "Dynamo LLM Metrics (JSON)"),
        ("/health", "Health Check"),
        ("/dashboard", "Dashboard HTML"),
        ("/dashboard/dynamo", "Advanced Dashboard HTML"),
    ]

    results = []
    async with aiohttp.ClientSession() as session:
        for endpoint, name in endpoints:
            url = base_url + endpoint
            success = await check_endpoint(session, url, name)
            results.append((name, success))

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print()
    print(f"Result: {passed}/{total} endpoints working")

    if passed == total:
        print()
        print("🎉 All endpoints working! Dashboard should load correctly.")
        print()
        print("Open in browser: http://localhost:8000/dashboard/dynamo")
    else:
        print()
        print("⚠️  Some endpoints failed. Dashboard may not work correctly.")
        print()
        print("Fix:")
        print("  1. Make sure server is running: fakeai server")
        print("  2. Check for errors in server logs")
        print("  3. See DASHBOARD_QUICK_FIX.md for troubleshooting")

    return passed == total


if __name__ == "__main__":
    import sys

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
