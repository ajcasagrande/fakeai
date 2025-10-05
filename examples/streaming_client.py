#!/usr/bin/env python3
"""
Streaming client example for the FakeAI server.

This script demonstrates how to use streaming completions with the FakeAI server,
handling the streamed responses in different ways and providing examples for 
real-time processing of token-by-token responses.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletionChunk


async def simple_streaming_chat() -> None:
    """Simple example of streaming chat completions."""
    print("\n--- Simple Streaming Chat Example ---")
    
    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )

    print("Prompt: Write a short story about AI")
    print("Response: ", end="", flush=True)
    
    start_time = time.time()
    stream = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Write a short story about AI"}],
        stream=True,
        max_tokens=150,  # Ensure we specify max_tokens to get a decent response
    )
    
    # Simple streaming: just print each token as it arrives
    content_received = False
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content_received = True
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    if not content_received:
        print("[No content received in stream. The FakeAI server may need to be restarted.]")
    
    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.2f}s")


async def collect_full_response() -> None:
    """Example of collecting the full streamed response."""
    print("\n--- Collecting Full Streamed Response ---")
    
    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )

    print("Prompt: Explain quantum computing in simple terms")
    print("Streaming response...")
    
    start_time = time.time()
    stream = await client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[{"role": "user", "content": "Explain quantum computing in simple terms"}],
        stream=True,
    )
    
    # Collect the full response
    collected_content = ""
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            collected_content += content
            # Print progress indicator
            print(".", end="", flush=True)
    
    elapsed = time.time() - start_time
    print(f"\nStreaming completed in {elapsed:.2f}s")
    print("\nFull collected response:")
    print(f"{collected_content}")


async def interactive_streaming() -> None:
    """Example of interactive streaming with real-time token processing."""
    print("\n--- Interactive Streaming Example ---")
    
    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )

    # This demonstrates how you might implement a more interactive experience
    print("Prompt: List 5 programming best practices")
    print("Response (with token timing):")
    
    start_time = time.time()
    last_token_time = start_time
    tokens_count = 0
    
    stream = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "List 5 programming best practices"}],
        stream=True,
    )
    
    # Process each token with timing information
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            now = time.time()
            token_time = now - last_token_time
            tokens_count += 1
            
            # Print token with timing data
            print(f"{content}", end="", flush=True)
            
            # For demonstration, we could do real-time processing here
            # For example, we could analyze tokens, trigger actions, etc.
            
            last_token_time = now
    
    total_time = time.time() - start_time
    print(f"\n\nReceived {tokens_count} tokens in {total_time:.2f}s")
    print(f"Average token rate: {tokens_count / total_time:.2f} tokens/second")


async def multi_message_conversation() -> None:
    """Example of a multi-message conversation with streaming responses."""
    print("\n--- Multi-message Conversation Example ---")
    
    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )
    
    # This simulates a back-and-forth conversation
    conversation = [
        {"role": "system", "content": "You are a technical assistant helping with coding."},
        {"role": "user", "content": "How do I create a simple HTTP server in Python?"}
    ]
    
    print("User: How do I create a simple HTTP server in Python?")
    print("Assistant: ", end="", flush=True)
    
    # First response
    response_content = await stream_and_collect(client, conversation)
    
    # Add the assistant's response to the conversation
    conversation.append({"role": "assistant", "content": response_content})
    
    # Add the user's follow-up question
    conversation.append({"role": "user", "content": "How do I add custom headers to the responses?"})
    
    print("\n\nUser: How do I add custom headers to the responses?")
    print("Assistant: ", end="", flush=True)
    
    # Get the follow-up response
    await stream_and_collect(client, conversation)


async def stream_and_collect(client: AsyncOpenAI, messages: List[Dict[str, str]]) -> str:
    """Helper function to stream a response and collect it.
    
    Args:
        client: The OpenAI async client
        messages: The conversation messages
        
    Returns:
        The full response text
    """
    stream = await client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=messages,
        stream=True,
    )
    
    collected_content = ""
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            collected_content += content
            print(content, end="", flush=True)
    
    return collected_content


async def process_multiple_completions() -> None:
    """Example of processing multiple streaming completions concurrently."""
    print("\n--- Multiple Concurrent Completions Example ---")
    
    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )
    
    # Define a function to handle a single streaming request
    async def process_stream(prompt: str, index: int) -> str:
        print(f"Starting stream {index}: {prompt}")
        result = ""
        
        stream = await client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=50,  # Keep responses shorter for this example
        )
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                result += content
        
        print(f"Completed stream {index}")
        return result
    
    # Process multiple streams concurrently
    prompts = [
        "Write a haiku about programming",
        "Give me a short Python tip",
        "Write a brief JSON example"
    ]
    
    tasks = [process_stream(prompt, i) for i, prompt in enumerate(prompts)]
    results = await asyncio.gather(*tasks)
    
    # Show the results
    for i, result in enumerate(results):
        print(f"\nResult {i}: {prompts[i]}")
        print(f"{result}")


async def advanced_stream_processing() -> None:
    """Advanced example showing how to process stream events in detail."""
    print("\n--- Advanced Stream Processing Example ---")
    
    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )
    
    # Custom stream handler that processes each chunk in detail
    class StreamHandler:
        def __init__(self):
            self.start_time = time.time()
            self.tokens = []
            self.finish_reason = None
            self.content = ""
            
        async def handle_stream(self, stream: AsyncIterator[ChatCompletionChunk]) -> None:
            """Process a stream of chat completion chunks."""
            print("Beginning stream processing...")
            
            try:
                async for chunk in stream:
                    # Process chunk metadata
                    if hasattr(chunk, 'id'):
                        print(f"Chunk ID: {chunk.id}")
                    
                    # Process choices
                    for choice in chunk.choices:
                        # Check if this choice has a finish reason
                        if choice.finish_reason:
                            self.finish_reason = choice.finish_reason
                            print(f"\nFinish reason: {choice.finish_reason}")
                        
                        # Process delta content
                        if choice.delta.content:
                            self.tokens.append({
                                'content': choice.delta.content,
                                'time': time.time() - self.start_time
                            })
                            self.content += choice.delta.content
                            print(choice.delta.content, end="", flush=True)
            except Exception as e:
                print(f"Error during stream processing: {e}")
            
            # Print summary
            elapsed = time.time() - self.start_time
            print(f"\n\nStream completed in {elapsed:.2f}s")
            print(f"Received {len(self.tokens)} tokens")
            print(f"Average token rate: {len(self.tokens) / elapsed:.2f} tokens/second")
    
    # Use the handler with a streaming request
    handler = StreamHandler()
    stream = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Explain how streaming works in APIs"}],
        stream=True,
    )
    
    await handler.handle_stream(stream)


async def main() -> None:
    """Run the streaming examples."""
    print("FakeAI Server - Streaming Client Examples")
    print("=========================================")
    
    try:
        # Run all examples
        await simple_streaming_chat()
        await collect_full_response()
        await interactive_streaming()
        await multi_message_conversation()
        await process_multiple_completions()
        await advanced_stream_processing()
        
        print("\nAll streaming examples completed successfully!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nMake sure the FakeAI server is running at http://localhost:8000")
        print("You can start it with: fakeai-server")


if __name__ == "__main__":
    asyncio.run(main())
