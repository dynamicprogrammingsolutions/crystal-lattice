# Bridge service documentation

The Bridge service lets remote Crystal Lattice frontends discover and pair
with registered local servers, then relay HTTP-shaped application requests
without requiring the server to be publicly addressable.

Start here:

- [Quickstart](quickstart.md)
- [Bridge protocol guide](bridge-protocol.md)
- [Production deployment](../PRODUCTION_DEPLOYMENT.md)

Maintainer documentation:

- [Development index](development/index.md)
- [Architecture](development/architecture.md)
- [Testing](development/testing.md)

## Supported connection paths

The registered server always maintains a Phoenix WebSocket control connection.
A frontend can use:

- WebSocket-only mode for discovery, pairing, events, and proxied requests;
- HTTP-only mode for all frontend control and proxy operations;
- hybrid mode, where only exact `GET /events` requests use the legacy
  frontend WebSocket path.

WebSocket remains the compatibility default. HTTP and hybrid are explicit
frontend choices.
