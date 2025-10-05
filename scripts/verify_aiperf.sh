#!/bin/bash
# Run AIPerf against the FakeAI server to verify token timing metrics

echo "Starting FakeAI server in background..."
# Start the FakeAI server (assuming it's already installed and in path)
fakeai-server --port 8000 &
SERVER_PID=$!

# Make sure to kill the server when the script exits
trap "kill $SERVER_PID" EXIT

# Wait for server to fully start
echo "Waiting for server to start up..."
sleep 2

# Run AIPerf with deepseek model (assuming aiperf is installed)
echo "Running AIPerf tests..."
aiperf profile \
  --model deepseek-ai/DeepSeek-R1 \
  --url http://localhost:8000 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 100 \
  --request-count 1000 \
  --synthetic-tokens-mean 128 \
  --synthetic-tokens-stddev 0 \
  --output-tokens-mean 100 \
  --output-tokens-stddev 0 \
  --warmup-request-count 2

# Show the results
echo "Test complete! Check the results above for timing metrics."

# Get server metrics
echo -e "\nFetching server metrics..."
python3 $(dirname "$0")/aiperf_metrics.py

# Show a reminder about the metrics endpoint
echo -e "\nYou can monitor metrics in real-time by visiting: http://localhost:8000/metrics"
