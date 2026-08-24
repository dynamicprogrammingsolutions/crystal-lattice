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

High-level data flow:

```text
[Frontend] --WebSocket or HTTP--> [Bridge node(s)] --WebSocket control--> [Python server]
                                      |                                      |
                                      +-- Phoenix.PubSub + clustering -------+
                                                                             |
                                                                    [local HTTP app]
```

The bridge treats proxied application paths and bodies as opaque. The legacy
frontend path serializes HTTP-shaped requests through Phoenix channels. The
opt-in HTTP path keeps metadata on the Python server WebSocket and transfers
body bytes through HTTP endpoints.

---

## 2. Key Components

See `docs/index.md` for current package documentation and the root
bridge-connectivity specification for the maintained cross-package contract.
`BRIDGE_PLAN.md` is a legacy planning artifact.

- `lib/bridge/endpoint.ex`
  - Phoenix endpoint that exposes:
    - WebSocket socket at `/ws` (e.g. `ws://bridge-host:4000/ws/websocket`).
    - HTTP `/bridge/v1/*` routes for control, proxying, and raw transfers.
    - HTTP `/health` endpoint for status and health checks.
  - Configured in `config/config.exs` under `:bridge, Bridge.Endpoint`.

- `lib/bridge/http_router.ex`
  - Runs before JSON parsing so it can consume raw request bytes.
  - Owns HTTP capability, discovery, pairing, resume, proxy, and transfer
    routes.

- `lib/bridge/router.ex`
  - Owns `GET /health`.

- `lib/bridge/socket.ex`
  - Defines the Phoenix socket and channels.
  - Entry point for `?type=server` and `?type=app` connections.

- `lib/bridge/server_channel.ex`
  - Channel for "server" clients (Python servers, etc.).
  - Handles:
    - `phx_join` / `register` events.
    - Receiving legacy responses and v2 response metadata from servers.
    - Relaying pairing, legacy requests, v2 metadata, and cancellation.

- `lib/bridge/app_channel.ex`
  - Channel for "app" clients (mobile, desktop).
  - Handles:
    - `list_servers` – enumerates registered servers.
    - `pair_request` – generate 6‑digit code and notify the server.
    - `pair_submit` – validate code and create a session.
    - Legacy full and chunked HTTP-shaped request messages.

- `lib/bridge/server_registry.ex`
  - Tracks active servers across the cluster.
  - Provides counts and listings used in `/health` and `list_servers`.

- `lib/bridge/pairing_manager.ex`
  - Generates and validates pairing codes.
  - Enforces TTL and rate limits.

- `lib/bridge/session_manager.ex`
  - Manages ephemeral legacy pairing sessions between app and server.

- `lib/bridge/pairing_token.ex`, `persistent_pairing_manager.ex`
  - Stateless signed logical-pairing credentials.

- `lib/bridge/http_transfer.ex`, `http_transfer_token.ex`
  - Supervised raw-byte transfer coordination, backpressure, limits,
    cancellation, and signed direction-scoped transfer credentials.

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

- `deploy/remote-docker/`
  - Reusable single-node remote Docker deployment.
  - Takes host-specific access, public URL, and the stable signing secret from
    environment variables supplied by a gitignored local wrapper.
  - Preserves an explicit Compose project identity and validates both origin
    and public HTTP v1 capability endpoints.

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

The maintained message contract is documented in `docs/bridge-protocol.md`
and the root bridge-connectivity protocol specification. It includes:

- From servers:
  - `register`
  - legacy `http_response*`
  - `http_response_v2_init`
- From apps:
  - `list_servers`
  - `pair_request`
  - `pair_submit`
  - `resume_session`
  - legacy `http_request*`
- Bridge‑originated events:
  - `pairing_requested`
  - `paired`
  - `http_request_v2`
  - `http_request_v2_cancel`
  - `superseded`

Treat these as a stable public protocol. If you need to add a new field or
message type, do so in a backwards‑compatible way and update the docs + Python
and mobile clients.

### 3.3. HTTP bridge protocol

HTTP and hybrid frontends rely on versioned `/bridge/v1/*` routes for
capability negotiation, discovery, pairing, resume validation, proxying, and
server body transfer.

- Frontends authenticate proxy requests with `X-Crystal-Bridge-Token`.
- Server body-transfer routes use short-lived bearer credentials.
- Keep application `Authorization` available to the local backend.
- Keep proxy/transfer bodies raw and outside JSON/WebSocket frames.
- Do not add automatic fallback or replay to the WebSocket path.

### 3.4. HTTP `/health`

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

- Keep the bridge **opaque with respect to application semantics**. It may
  implement transport-level HTTP routing, streaming, authentication, limits,
  and header filtering, but application routing and business logic belong in
  the registered server.

- Maintain backwards compatibility of:
  - WebSocket endpoints and query params.
  - Legacy messages documented in the maintained protocol.
  - Versioned HTTP v1 routes and v2 server control events.
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
