# Agent Guidelines – `bridge-elixir`

This file applies to everything under `bridge-elixir/`. It explains what the
bridge does, how it interacts with Python/mobile components, and how to extend
it safely.

---

## 1. Purpose & Role in the System

The **bridge** is a distributed Elixir/Phoenix service that lets:

- Local servers (e.g. the Python `agent_terminal_app` HTTP server running on a
  laptop) register over WebSockets as "servers".
- Mobile / desktop apps register as "apps" and:
  - Discover available servers.
  - Pair with a server using a 6‑digit code.
  - Send abstract HTTP requests (method/path/headers/body) through the bridge
    to the chosen server.

High‑level data flow:

```text
[Python server] --WebSocket--> [Bridge node(s)] <--WebSocket-- [Mobile app]
                   |                               ^
                   +-- Phoenix.PubSub + clustering +
```

The bridge itself is **HTTP‑agnostic**; it forwards serialized HTTP requests
and responses between paired clients using Phoenix channels.

---

## 2. Key Components

See also `README.md` and `BRIDGE_PLAN.md` for more detail.

- `lib/bridge/endpoint.ex`
  - Phoenix endpoint that exposes:
    - WebSocket socket at `/ws` (e.g. `ws://bridge-host:4000/ws/websocket`).
    - HTTP `/health` endpoint for status and health checks.
  - Configured in `config/config.exs` under `:bridge, Bridge.Endpoint`.

- `lib/bridge/router.ex`
  - Minimal Plug router; currently only `GET /health`.

- `lib/bridge/socket.ex`
  - Defines the Phoenix socket and channels.
  - Entry point for `?type=server` and `?type=app` connections.

- `lib/bridge/server_channel.ex`
  - Channel for "server" clients (Python servers, etc.).
  - Handles:
    - `phx_join` / `register` events.
    - Receiving `http_response` messages from servers.
    - Relaying pairing and HTTP request messages from apps via PubSub.

- `lib/bridge/app_channel.ex`
  - Channel for "app" clients (mobile, desktop).
  - Handles:
    - `list_servers` – enumerates registered servers.
    - `pair_request` – generate 6‑digit code and notify the server.
    - `pair_submit` – validate code and create a session.
    - `http_request` – send request to the server associated with a session.

- `lib/bridge/server_registry.ex`
  - Tracks active servers across the cluster.
  - Provides counts and listings used in `/health` and `list_servers`.

- `lib/bridge/pairing_manager.ex`
  - Generates and validates pairing codes.
  - Enforces TTL and rate limits.

- `lib/bridge/session_manager.ex`
  - Manages pairing sessions between app and server.
  - Associates a `session_id` with both sides for HTTP proxying.

- `config/config.exs`
  - Base configuration: endpoint port, logger format, libcluster gossip setup,
    pairing/session timeouts.

- `config/runtime.exs`
  - Runtime tuning (e.g. distributed Erlang listen ports when `NODE_NAME` is
    set).
  - Future place to optionally enable HTTPS for `Bridge.Endpoint` if we choose
    to implement internal TLS.

- `docker-compose.yml`, `haproxy.cfg`
  - Multi‑node cluster with HAProxy load balancing.
  - Nodes use libcluster Gossip to form a cluster.

- `PRODUCTION_DEPLOYMENT.md`
  - Detailed instructions for single‑node and clustered Docker deployments
    (with optional TLS at HAProxy or Nginx).

---

## 3. External Contracts

When changing behavior here, keep these contracts in mind:

### 3.1. WebSocket endpoints

- Server connection:

  ```text
  ws(s)://<bridge-host>:4000/ws/websocket?type=server
  ```

- App connection:

  ```text
  ws(s)://<bridge-host>:4000/ws/websocket?type=app
  ```

The Python bridge client (`application/python/agent_terminal_app/bridge_client.py`)
and the React Native app both rely on:

- Path: `/ws/websocket` (Phoenix default).
- Query param: `type=server` or `type=app`.
- Phoenix channel message format (`topic`, `event`, `payload`, `ref`).

Do not change these without coordinating updates to those clients.

### 3.2. Message protocol

The JSON message types are documented in `BRIDGE_PLAN.md` and `README.md` and
include:

- From servers:
  - `register`
  - `http_response`
- From apps:
  - `list_servers`
  - `pair_request`
  - `pair_submit`
  - `http_request`
- Bridge‑originated events:
  - `pairing_requested`
  - `paired`

Treat these as a stable public protocol. If you need to add a new field or
message type, do so in a backwards‑compatible way and update the docs + Python
and mobile clients.

### 3.3. HTTP `/health`

Used by HAProxy, Docker tests, and external monitoring.

- Path: `GET /health`.
- Response: JSON with fields including at least:
  - `status` (e.g. `"healthy"`)
  - `node`
  - `cluster_size`
  - `active_servers`
  - `active_sessions`

If you add fields, keep the existing ones.

---

## 4. Development & Testing

### 4.1. Local dev

- Install Elixir/Erlang, then:

  ```bash
  cd bridge-elixir
  mix deps.get
  mix compile
  mix test
  ```

- Single‑node run:

  ```bash
  mix run --no-halt
  ```

### 4.2. Docker & integration tests

- Build and start the default cluster (2 nodes + HAProxy):

  ```bash
  cd bridge-elixir
  make docker-build
  make docker-up
  curl http://localhost:4000/health
  ```

- Run Python‑based integration test against Docker cluster:

  ```bash
  cd bridge-elixir
  ./run-integration-tests.sh
  ```

See `PRODUCTION_DEPLOYMENT.md` for production‑oriented Docker commands
(`docker-compose.single-node.yml`, `docker-compose.cluster-ssl.yml`, helper
scripts in `scripts/`).

### 4.3. Testing expectations

- Any change to core bridge behavior (pairing, HTTP proxying, registry,
  channels, clustering) should be covered by Elixir tests under `test/bridge/`
  and, where relevant, by `test_docker.py` or higher‑level integration tests.
- Do not rely solely on manual testing through the Python or mobile clients for
  protocol changes.

---

## 5. Change Guidelines

- Keep the bridge **stateless with respect to HTTP semantics** – it should only
  forward requests/responses; HTTP routing and business logic belong in the
  Python server (or other backend servers) that connect as "servers".

- Maintain backwards compatibility of:
  - WebSocket endpoints and query params.
  - Message types and fields documented in `BRIDGE_PLAN.md`.
  - `/health` endpoint shape.

- Clustering:
  - The current setup uses `libcluster`'s Gossip strategy and an Erlang
    distribution cookie (`COOKIE`). If changing clustering strategy, update:
    - `config/config.exs` (libcluster config).
    - `PRODUCTION_DEPLOYMENT.md` (deployment expectations).
    - Any HAProxy / Docker notes that assume gossip and multicast.

- TLS:
  - Today the recommended pattern is TLS termination at Nginx/HAProxy or a
    cloud load balancer, **not** inside Phoenix.
  - Internal TLS hooks (`TLS_ENABLED`, `TLS_CERT_PATH`, `TLS_KEY_PATH`) are
    intentionally not wired up yet. If you implement them, mirror the plan in
    `PRODUCTION_DEPLOYMENT.md` and keep the external contracts unchanged.

When in doubt, prefer: protocol stability and clear docs over convenience
shortcuts that lock in a specific environment.
