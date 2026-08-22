# Bridge connectivity product specification

## Purpose

The bridge lets a frontend reach a Crystal Lattice server that is not directly
addressable from the frontend's network. The bridge relays HTTP-shaped
application requests after an explicit user pairing flow. It does not interpret
the proxied application API.

The supported roles are:

- a local server that registers through a long-lived WebSocket control
  connection;
- a frontend that discovers and pairs with that server;
- one or more bridge nodes that coordinate discovery, pairing, sessions, and
  request routing;
- the local HTTP application behind the registered server.

## Server availability

A registered server has a stable `server_id` and current display metadata.
Available servers are discoverable through both frontend control transports.
Registration is cluster-visible, and disappearance of the active server
control connection removes the server from discovery.

The default duplicate-identity policy is takeover: a new control connection for
the same `server_id` becomes active and the previous connection is told that it
was superseded. Deployments may instead reject a duplicate registration.

## Pairing and later access

Pairing is deliberate and user-mediated:

1. The frontend selects an available server.
2. The bridge creates a six-digit code with a configured lifetime and attempt
   limit.
3. The code is shown only by the registered server.
4. The user enters the code in the frontend.
5. The bridge issues a signed pairing credential bound to the server and
   client identity.

The pairing credential represents durable logical authorization for its
configured lifetime. It is stateless at the bridge; active WebSocket session
identifiers are separate, ephemeral values.

A valid credential can:

- create a fresh legacy WebSocket session after reconnection; or
- validate HTTP access and current server availability without creating a
  frontend WebSocket session.

Invalid, expired, tampered, or server-mismatched credentials do not grant
access.

## Frontend transport modes

The frontend chooses one explicit bridge mode:

| Mode | Discovery and pairing | `GET /events` | Other proxied requests |
| --- | --- | --- | --- |
| `websocket` | Legacy WebSocket | Legacy WebSocket | Legacy WebSocket |
| `http` | HTTP v1 | HTTP v1 proxy | HTTP v1 proxy |
| `hybrid` | HTTP v1 | Legacy WebSocket | HTTP v1 proxy |

`websocket` is the compatibility default. A missing saved mode means
`websocket`.

Hybrid routing is exact. Only a `GET` whose path is `/events` or starts with
`/events?` uses the legacy path. Every control operation and every other
proxied request uses HTTP.

There is no automatic fallback between HTTP and WebSocket. A failed HTTP
request might already have reached the local application, so retrying it over
WebSocket could duplicate a non-idempotent operation. Rollback is an explicit
mode change applied to later requests.

## Payload behavior

The existing WebSocket path remains text-oriented:

- small request and response bodies are carried in the Phoenix message;
- large UTF-8 bodies use ordered application-level chunks;
- callers continue to receive the existing frontend `Transport` result.

The HTTP path uses raw HTTP bytes:

- request bodies move from frontend to bridge to server without JSON framing
  or base64 conversion;
- response bodies move from server to bridge to frontend as raw bytes;
- only request metadata, response status/headers, paths, and short-lived
  transfer credentials use the server WebSocket;
- JSON and text retain the normal frontend response behavior, while non-text
  responses are exposed as binary data.

## Availability and failure behavior

Transient bridge loss may be retried by reconnecting the server control
connection or by explicitly reconnecting the frontend transport. A server
restart does not require a new pairing while the signed credential remains
valid and the server returns with the same `server_id`.

Each proxied request has one terminal result. Timeouts, byte limits, invalid
credentials, peer loss, server loss, or protocol failure cancel remaining work
and release per-request state. If an HTTP response has already started, later
failure terminates the stream rather than fabricating a second HTTP response.

## Security posture

The pairing code is short-lived and attempt-limited. Durable pairing and
transfer credentials are signed and expire. The current pairing-only HTTP
baseline carries the pairing credential through `X-Crystal-Bridge-Token`,
leaving a caller's `Authorization` header available to the local application.
Planned deployment and external access credentials use distinct carriers
defined by the related access-control and connectivity requirements.

Hop-by-hop headers, bridge credentials, host, stale content length, and stale
content encoding are not forwarded across inappropriate boundaries.
Internet-facing deployments terminate TLS before the bridge origin.

## Compatibility and rollout

The legacy `BridgeTransport` and its wire messages remain supported and are not
internally rewritten to use the HTTP path. HTTP and hybrid modes are opt-in.

Changing the default requires separate approval after:

- the transfer-safety requirement is fully verified;
- bounded concurrent load/soak evidence is available;
- physical-device iOS and Android network checks pass;
- rollback to WebSocket remains available.

## Non-goals

- Choosing a route based on payload size or endpoint frequency.
- Automatic transport fallback or replay.
- Replacing the registered server's WebSocket control connection.
- Defining the application API carried through the bridge.
- Making HTTP or hybrid the permanent default in the current baseline.
