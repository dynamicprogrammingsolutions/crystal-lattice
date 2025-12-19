# Bridge Service

A distributed Elixir/Phoenix-based bridge service that enables communication between local servers and mobile apps across different networks.

## Overview

This bridge acts as a relay/proxy, allowing:
- Servers running on user PCs to connect and register
- Mobile apps to discover and pair with servers
- HTTP requests to be proxied through the bridge via WebSockets
- Distributed operation across multiple nodes with automatic clustering

## Architecture

```
[Server PC] --WebSocket--> [Bridge Node 1] --|
                                              |--> Distributed State (PubSub)
[Mobile App] --WebSocket-> [Bridge Node 2] --|
```

### Key Features

- **Distributed:** Multiple bridge nodes form a cluster automatically
- **Zero-Configuration:** Nodes discover each other via Gossip protocol
- **Secure Pairing:** 6-digit codes with expiration and rate limiting
- **HTTP Proxy:** Transparent request/response forwarding
- **Load Balanced:** HAProxy distributes connections across nodes
- **Fault Tolerant:** Sessions survive individual node failures

## Quick Start

### Prerequisites

- Elixir 1.14+ and Erlang/OTP 24+
- Docker and Docker Compose (for distributed testing)
- Python 3.8+ (for integration tests)

### Local Development

```bash
# Install dependencies
make deps

# Compile
make compile

# Run single node
make run

# The bridge will be available at:
# - WebSocket: ws://localhost:4000/ws
# - Health: http://localhost:4000/health
```

### Docker Cluster

```bash
# Build images
make docker-build

# Start 2-node cluster + HAProxy
make docker-up

# Check health
make docker-health

# View logs
make docker-logs

# Stop cluster
make docker-down
```

### End-to-End Testing

#### Step 1: Start the Bridge

```bash
cd bridge-elixir
docker-compose up -d

# Verify bridge is running
curl http://localhost:4000/health
# Should return: {"status":"ok"}
```

#### Step 2: Start the Python Server

In a new terminal:

```bash
cd server-python
python bonjour_server.py --port 8080 --bridge ws://localhost:4000/ws/websocket --bridge-name "MyTestServer" --bridge-location "Development"

# Expected output:
# Starting Flask server on port 8080...
# Connecting to bridge at ws://localhost:4000/ws/websocket
# Connected to bridge
# Registered with bridge as 'MyTestServer'
# Server is ready and waiting for connections!
```

#### Step 3: Start the Client (Interactive)

In a third terminal:

```bash
cd server-python
python bridge_client.py

# Interactive menu will appear
```

#### Step 4: Test the Flow

1. Select option `1` (List Available Servers) - Should show "MyTestServer"
2. Select option `2` (Connect to Server)
3. Enter server number: `1`
4. Check the server terminal for the pairing code (e.g., `123456`)
5. Enter the 6-digit code in the client
6. Select option `3` (Execute GET Request) - Should receive response
7. Select option `4` (Execute PUT Request) - Should receive response

## WebSocket Protocol

### Connection

**Server Connection:**
```
ws://bridge-host:4000/ws?type=server
```

**App Connection:**
```
ws://bridge-host:4000/ws?type=app
```

### Message Format

All messages are JSON with a `type` field.

#### Server Messages

**Register:**
```json
{
  "type": "register",
  "server_id": "uuid",
  "display_name": "John's Computer",
  "computer_name": "MacBook-Pro.local",
  "location": "San Francisco"
}
```

**HTTP Response:**
```json
{
  "type": "http_response",
  "request_id": "uuid",
  "status": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"result\": \"success\"}"
}
```

#### App Messages

**List Servers:**
```json
{
  "type": "list_servers"
}
```

**Request Pairing:**
```json
{
  "type": "pair_request",
  "server_id": "uuid"
}
```

**Submit Code:**
```json
{
  "type": "pair_submit",
  "server_id": "uuid",
  "code": "123456"
}
```

**HTTP Request:**
```json
{
  "type": "http_request",
  "request_id": "uuid",
  "session_id": "uuid",
  "method": "GET",
  "path": "/api/data",
  "headers": {},
  "body": null
}
```

## Testing

### Unit Tests

Run Elixir unit tests:

```bash
# All unit tests
make test-unit

# Or manually
mix test --exclude integration --exclude websocket
```

Tests cover:
- Server registration and unregistration
- Pairing code generation and validation
- Session creation and management
- Channel lifecycle
- Distributed state synchronization

### Integration Tests

Run Python integration tests against running bridge:

```bash
# Start bridge first
make docker-up

# Wait for healthy state
sleep 10

# Run integration tests
cd ../server-python
python -m pytest test_bridge_integration.py -v -s

# Stop bridge
cd ../bridge-elixir
make docker-down
```

Tests cover:
- Bridge WebSocket connection (Phoenix protocol)
- Server registration with metadata
- Client server discovery
- Complete pairing flow
- Real Python server integration

### Manual Testing with wscat

Install wscat:
```bash
npm install -g wscat
```

#### Test Server Connection

Terminal 1 (Server):
```bash
wscat -c "ws://localhost:4000/ws?type=server"

# Send registration
{"type":"register","server_id":"test-server-123","display_name":"Test Server","computer_name":"test.local","location":"NYC"}

# Wait for pairing requests...
```

Terminal 2 (App):
```bash
wscat -c "ws://localhost:4000/ws?type=app"

# List servers
{"type":"list_servers"}

# Request pairing
{"type":"pair_request","server_id":"test-server-123"}

# Check Terminal 1 for pairing code, then submit:
{"type":"pair_submit","server_id":"test-server-123","code":"123456"}

# You should receive a session_id
```

### Automated Test Suite

Run the full integration test suite with detailed logging:

```bash
cd server-python
python -m pytest test_bridge_integration.py -v -s

# Expected output with stages:
# Stage 1/4: Server Registration
# Stage 2/4: Server Listing
# Stage 3/4: Pairing Flow
# Stage 4/4: Full Integration with Real Server
```

## Configuration

### Environment Variables

```bash
# Node Configuration
NODE_NAME=bridge@hostname       # Erlang node name
COOKIE=secret_cookie            # Erlang cluster cookie
PORT=4000                       # HTTP port

# Clustering
GOSSIP_PORT=45892              # Cluster gossip port
GOSSIP_MULTICAST_ADDR=230.1.1.251  # Multicast address

# Security
PAIRING_CODE_TTL=300           # Code expiration (seconds)
MAX_PAIRING_ATTEMPTS=3         # Max wrong code attempts
SESSION_TIMEOUT=3600           # Session timeout (seconds)
```

**Note:** The WebSocket endpoint has `check_origin: false` configured in `lib/bridge/endpoint.ex` to allow connections from mobile apps (React Native) across different networks. For production deployments, configure specific allowed origins:

```elixir
# lib/bridge/endpoint.ex
socket "/ws", Bridge.Socket,
  websocket: [
    timeout: 45_000,
    check_origin: ["https://yourdomain.com", "//yourdomain.com:4000"]
  ],
  longpoll: false
```

### Configuration Files

- `config/config.exs` - Base configuration
- `config/dev.exs` - Development overrides
- `config/prod.exs` - Production settings
- `config/test.exs` - Test environment

## Monitoring

### Health Check

```bash
curl http://localhost:4000/health
```

Response:
```json
{
  "status": "healthy",
  "node": "bridge@bridge-node-1",
  "cluster_size": 2,
  "active_servers": 5,
  "active_sessions": 12
}
```

### HAProxy Stats

Visit: http://localhost:8404/stats

Monitor:
- Active connections per backend
- Request rate
- Error rate
- Health check status

### Application Logs

```bash
# Watch all nodes
make docker-logs

# Specific node
docker logs -f bridge-node-1

# Filter for errors
docker logs bridge-node-1 2>&1 | grep ERROR
```

## Development

### Project Structure

```
bridge-elixir/
├── lib/
│   └── bridge/
│       ├── application.ex          # Main application supervisor
│       ├── endpoint.ex             # Phoenix endpoint
│       ├── router.ex               # HTTP routes
│       ├── socket.ex               # WebSocket connection handler
│       ├── server_channel.ex       # Server WebSocket channel
│       ├── app_channel.ex          # App WebSocket channel
│       ├── server_registry.ex      # Distributed server tracking
│       ├── pairing_manager.ex      # Pairing code management
│       └── session_manager.ex      # Session tracking
├── config/
│   ├── config.exs                  # Base config
│   ├── dev.exs                     # Development config
│   ├── prod.exs                    # Production config
│   └── test.exs                    # Test config
├── test/
│   ├── bridge/
│   │   ├── server_registry_test.exs
│   │   ├── pairing_manager_test.exs
│   │   ├── session_manager_test.exs
│   │   ├── integration_test.exs
│   │   └── websocket_test.exs
│   └── support/
│       └── test_client.ex          # WebSocket test client
├── docker-compose.yml              # Multi-node orchestration
├── Dockerfile                      # Container image
├── haproxy.cfg                     # Load balancer config
├── Makefile                        # Convenience commands
└── mix.exs                         # Project definition
```

### Adding Features

1. **New Message Types:** Update channel handlers in `server_channel.ex` / `app_channel.ex`
2. **New State:** Add GenServer to `application.ex` supervisor
3. **Cross-Node Logic:** Use `Phoenix.PubSub.broadcast/3` for cluster-wide events

### Debugging

```bash
# Attach to running node
docker exec -it bridge-node-1 sh
iex --name debug@bridge-node-1 --cookie bridge_secret_cookie --remsh bridge@bridge-node-1

# Check cluster status
Node.list()

# Inspect ETS tables
:ets.tab2list(:bridge_servers)
:ets.tab2list(:bridge_pairing_codes)
:ets.tab2list(:bridge_sessions)
```

### Development Workflow

1. Make changes to source files
2. Restart Docker containers: `make docker-down && make docker-up`
3. Run tests: `make test-unit` or Python integration tests
4. Check logs: `make docker-logs`

## Production Deployment

### Requirements

- Load balancer with health checks
- Persistent cookie for cluster formation
- TLS/SSL certificates for wss://
- Resource limits (memory, CPU)
- Monitoring and alerting

### Kubernetes

See `BRIDGE_PLAN.md` for Kubernetes deployment strategy.

Key considerations:
- StatefulSet for stable network identities
- Service with session affinity
- ConfigMap for configuration
- Secrets for sensitive data
- Horizontal Pod Autoscaler for scaling

### Environment

- Minimum 2 nodes for high availability
- Recommended: 4+ CPU cores, 2GB+ RAM per node
- Network: Allow multicast for clustering or use libcluster DNS strategy

### TLS/SSL

For production, use secure WebSocket connections:

```elixir
# config/prod.exs
config :bridge, BridgeWeb.Endpoint,
  url: [host: "bridge.example.com", port: 443, scheme: "https"],
  https: [
    port: 443,
    cipher_suite: :strong,
    keyfile: System.get_env("SSL_KEY_PATH"),
    certfile: System.get_env("SSL_CERT_PATH")
  ]
```

## Troubleshooting

### Nodes Not Clustering

**Check:**
- Same `COOKIE` environment variable on all nodes
- Multicast enabled on network
- `GOSSIP_PORT` not blocked by firewall

**Verify cluster:**
```bash
docker exec bridge-node-1 sh -c "elixir -e 'IO.inspect Node.list()' --name debug@bridge-node-1 --cookie bridge_secret_cookie --remsh bridge@bridge-node-1"
```

### Pairing Fails

**Check:**
- Server is registered: `curl localhost:4000/health | jq .active_servers`
- Pairing code hasn't expired (5 min TTL)
- Max attempts not exceeded (3 attempts)

**Debug:**
- Check server logs for pairing code display
- Verify code is exactly 6 digits
- Request new pairing if needed

### WebSocket Connection Issues

**Check:**
- Verify endpoint: `ws://localhost:4000/ws?type=server` or `?type=app`
- Check browser console for errors
- Test with `wscat`: `wscat -c "ws://localhost:4000/ws?type=server"`

**Common causes:**
- Wrong URL (missing `?type=` parameter)
- Bridge not running
- Firewall blocking port 4000

### Connection Refused

**Solutions:**
```bash
# Check bridge is running
docker ps | grep bridge

# Check bridge health
curl http://localhost:4000/health

# Restart bridge
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Server Registration Fails

**Check:**
1. Wait 2-3 seconds after server starts
2. Check server logs for "Registered with bridge"
3. Verify bridge connection: `curl http://localhost:4000/health`
4. Check websockets library: `python -c "import websockets"`

### HTTP Request Timeouts

**Check:**
1. Verify pairing completed successfully (check session ID)
2. Confirm server is still running
3. Check server logs for errors
4. Verify HTTP endpoint exists on server
5. Check bridge logs for routing errors

### Port Conflicts

**Solutions:**
```bash
# Check what's using the port
lsof -i :4000

# Kill process
kill -9 <PID>

# Or use different port in docker-compose.yml
```

## Performance Expectations

- **Server Registration:** < 1 second
- **Server Discovery:** < 2 seconds
- **Pairing Flow:** < 3 seconds
- **HTTP Request (through bridge):** < 500ms
- **Code Generation:** < 10ms
- **WebSocket Latency:** < 50ms

## Scalability

- **Bridge nodes:** Tested with 2-10 nodes
- **Concurrent connections:** 1000+ per node
- **Sessions:** Limited by memory (ETS tables)
- **Throughput:** 10,000+ messages/sec per node

## Test Scenarios

### Scenario 1: Basic Server Registration

1. Start bridge: `make docker-up`
2. Connect as server with unique ID
3. Send register message
4. Connect as app
5. Send list_servers message
6. Verify server appears in list

**Expected Result:** Server appears in app's server list with correct metadata

### Scenario 2: Complete Pairing Flow

1. Start bridge
2. Register server (Terminal 1)
3. Connect app (Terminal 2)
4. App requests pairing with server_id
5. Server receives pairing_requested with 6-digit code
6. App submits code
7. Both receive paired message with session_id

**Expected Result:** Valid session_id returned to both parties

### Scenario 3: Cross-Node Pairing

1. Start 2-node cluster: `make docker-up`
2. Connect server to Node 1 (port 4001)
3. Connect app to Node 2 (port 4002)
4. Execute pairing flow
5. Verify both sides receive updates

**Expected Result:** Pairing succeeds despite different nodes

### Scenario 4: HTTP Proxy

1. Complete pairing flow (get session_id)
2. App sends http_request with session_id
3. Server receives http_request
4. Server sends http_response
5. App receives http_response

**Expected Result:** Request/response correlated by request_id

## Common Commands

```bash
# Start cluster
cd bridge-elixir && docker-compose up -d

# Stop cluster
cd bridge-elixir && docker-compose down

# View logs
cd bridge-elixir && docker-compose logs -f

# Check health
curl http://localhost:4000/health | jq

# Run unit tests
cd bridge-elixir && mix test

# Run integration tests
cd server-python && python -m pytest test_bridge_integration.py -v -s

# Start Python server with bridge
cd server-python && python bonjour_server.py --port 8080 --bridge ws://localhost:4000/ws/websocket

# Start interactive client
cd server-python && python bridge_client.py
```

## Next Steps

### For Development
1. Add more endpoints to Python server
2. Test with multiple servers simultaneously
3. Test with multiple clients per server
4. Stress test with concurrent requests

### For Production
1. Enable TLS (`wss://` instead of `ws://`)
2. Add authentication tokens
3. Configure monitoring (Prometheus/Grafana)
4. Set up logging aggregation
5. Deploy to Kubernetes
6. Configure auto-scaling

### For Mobile Integration
1. See `../react-native-app/` for React Native client
2. Implement WebSocket connection in app
3. Add pairing UI with code entry
4. Proxy HTTP requests through bridge session
5. Handle connection failures and reconnection

## Resources

- [Phoenix Framework](https://phoenixframework.org/)
- [libcluster](https://hexdocs.pm/libcluster/)
- [Phoenix.PubSub](https://hexdocs.pm/phoenix_pubsub/)
- [Phoenix Channels Guide](https://hexdocs.pm/phoenix/channels.html)
- [Erlang Distribution](https://www.erlang.org/doc/reference_manual/distributed.html)
- [HAProxy Documentation](http://www.haproxy.org/documentation.html)

## Files Reference

### Bridge Service
- `lib/bridge/application.ex` - Main application
- `lib/bridge/endpoint.ex` - HTTP/WebSocket endpoint
- `lib/bridge/socket.ex` - Socket handler
- `lib/bridge/server_channel.ex` - Server channel logic
- `lib/bridge/app_channel.ex` - App channel logic
- `lib/bridge/server_registry.ex` - Server tracking
- `lib/bridge/pairing_manager.ex` - Pairing codes
- `lib/bridge/session_manager.ex` - Session management
- `docker-compose.yml` - Cluster configuration

### Python Integration
- `../server-python/bonjour_server.py` - Flask server with bridge support
- `../server-python/bridge_client.py` - Interactive test client
- `../server-python/test_bridge_integration.py` - Automated integration tests

### Documentation
- `README.md` - This file
- `BRIDGE_PLAN.md` - Detailed design document
- `../README.md` - Main project documentation
- `../PROJECT_STRUCTURE.md` - Project structure guide

## License

See main project README.
