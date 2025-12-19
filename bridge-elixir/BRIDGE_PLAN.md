# Bridge Service - Detailed Implementation Plan

## Overview
An Elixir-based distributed bridge service that enables communication between local servers and mobile apps across different networks by acting as a relay/proxy.

## Technology Stack

### Core Technologies
- **Elixir 1.14+** - Runtime and language
- **Phoenix Framework** - WebSocket handling and HTTP server
- **Phoenix.PubSub** - Distributed message passing between nodes
- **libcluster** - Automatic cluster formation and management
- **Cowboy** - HTTP server (included with Phoenix)
- **Jason** - JSON encoding/decoding

### Deployment & Testing
- **Docker** - Containerization
- **Docker Compose** - Multi-node orchestration
- **HAProxy** - Load balancing across bridge instances
- **ExUnit** - Elixir's built-in testing framework
- **WebSockex** - WebSocket client for testing

### Why These Choices?
1. **Elixir**: Built for distributed systems, excellent concurrency model (BEAM VM)
2. **Phoenix.PubSub**: Native support for clustering and message broadcasting
3. **WebSockets**: Full-duplex communication, ideal for proxying HTTP requests
4. **libcluster**: Handles service discovery in Docker/Kubernetes environments
5. **HAProxy**: Simple, reliable load balancing with health checks

## Architecture

### High-Level Flow
```
[Server PC] --WS--> [Bridge Node 1] --|
                                       |--> [Distributed State]
[Mobile App] --WS-> [Bridge Node 2] --|
```

### Core Components

#### 1. Connection Manager
- Maintains WebSocket connections from servers and apps
- Tracks connection metadata (type, ID, name, location)
- Uses GenServer per connection for isolation
- Stores connections in Registry for fast lookup

#### 2. Server Registry
- Distributed ETS table (via :global or Phoenix.PubSub)
- Stores active servers across all nodes
- Schema: `{server_id, node, display_name, computer_name, location, connected_at}`
- Automatically removes servers on disconnect

#### 3. Pairing Manager
- Generates and validates 6-digit codes
- Stores pending pairing requests with TTL (5 minutes)
- Schema: `{code, server_id, client_id, expires_at}`
- Uses ETS with automatic expiration cleanup

#### 4. Message Router
- Routes messages between paired connections
- Handles cross-node routing via PubSub
- Supports request/response correlation (request_id)
- Implements timeout handling

#### 5. HTTP Proxy
- Translates HTTP requests to WebSocket messages
- Forwards to appropriate server connection
- Waits for response and returns to app
- Handles streaming for large payloads

### Distributed State Management

#### Connection Tracking
```elixir
# Each node tracks its local connections
%{
  server_id => %{
    pid: pid(),
    node: node(),
    display_name: "John's Computer",
    computer_name: "MacBook-Pro.local",
    location: "San Francisco, CA",
    connected_at: DateTime.t()
  }
}
```

#### Cross-Node Communication
- Phoenix.PubSub topics:
  - `servers:list` - Server registry updates
  - `pairing:{server_id}` - Pairing events
  - `tunnel:{session_id}` - HTTP proxy messages

#### Cluster Formation
```elixir
# libcluster strategy for Docker
config :libcluster,
  topologies: [
    bridge: [
      strategy: Cluster.Strategy.Gossip,
      config: [
        port: 45892,
        multicast_addr: "230.1.1.251"
      ]
    ]
  ]
```

## Message Protocol Specification

### WebSocket Message Format
All messages are JSON objects with a `type` field.

#### Server Messages

**1. Register**
```json
{
  "type": "register",
  "server_id": "uuid-v4",
  "display_name": "John's Computer",
  "computer_name": "MacBook-Pro.local",
  "location": "San Francisco, CA"  // Optional
}
```

**2. Pairing Code Display**
```json
{
  "type": "pairing_requested",
  "client_id": "uuid-v4",
  "code": "123456",
  "expires_at": "2025-01-01T12:00:00Z"
}
```

**3. Pairing Success**
```json
{
  "type": "paired",
  "client_id": "uuid-v4",
  "session_id": "uuid-v4"
}
```

**4. HTTP Request (from bridge to server)**
```json
{
  "type": "http_request",
  "request_id": "uuid-v4",
  "method": "GET",
  "path": "/api/data",
  "headers": {"Authorization": "Bearer token"},
  "body": null  // or base64 encoded for binary
}
```

**5. HTTP Response (from server to bridge)**
```json
{
  "type": "http_response",
  "request_id": "uuid-v4",
  "status": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"result\": \"success\"}"  // base64 for binary
}
```

#### App Messages

**1. List Servers**
```json
{
  "type": "list_servers"
}
```

**2. Server List Response**
```json
{
  "type": "server_list",
  "servers": [
    {
      "server_id": "uuid-v4",
      "display_name": "John's Computer",
      "computer_name": "MacBook-Pro.local",
      "location": "San Francisco, CA"
    }
  ]
}
```

**3. Request Pairing**
```json
{
  "type": "pair_request",
  "server_id": "uuid-v4",
  "client_id": "uuid-v4"
}
```

**4. Submit Pairing Code**
```json
{
  "type": "pair_submit",
  "server_id": "uuid-v4",
  "client_id": "uuid-v4",
  "code": "123456"
}
```

**5. Pairing Success**
```json
{
  "type": "paired",
  "session_id": "uuid-v4"
}
```

**6. HTTP Request (from app)**
```json
{
  "type": "http_request",
  "request_id": "uuid-v4",
  "session_id": "uuid-v4",
  "method": "PUT",
  "path": "/api/data",
  "headers": {},
  "body": "{\"value\": 42}"
}
```

**7. HTTP Response**
```json
{
  "type": "http_response",
  "request_id": "uuid-v4",
  "status": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"success\": true}"
}
```

### Error Messages
```json
{
  "type": "error",
  "code": "PAIRING_FAILED",
  "message": "Invalid pairing code",
  "details": {}
}
```

## Security Considerations

### Authentication & Authorization
1. **Pairing Code**: 6-digit numeric code (1,000,000 combinations)
2. **Code Expiration**: 5 minutes TTL
3. **Rate Limiting**: Max 3 code submission attempts per minute per client
4. **Session ID**: UUID v4 after successful pairing
5. **TLS/SSL**: Required for production (wss://)

### Additional Security Measures
- Connection timeout: 30 seconds idle
- Max message size: 10 MB
- Request timeout: 60 seconds
- Max active sessions per server: 10

## Docker Setup

### Architecture
```
┌─────────────────────────────────────────────────┐
│                   HAProxy                       │
│            (Load Balancer: :4000)               │
└──────────┬─────────────────────┬────────────────┘
           │                     │
           v                     v
    ┌──────────────┐      ┌──────────────┐
    │ Bridge Node 1│      │ Bridge Node 2│
    │   (:4001)    │◄────►│   (:4002)    │
    └──────────────┘      └──────────────┘
         Clustered via Gossip Protocol
```

### Services
1. **bridge-node-1**: First Elixir node
2. **bridge-node-2**: Second Elixir node  
3. **haproxy**: Load balancer (distributes connections)

### Network
- Internal Docker network for cluster gossip
- Exposed port 4000 for WebSocket connections
- HAProxy distributes load using round-robin

## Implementation Roadmap

### Phase 1: Core Bridge (MVP)
- [ ] Phoenix project setup
- [ ] WebSocket connection handling
- [ ] Server registration
- [ ] Server listing
- [ ] Basic message routing (single node)

### Phase 2: Pairing
- [ ] Pairing code generation
- [ ] Code validation with expiration
- [ ] Session management
- [ ] Pairing flow end-to-end

### Phase 3: HTTP Proxy
- [ ] HTTP request serialization
- [ ] Request/response correlation
- [ ] Timeout handling
- [ ] Error handling

### Phase 4: Distribution
- [ ] libcluster setup
- [ ] Phoenix.PubSub integration
- [ ] Distributed server registry
- [ ] Cross-node message routing

### Phase 5: Production Ready
- [ ] TLS/SSL configuration
- [ ] Rate limiting
- [ ] Monitoring & metrics
- [ ] Health checks
- [ ] Docker Compose setup
- [ ] HAProxy configuration

### Phase 6: Testing
- [ ] Unit tests for each component
- [ ] Integration tests with Docker
- [ ] Multi-node scenario tests
- [ ] Load testing

## Testing Strategy

### Unit Tests (ExUnit)
```elixir
# Test server registration
test "registers server and broadcasts to cluster"
test "generates unique 6-digit pairing code"
test "validates pairing code within expiration"
test "routes HTTP request to correct server"
```

### Integration Tests (Docker Compose)
```elixir
# Test distributed scenarios
test "server connects to node 1, app connects to node 2"
test "pairing works across nodes"
test "HTTP proxy works across nodes"
test "server disconnect removes from registry"
```

### Test Setup
1. Start Docker Compose (2 nodes + HAProxy)
2. WebSocket client connects as "server"
3. Another client connects as "app"
4. Execute pairing flow
5. Send HTTP request through tunnel
6. Verify response
7. Cleanup

### Test Client (Elixir)
```elixir
defmodule BridgeTest.Client do
  use WebSockex
  
  def connect_as_server(url, name) do
    WebSockex.start_link(url, __MODULE__, %{type: :server})
  end
  
  def register(pid, server_info) do
    send_message(pid, %{type: "register", ...})
  end
end
```

## Configuration

### Environment Variables
```bash
# Node identification
NODE_NAME=bridge@bridge-node-1
COOKIE=bridge_secret_cookie

# Network
PORT=4000
HOST=0.0.0.0

# Clustering
CLUSTER_STRATEGY=gossip
GOSSIP_PORT=45892
GOSSIP_MULTICAST_ADDR=230.1.1.251

# Security
PAIRING_CODE_TTL=300  # 5 minutes
MAX_PAIRING_ATTEMPTS=3
SESSION_TIMEOUT=3600  # 1 hour

# TLS (production)
TLS_ENABLED=false
TLS_CERT_PATH=/path/to/cert.pem
TLS_KEY_PATH=/path/to/key.pem
```

## API Reference

### WebSocket Endpoints

#### `/ws/server` - Server Connection
- Authenticates server
- Registers server in distributed registry
- Handles HTTP proxy requests
- Manages pairing flow

#### `/ws/app` - App Connection
- Lists available servers
- Initiates pairing
- Validates pairing codes
- Proxies HTTP requests to servers

### HTTP Endpoints (for monitoring)

#### `GET /health` - Health Check
```json
{
  "status": "healthy",
  "node": "bridge@bridge-node-1",
  "cluster_size": 2,
  "active_servers": 5,
  "active_clients": 12
}
```

#### `GET /metrics` - Prometheus Metrics
```
bridge_active_servers 5
bridge_active_clients 12
bridge_cluster_nodes 2
bridge_http_requests_total 1234
```

## Performance Targets

- **Latency**: < 100ms additional overhead for HTTP proxy
- **Throughput**: > 1000 concurrent connections per node
- **Availability**: 99.9% uptime with 2+ nodes
- **Recovery**: < 5s cluster healing after node failure

## Future Enhancements

1. **Authentication**: JWT tokens instead of pairing codes
2. **Encryption**: End-to-end encryption between server and app
3. **Compression**: WebSocket message compression
4. **Streaming**: Support for large file uploads/downloads
5. **Kubernetes**: Deployment configuration and service discovery
6. **Dashboard**: Web UI for monitoring active connections
7. **Client SDKs**: Official libraries for Node.js/Swift/Kotlin
8. **Analytics**: Connection metrics and usage statistics

## References

- [Phoenix Framework](https://phoenixframework.org/)
- [libcluster Documentation](https://hexdocs.pm/libcluster/)
- [Phoenix.PubSub](https://hexdocs.pm/phoenix_pubsub/)
- [Elixir Registry](https://hexdocs.pm/elixir/Registry.html)
- [HAProxy Configuration](http://www.haproxy.org/)
