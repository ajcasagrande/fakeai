#!/bin/bash
# Run comprehensive streaming tests
#
# Usage:
#   ./examples/run_streaming_tests.sh
#
# Prerequisites:
#   - FakeAI server must be running on http://localhost:8000
#   - Python packages: requests

set -e

echo "========================================"
echo "FakeAI Streaming Tests"
echo "========================================"
echo ""

# Check if server is running
echo "Checking if FakeAI server is running..."
if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Error: FakeAI server is not running on http://localhost:8000"
    echo ""
    echo "Please start the server first:"
    echo "  python -m fakeai.app"
    echo ""
    exit 1
fi
echo "✓ Server is running"
echo ""

# Run the tests
echo "Running comprehensive streaming tests..."
echo ""
python tests/test_streaming_complete.py

echo ""
echo "========================================"
echo "Tests completed!"
echo "========================================"
