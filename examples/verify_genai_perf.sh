#!/bin/bash
# Run GenAI-Perf against the FakeAI server to verify token timing metrics

echo "Starting FakeAI server in background..."
# Start the FakeAI server (assuming it's already installed and in path)
fakeai-server --port 8000 &
SERVER_PID=$!

# Make sure to kill the server when the script exits
trap "kill $SERVER_PID" EXIT

# Wait for server to fully start
echo "Waiting for server to start up..."
sleep 2

# Run GenAI-Perf with deepseek model (assuming genai-perf is installed)
echo "Running GenAI-Perf tests..."
genai-perf profile \
  -m deepseek-ai/DeepSeek-R1-Distill-Llama-8B \
  --endpoint-type chat \
  --synthetic-input-tokens-mean 128 \
  --synthetic-input-tokens-stddev 0 \
  --output-tokens-mean 100 \
  --output-tokens-stddev 0 \
  --url localhost:8000 \
  --streaming \
  --concurrency 100 \
  --request-count 1000 \
  --warmup-request-count 2 \
  -- -H "Authorization: Bearer 12345"

# Show the results
echo "Test complete! Check the results above for timing metrics."
