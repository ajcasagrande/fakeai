"""
Test script to verify token timing metrics with request body stream parameter.
"""
import asyncio
import json
import time
from typing import Dict, Any

import aiohttp


async def test_chat_completion_stream():
    """Test chat completion streaming with token timing information."""
    url = "http://localhost:8000/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer fake-key"
    }
    data = {
        "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        "messages": [{"role": "user", "content": "Tell me a short story about a robot."}],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": True  # This should now be properly recognized in the request body
    }

    print("Testing chat completion stream with stream parameter in request body...")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                print(f"Response status: {response.status}")
                print(f"Headers: {response.headers}")
                
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "")
                    print(f"Content-Type: {content_type}")
                    if "text/event-stream" in content_type:
                        print("Streaming response detected! Success!")
                    else:
                        print("ERROR: Response is not a streaming response.")
                    
                    # Just read the first few chunks to confirm token timing
                    token_count = 0
                    async for line in response.content:
                        if not line.strip():
                            continue
                        
                        if line.startswith(b'data: '):
                            line = line[6:].strip()  # Remove 'data: ' prefix
                        
                        if line == b'[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(line)
                            # Check for token timing info in the first few tokens
                            if (chunk.get("choices") and 
                                chunk["choices"][0].get("delta") and
                                chunk["choices"][0]["delta"].get("token_timing")):
                                
                                token_timing = chunk["choices"][0]["delta"].get("token_timing")
                                print(f"Token timing detected: {token_timing}")
                                token_count += 1
                                
                                # Just check the first few tokens
                                if token_count >= 3:
                                    print("Success! Token timing is present in streaming response.")
                                    break
                        except json.JSONDecodeError:
                            print(f"Could not decode line: {line}")
                else:
                    print(f"Error: {response.status}")
                    print(await response.text())
        except Exception as e:
            print(f"Exception: {e}")


async def main():
    """Run all tests."""
    await test_chat_completion_stream()


if __name__ == "__main__":
    asyncio.run(main())
