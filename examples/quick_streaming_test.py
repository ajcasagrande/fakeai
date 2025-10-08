#!/usr/bin/env python3
"""
Quick Streaming Test

A simplified version for quick testing of streaming functionality.
"""

import json
import sys
import time

import requests

BASE_URL = "http://localhost:8000"
API_KEY = "test-key"


def quick_test():
    """Run a quick streaming test."""
    print("Quick Streaming Test")
    print("=" * 60)

    # Test chat completions
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "user", "content": "Count to 5"}
        ],
        "stream": True,
        "max_tokens": 20
    }

    try:
        print(f"Sending request to {url}...")
        start = time.time()
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False

        print("✓ Connected, receiving stream...\n")

        tokens = []
        first_token_time = None

        for line in response.iter_lines():
            if not line:
                continue

            line_str = line.decode('utf-8').strip()
            if not line_str.startswith("data: "):
                continue

            data_str = line_str[6:]
            if data_str == "[DONE]":
                break

            try:
                data = json.loads(data_str)
                if "choices" in data and len(data["choices"]) > 0:
                    delta = data["choices"][0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        token = delta["content"]
                        tokens.append(token)

                        if first_token_time is None:
                            first_token_time = time.time()
                            ttft = (first_token_time - start) * 1000
                            print(f"First token: '{token}' (TTFT: {ttft:.2f}ms)")
                        else:
                            print(f"Token: '{token}'")
            except json.JSONDecodeError:
                pass

        end = time.time()
        duration = (end - start) * 1000

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"✓ Success: True")
        print(f"✓ Tokens received: {len(tokens)}")
        print(f"✓ TTFT: {((first_token_time - start) * 1000):.2f}ms" if first_token_time else "✗ TTFT: N/A")
        print(f"✓ Duration: {duration:.2f}ms")
        print(f"✓ Generated: {''.join(tokens)}")
        print(f"{'='*60}")

        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Is the server running at {BASE_URL}?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
