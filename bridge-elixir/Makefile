.PHONY: help deps compile test test-unit test-integration run docker-build docker-up docker-down docker-logs docker-test clean

help:
	@echo "Bridge Service - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make deps              - Install dependencies"
	@echo "  make compile           - Compile project"
	@echo "  make test              - Run all tests"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests"
	@echo "  make run               - Run single node locally"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build      - Build Docker images"
	@echo "  make docker-up         - Start cluster (2 nodes + HAProxy)"
	@echo "  make docker-down       - Stop cluster"
	@echo "  make docker-logs       - View cluster logs"
	@echo "  make docker-test       - Run integration tests against Docker cluster"
	@echo "  make docker-health     - Check cluster health"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean             - Clean build artifacts"

deps:
	mix deps.get

compile: deps
	mix compile

test: test-unit

test-unit:
	mix test --exclude integration --exclude websocket

test-integration:
	mix test --only integration

run:
	mix run --no-halt

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@echo ""
	@make docker-health

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-health:
	@echo "Checking cluster health..."
	@echo ""
	@echo "=== HAProxy ==="
	@curl -s http://localhost:4000/health | jq . || echo "Failed to reach HAProxy"
	@echo ""
	@echo "=== Node 1 (direct) ==="
	@docker exec bridge-node-1 wget -qO- http://localhost:4001/health 2>/dev/null | jq . || echo "Failed"
	@echo ""
	@echo "=== Node 2 (direct) ==="
	@docker exec bridge-node-2 wget -qO- http://localhost:4002/health 2>/dev/null | jq . || echo "Failed"
	@echo ""
	@echo "=== HAProxy Stats ==="
	@echo "Visit: http://localhost:8404/stats"

docker-test: docker-up
	@echo "Running integration tests against Docker cluster..."
	@sleep 2
	MIX_ENV=test mix test --only integration

clean:
	mix clean
	rm -rf _build deps
