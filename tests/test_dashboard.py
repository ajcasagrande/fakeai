#!/usr/bin/env python3
"""
Quick test script to verify dashboard endpoints are working.

Run this to check if all required endpoints return valid data.
"""
import requests
import json


def test_endpoint(url, name):
    """Test if endpoint returns valid data."""
    try:
        print(f"Testing {name}...")
        response = requests.get(url, timeout=2)

        if response.status_code == 200:
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"  ✅ {name}: OK (returned {len(json.dumps(data))} bytes)")
                return True
            except json.JSONDecodeError:
                # Not JSON, check if it's text (Prometheus format)
                if response.headers.get('content-type', '').startswith('text/plain'):
                    print(f"  ✅ {name}: OK (Prometheus format)")
                    return True
                else:
                    print(f"  ⚠️  {name}: Returned non-JSON data")
                    return False
        else:
            print(f"  ❌ {name}: Failed (status {response.status_code})")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  ❌ {name}: Connection failed (is server running?)")
        return False
    except requests.exceptions.Timeout:
        print(f"  ❌ {name}: Timeout")
        return False
    except Exception as e:
        print(f"  ❌ {name}: Error - {e}")
        return False


def main():
    """Test all dashboard endpoints."""
    base_url = "http://localhost:8000"

    print("=" * 60)
    print("FakeAI Dashboard Endpoint Test")
    print("=" * 60)
    print()

    # Test all required endpoints
    endpoints = [
        ("/metrics", "Core Metrics"),
        ("/kv-cache-metrics", "KV Cache Metrics"),
        ("/dcgm-metrics/json", "DCGM GPU Metrics (JSON)"),
        ("/dynamo-metrics/json", "Dynamo LLM Metrics (JSON)"),
        ("/health", "Health Check"),
        ("/dashboard", "Dashboard HTML"),
        ("/dashboard/dynamo", "Advanced Dashboard HTML"),
    ]

    results = []
    for endpoint, name in endpoints:
        url = base_url + endpoint
        success = test_endpoint(url, name)
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
        print("  1. Make sure server is running: python run_server.py")
        print("  2. Check for errors in server logs")
        print("  3. See DASHBOARD_QUICK_FIX.md for troubleshooting")

    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
