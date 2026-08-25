# Bridge service quickstart

## Prerequisites

- Elixir 1.14 or later with a compatible Erlang/OTP release
- Docker when running the provided multi-node environment
- Python 3 for the bridge-owned Docker integration tests

## Run one bridge node

From `bridge-elixir`:

```bash
mix deps.get
mix run --no-halt
```

The default endpoints are:

```text
Health:           http://127.0.0.1:4000/health
Server WebSocket: ws://127.0.0.1:4000/ws/websocket?type=server
App WebSocket:    ws://127.0.0.1:4000/ws/websocket?type=app
HTTP bridge API:  http://127.0.0.1:4000/bridge/v1
```

Check health:

```bash
curl http://127.0.0.1:4000/health
```

## Register the Crystal Lattice server

From an installed terminal application:

```bash
crystal-lattice --server --console --enable-bridge \
  --bridge-url ws://127.0.0.1:4000/ws/websocket
```

The terminal application opens the server control WebSocket, registers a
stable server identity, and forwards bridge requests to its local HTTP
listener. Keep the command running.

Use `--bridge-server-id` or the normal project profile to retain the same
server identity across restarts. Use `--bridge-http-base` only when the public
HTTP origin cannot be derived from the WebSocket URL.

## Pair a frontend

In Crystal Lattice Control:

1. Create a new connection.
2. Choose Bridge.
3. Enter `ws://<reachable-host>:4000/ws/websocket`.
4. Leave WebSocket selected for the compatibility path, or explicitly select
   HTTP or Hybrid.
5. Select the registered server.
6. Enter the six-digit code printed by the server process.

The saved pairing credential can be used after reconnect or bridge restart as
long as it remains valid, the bridge deployment retains the same signing
secret, and the server returns with the same `server_id`.

For a physical device, use an address reachable from that device rather than
`127.0.0.1`.

## Run the two-node bridge

```bash
make docker-up
curl http://127.0.0.1:4000/health
```

The provided environment starts two bridge nodes behind round-robin HAProxy.
Stop it with:

```bash
make docker-down
```

The frontend continues to use one public WebSocket URL. HTTP pairing and body
transfer do not require affinity to one bridge node.

## Run tests

```bash
mix test
./run-integration-tests.sh
```

The first command runs the Elixir suite. The second uses the two-node
Docker/HAProxy environment to cover legacy registration/discovery/pairing and
cross-node HTTP pairing plus raw body transfer.

For the full SDK-to-Python E2E:

```bash
npm --workspace @crystal-lattice/frontend-sdk run integration:bridge
```

See [Testing](development/testing.md) for test ownership and optional hosted
commands.

## Production

Do not expose a plain HTTP bridge directly to the internet. Use the
[production deployment guide](../PRODUCTION_DEPLOYMENT.md) for TLS termination,
cluster configuration, shared secrets, edge forwarding, and cleanup.
