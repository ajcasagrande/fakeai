#!/bin/bash
# FakeAI Server Startup Script
# Starts the FakeAI server on port 8765 with proper configuration

# Set the port configuration
export FAKEAI_SERVER__PORT=8765

# Start the server
echo "Starting FakeAI server on port 8765..."
uvicorn fakeai.app:app --host 0.0.0.0 --port 8765

# Note: To run in background, use:
# nohup ./start_fakeai.sh > /tmp/fakeai.log 2>&1 &
