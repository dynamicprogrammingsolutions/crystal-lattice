# Bridge protocol guide

The bridge supports one registered-server control channel and two frontend
transport families. This page describes the current operator and integrator
contract.

## Roles and endpoints

| Role | Endpoint |
| --- | --- |
| Registered server | `/ws/websocket?type=server`, channel `server:<server_id>` |
| Legacy frontend | `/ws/websocket?type=app`, channel `app:<client_id>` |
| HTTP frontend | `/bridge/v1/*` |
| Health monitor | `GET /health` |

Phoenix messages use `topic`, `event`, `payload`, and `ref`. Clients must join
their channel with `phx_join` before sending bridge events. The legacy
frontend transport also uses Phoenix heartbeats.

## Registration and discovery

The server sends `register` with:

```json
{
  "server_id": "stable-id",
  "display_name": "My Crystal Lattice",
  "computer_name": "host.local",
  "location": "Office"
}
```

WebSocket frontends use `list_servers`. HTTP frontends use:

```text
GET /bridge/v1/servers
```

Both expose only public server metadata. Registration ownership, node, PID, and
connection timestamps remain internal.

## Pairing

WebSocket pairing uses `pair_request` followed by `pair_submit`. Success
returns a fresh ephemeral `session_id` and signed `pairing_token`.
`resume_session` verifies that token and returns another ephemeral session.

HTTP pairing uses:

```text
POST /bridge/v1/pairings/request
POST /bridge/v1/pairings/confirm
POST /bridge/v1/pairings/resume
```

The request route accepts `server_id` and `client_id` and returns an opaque
signed request handle. The six-digit code is delivered only to the registered
server. Confirmation accepts the handle and code and returns the signed
pairing token.

HTTP resume validates a pairing token from:

```text
X-Crystal-Bridge-Token: <token>
```

It confirms current server availability without creating a frontend
WebSocket session.

## Legacy WebSocket proxy

Small UTF-8 requests use `http_request`; large requests use
`http_request_init`, ordered `http_request_chunk`, and `http_request_end`.
The server replies with `http_response` or the corresponding chunked response
events.

The legacy path is text-oriented. It remains supported unchanged and is the
frontend compatibility default.

## HTTP proxy

An authenticated frontend sends any supported method to:

```text
/bridge/v1/proxy/<application-path-and-query>
```

with `X-Crystal-Bridge-Token`. A caller's `Authorization` header is preserved
for the local application.

The bridge sends `http_request_v2` metadata to the registered server. When a
request body is present, the server downloads it from the supplied
request-body path using its direction-scoped bearer token. The server sends
`http_response_v2_init`, then uploads raw response bytes to the supplied
response-body path.

No request or response body bytes are placed in v2 WebSocket messages. JSON,
text, and binary content all use the same raw byte path.

## Transfer endpoints

The paths supplied in `http_request_v2` have these forms:

```text
GET /bridge/v1/transfers/<request_id>/request-body
PUT /bridge/v1/transfers/<request_id>/response-body
```

They authenticate with `Authorization: Bearer <transfer-token>`. Credentials
are signed, short-lived, direction-scoped, and checked against the transfer's
request and server identity. One consumer/uploader may attach in each
direction.

## Common HTTP behavior

- Protocol capability: `GET /bridge/v1/capabilities`
- Common response cache policy: `Cache-Control: no-store`
- Error body: `{"error": "<reason>"}`
- Explicit empty request body:
  `X-Crystal-Bridge-Body-Present: 1`
- Frontend authentication is never forwarded to the local application.
- Hop-by-hop and stale framing/encoding headers are removed.

The origin negotiates gzip for eligible viewer responses. Brotli depends on
the selected deployment edge.

## Compatibility and rollback

HTTP clients check protocol version 1 before using the new routes. There is no
automatic HTTP-to-WebSocket fallback. A frontend rolls back by reconstructing
its connection in WebSocket mode.
