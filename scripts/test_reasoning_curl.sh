#!/bin/bash
# Test reasoning content support with GPT-OSS models using curl

echo "=========================================="
echo "Testing GPT-OSS Models with Reasoning"
echo "=========================================="
echo ""
echo "GPT-OSS: OpenAI's open-source reasoning models"
echo "Released: August 2025 | License: Apache 2.0"
echo ""

# Start server in background (if not already running)
# Uncomment these lines to auto-start the server:
# python run_server.py &
# SERVER_PID=$!
# sleep 2

echo "1. Non-streaming request with gpt-oss-120b:"
echo ""

curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-120b",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }' | python -m json.tool | head -40

echo ""
echo "Note the 'reasoning_content' field in the message!"
echo ""
echo "=========================================="
echo ""

echo "2. Streaming request with gpt-oss-20b (low latency):"
echo ""

curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-20b",
    "messages": [{"role": "user", "content": "Explain AI"}],
    "stream": true
  }' | head -30

echo ""
echo "Note: Reasoning chunks come first (reasoning_content),"
echo "      followed by regular content chunks."
echo ""

# Clean up server if we started it
# if [ ! -z "$SERVER_PID" ]; then
#   kill $SERVER_PID
# fi
