#!/bin/bash

set -e

echo "🚀 Testing Bridge Docker Deployment"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

# Check if cluster is running
if ! docker ps | grep -q "bridge-node-1"; then
    echo "⚠️  Bridge cluster is not running"
    echo "Starting cluster..."
    make docker-up
    sleep 10
fi

echo "✅ Bridge cluster is running"
echo ""

# Check Python dependencies
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

echo "🧪 Running integration tests..."
echo ""

BRIDGE_URL=ws://localhost:4000/ws/websocket python3 test_docker.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed"
fi

exit $exit_code
