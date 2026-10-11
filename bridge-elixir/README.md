# Crystal Lattice Bridge

The Bridge is a distributed Elixir/Phoenix service that lets remote Crystal
Lattice frontends discover and pair with registered local servers, then relay
HTTP-shaped application requests across networks.

The registered server always uses a Phoenix WebSocket for registration and
control. Frontends can use:

- WebSocket-only mode for the established compatibility path;
- HTTP-only mode for discovery, pairing, events, and proxied requests;
- hybrid mode, where only exact `GET /events` requests use the frontend
  WebSocket and all other operations use HTTP.

HTTP is the frontend product default. WebSocket and hybrid remain explicit
development diagnostics, and HTTP failures do not fall back automatically.

## Quick start

Prerequisites:

- Elixir 1.14 or later with compatible Erlang/OTP
- Docker for the provided clustered environment
- Python 3 for bridge-owned integration tests

Run one bridge node:

```bash
mix deps.get
mix run --no-halt
curl http://127.0.0.1:4000/health
```

Default public endpoints:

```text
WebSocket: /ws/websocket?type=server|app
Health:    /health
HTTP API:  /bridge/v1/*
```

Run the two-node Docker/HAProxy environment:

```bash
make docker-up
curl http://127.0.0.1:4000/health
```

Register the terminal application:

```bash
crystal-lattice --server --console --enable-bridge \
  --bridge-url ws://127.0.0.1:4000/ws/websocket
```

Then create a Bridge connection in Crystal Lattice Control, select the
registered server, and enter the six-digit code printed by the server process.

See the [quickstart](docs/quickstart.md) for mode selection, physical-device
addresses, stable server identity, and teardown.

## Testing

Run the Elixir suite:

```bash
mix test
```

Run legacy and cross-node HTTP integration against the Docker cluster:

```bash
./run-integration-tests.sh
```

Run the production frontend SDK → bridge → Python → FastAPI E2E:

```bash
npm --workspace @crystal-lattice/frontend-sdk run integration:bridge
```

See [Bridge service testing](docs/development/testing.md) for test ownership,
hosted variants, and the focused hardening boundary.

## Documentation

- [Bridge documentation index](docs/index.md)
- [Quickstart](docs/quickstart.md)
- [Protocol guide](docs/bridge-protocol.md)
- [Development architecture](docs/development/architecture.md)
- [Production deployment](PRODUCTION_DEPLOYMENT.md)

`BRIDGE_PLAN.md` is a legacy planning document and is not the current protocol
or architecture source of truth.

## License

Copyright (C) 2026 Dynamic Programming Solutions Kft.

This program is free software under the GNU Affero General Public License,
version 3 or, at your option, any later version. See the repository license
terms for details.