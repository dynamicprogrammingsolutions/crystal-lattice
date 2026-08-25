#!/bin/bash

set -e

echo "🚀 Bridge Integration Test Runner"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo ""
    echo "On macOS:"
    echo "  1. Open Docker Desktop application"
    echo "  2. Wait for it to start (whale icon in menu bar)"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "../venv/bin/activate" ]; then
        echo "📦 Activating Python virtual environment..."
        source ../venv/bin/activate
    else
        echo "⚠️  No virtual environment found, using system Python"
    fi
fi

# Check Python dependencies
echo "🐍 Checking Python dependencies..."
if ! python3 -c "import httpx, websockets" 2>/dev/null; then
    echo "📦 Installing integration dependencies..."
    python3 -m pip install -q -r requirements.txt
fi
echo "✅ Python dependencies ready"
echo ""

# Check if cluster is already running
if docker ps | grep -q "bridge-node"; then
    echo "✅ Bridge cluster is already running"
    echo ""
else
    echo "🐳 Starting Bridge cluster..."
    echo "   This will take about 30 seconds..."
    echo ""
    
    docker-compose build --quiet
    docker-compose up -d
    
    echo "⏳ Waiting for cluster to be healthy..."
    sleep 15
    
    # Check health
    for i in {1..10}; do
        if curl -s http://localhost:4000/health > /dev/null 2>&1; then
            echo "✅ Cluster is healthy!"
            echo ""
            break
        fi
        echo "   Still waiting... ($i/10)"
        sleep 2
    done
fi

# Show cluster status
echo "📊 Cluster Status:"
echo ""
curl -s http://localhost:4000/health | python3 -m json.tool || echo "❌ Health check failed"
echo ""

# Run integration tests
echo "🧪 Running Integration Tests..."
echo "=================================="
echo ""

BRIDGE_URL=ws://localhost:4000/ws/websocket python3 test_docker.py
BRIDGE_URL=ws://localhost:4000/ws/websocket \
BRIDGE_HTTP_BASE_URL=http://localhost:4000 \
python3 test_http_cluster.py

exit_code=$?

echo ""
echo "=================================="
if [ $exit_code -eq 0 ]; then
    echo "✅ All integration tests passed!"
else
    echo "❌ Some integration tests failed"
fi
echo ""
echo "💡 Tips:"
echo "   - View logs: make docker-logs"
echo "   - Check health: make docker-health"
echo "   - Stop cluster: make docker-down"
echo ""

exit $exit_code
