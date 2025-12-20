#!/bin/bash

set -e

echo "🚀 Deploying Bridge (single-node)"
echo "==================================="
echo ""

# Ensure Docker daemon is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Please start Docker and try again."
  exit 1
fi

# Detect docker compose command
if docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
elif docker-compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker-compose"
else
  echo "❌ Neither 'docker compose' nor 'docker-compose' is available."
  exit 1
fi

echo "✅ Using: $DOCKER_COMPOSE"
echo ""

cd "$(dirname "$0")/.."

echo "🐳 Starting single-node bridge on port 4000..."
$DOCKER_COMPOSE -f docker-compose.single-node.yml up -d

echo "⏳ Waiting for bridge to become healthy..."
sleep 5

if curl -sf http://localhost:4000/health >/dev/null 2>&1; then
  echo "✅ Bridge is up and healthy on http://localhost:4000/health"
  echo ""
  echo "WebSocket endpoints (HTTP only):"
  echo "  ws://<host>:4000/ws/websocket?type=server"
  echo "  ws://<host>:4000/ws/websocket?type=app"
  echo ""
else
  echo "⚠️  Bridge container started, but health check failed."
  echo "   - Check logs with: $DOCKER_COMPOSE -f docker-compose.single-node.yml logs -f"
  echo "   - Verify that port 4000 is not in use by another process."
  exit 1
fi
