#!/bin/bash

set -e

echo "🚀 Deploying Bridge cluster"
echo "============================"
echo ""

USE_SSL=0
if [ "$1" = "--ssl" ] || [ "$1" = "ssl" ]; then
  USE_SSL=1
fi

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

if [ $USE_SSL -eq 1 ]; then
  echo "🔐 Starting TLS-terminating HAProxy cluster on port 4000..."
  echo "   (Make sure certs/bridge.pem exists – see PRODUCTION_DEPLOYMENT.md)"
  $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.cluster-ssl.yml up -d
else
  echo "🐳 Starting HTTP-only cluster on port 4000..."
  $DOCKER_COMPOSE up -d
fi

echo "⏳ Waiting for cluster to become healthy..."
sleep 10

if curl -sf http://localhost:4000/health >/dev/null 2>&1; then
  echo "✅ Cluster is up and healthy on http://localhost:4000/health"
  echo ""
  if [ $USE_SSL -eq 1 ]; then
    echo "Public WebSocket endpoints (TLS terminated at HAProxy):"
    echo "  wss://<host>:4000/ws/websocket?type=server"
    echo "  wss://<host>:4000/ws/websocket?type=app"
  else
    echo "Public WebSocket endpoints (HTTP only):"
    echo "  ws://<host>:4000/ws/websocket?type=server"
    echo "  ws://<host>:4000/ws/websocket?type=app"
  fi
  echo ""
  echo "HAProxy stats: http://<host>:8404/stats"
else
  echo "⚠️  Cluster containers started, but health check failed."
  echo "   - Check logs with: $DOCKER_COMPOSE logs -f"
  echo "   - Verify that port 4000 is not in use by another process."
  exit 1
fi
