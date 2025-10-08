#!/usr/bin/env python3
"""
Debug script for the FakeAI server streaming functionality.

This script attempts to diagnose issues with the streaming functionality
in the FakeAI server.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import time

from openai import AsyncOpenAI


async def debug_streaming() -> None:
    """Debug the streaming functionality."""
    print("FakeAI Streaming Debug Tool")
    print("==========================")

    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )

    print("\nAttempting direct API request...")

    # Try with various parameters to debug
    try:
        start_time = time.time()
        print("Sending request with max_tokens=100...")

        stream = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Say hello"}],
            stream=True,
            max_tokens=100,  # Explicitly set max_tokens
        )

        print("Request sent, waiting for response chunks...")

        # Debug each chunk
        chunk_count = 0
        content_chunks = 0

        async for chunk in stream:
            chunk_count += 1
            print(f"\nChunk {chunk_count}:")
            print(f"  ID: {chunk.id}")
            print(f"  Created: {chunk.created}")
            print(f"  Model: {chunk.model}")

            # Print detailed info about choices
            for i, choice in enumerate(chunk.choices):
                print(f"  Choice {i}:")
                print(f"    Index: {choice.index}")
                print(f"    Finish Reason: {choice.finish_reason}")

                if hasattr(choice, "delta"):
                    print(f"    Delta: {choice.delta}")

                    # Check if delta has content
                    if hasattr(choice.delta, "content") and choice.delta.content:
                        content_chunks += 1
                        print(f"    Content: '{choice.delta.content}'")
                    elif hasattr(choice.delta, "role"):
                        print(f"    Role: {choice.delta.role}")
                    else:
                        print("    No content in delta")
                else:
                    print("    No delta attribute")

        elapsed = time.time() - start_time
        print("\nStreaming request completed.")
        print(f"Total chunks received: {chunk_count}")
        print(f"Content-bearing chunks: {content_chunks}")
        print(f"Time elapsed: {elapsed:.2f}s")

        # Specific check for streaming issues
        if chunk_count > 0 and content_chunks == 0:
            print("\nISSUE DETECTED: Received chunks but no content.")
            print(
                "This suggests the server is sending empty chunks or not generating content."
            )
        elif chunk_count == 0:
            print("\nISSUE DETECTED: No chunks received.")
            print(
                "This suggests a server connection issue or streaming not working properly."
            )

    except Exception as e:
        print(f"\nError during streaming: {str(e)}")
        print(f"Error type: {type(e).__name__}")

        # Try to get more details from the error
        if hasattr(e, "response") and hasattr(e.response, "text"):
            try:
                error_data = json.loads(e.response.text)
                print(f"API error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error response: {e.response.text}")

    # Also test a non-streaming request to compare
    try:
        print("\n\nTesting non-streaming request for comparison...")
        start_time = time.time()

        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Say hello"}],
            stream=False,
            max_tokens=100,
        )

        elapsed = time.time() - start_time
        print(f"Non-streaming request completed in {elapsed:.2f}s")

        if hasattr(response, "choices") and response.choices:
            print(f"Content: '{response.choices[0].message.content}'")
            print("Non-streaming is working correctly.")
        else:
            print("Non-streaming response has no content.")

    except Exception as e:
        print(f"Error in non-streaming request: {str(e)}")

    print("\n" + "=" * 50)
    print("Diagnostic information:")
    print(
        "If both streaming and non-streaming requests have issues, the FakeAI server may not be running correctly."
    )
    print(
        "If only streaming has issues, there might be a problem with the streaming implementation in FakeAI."
    )
    print("=" * 50)


async def main() -> None:
    """Run the debug script."""
    try:
        await debug_streaming()
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("\nMake sure the FakeAI server is running at http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(main())
