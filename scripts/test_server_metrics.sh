#!/bin/bash
# Test FakeAI server metrics endpoints

echo "Starting FakeAI server in background..."
# Start the FakeAI server
fakeai-server --port 8000 &
SERVER_PID=$!

# Make sure to kill the server when the script exits
trap "kill $SERVER_PID" EXIT

# Wait for server to fully start
echo "Waiting for server to start up..."
sleep 2

# Run the metrics test script
echo "Running metrics test..."
python3 $(dirname "$0")/test_metrics.py

# Wait for user input to continue monitoring
echo -e "\nServer is running. Press Ctrl+C to exit..."
echo "You can monitor metrics at: http://localhost:8000/metrics"
echo "You can get AIPerf formatted metrics by running:"
echo "python3 $(dirname "$0")/aiperf_metrics.py"

# Keep the script running until user presses Ctrl+C
while true; do
  sleep 1
done
