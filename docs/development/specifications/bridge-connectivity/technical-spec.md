# Bridge connectivity technical specification

## Architecture

The bridge carries two related transport families over one server control
connection:

```text
Frontend
├── legacy WebSocket ── AppChannel ── PubSub ── ServerChannel ── Python server
└── HTTP v1 proxy ───── HttpRouter ── HttpTransfer ──────────────┤
                                                                └── local HTTP app

Server control and metadata always use ServerChannel WebSocket messages.
HTTP v1 request and response bodies use bridge transfer endpoints.
```

The Elixir application supervises:

- Phoenix PubSub;
- legacy response-waiter tasks;
- temporary HTTP transfer coordinators;
- cluster formation;
- the server registry;
- pairing, persistent-pairing compatibility, and session managers;
- the Phoenix endpoint.

The HTTP router runs before `Plug.Parsers` so proxy and transfer routes can read
raw body bytes. The health router runs after JSON parsing.

## Python server integration configuration

The Python FastAPI startup lifecycle creates bridge and Bonjour integrations
only from an explicit process-local `ServerIntegrationRuntimeConfig`. The
normal CLI assembles this value from CLI arguments, project/profile data,
resolved application configuration, the effective server address, and
documented defaults. An absent bridge or Bonjour member means that integration
is disabled.

Ambient process variables do not activate or configure the Python bridge
client or Bonjour advertising. This prevents a tool-launched child server from
inheriting the parent server's bridge identity and superseding its connection.
Direct FastAPI embedders use the same explicit configuration API.

The Python bridge transport settings are configured under
`application.bridge`. They cover WebSocket maximum message size, HTTP transfer
timeout, legacy response chunk size and threshold, legacy request-body maximum,
and bridge debug output. Invalid types or non-positive limits are rejected
with a field-specific startup error. These settings are process-start
configuration; application reload does not restart network integrations.

## State and authority

### Active server records

Each bridge node maintains an ETS view of active servers. A local registration
adds:

- stable `server_id`;
- display name, computer name, and optional location;
- owning channel PID and node;
- connection timestamp.

Registration and unregistration are broadcast over `servers:registry`, so
every connected node converges on the current record. The owning node monitors
the channel PID and removes the record if it dies. Remote records contain the
remote PID, which remains a routable Erlang PID while the cluster is connected.

By default, a duplicate `server_id` replaces the old registration and sends it
`superseded`. With the reject policy, the new registration receives
`already_registered`.

### Pairing codes

Pending six-digit codes are ETS state on the node that created them, keyed by
`{server_id, client_id}`. A request records an expiration and failed-attempt
count and sends the code to the current server channel.

Legacy pairing remains on one app channel node. HTTP pairing returns a signed
opaque request handle containing the server, client, owner-node name, expiry,
and unique ID. Confirmation resolves the owner only from the current finite
cluster-node set and validates the code there with `:erpc`; it never creates an
atom from untrusted input.

If the owner node is unavailable, HTTP confirmation fails and the frontend
must request a new code.

### Pairing credentials

A durable pairing credential is a stateless HMAC-signed payload containing:

- format version and credential type;
- server ID and optional client ID;
- issued-at and expiration timestamps;
- unique credential ID.

All bridge nodes that accept the credential must share the signing secret and
salt. No bridge-side credential record is required.

### Legacy sessions

A successful legacy pairing or resume creates a fresh UUID session in the
`SessionManager` on the app channel's node. The session identifies server,
client, owning nodes, creation time, and last activity. Legacy requests update
activity; an inactivity cleanup removes expired sessions.

HTTP mode does not create a frontend bridge session. It verifies the pairing
credential and current server registration for each connection/resume or
proxy operation.

## Legacy WebSocket request path

The frontend joins `app:<client_id>`, obtains an ephemeral session, and submits
HTTP-shaped request metadata through the app channel.

For a small body, `http_request` contains the UTF-8 string body. For a large
body, the frontend sends:

1. `http_request_init`;
2. ordered `http_request_chunk` events;
3. `http_request_end`.

The app channel validates the session, resolves the active server, and sends
the corresponding event to that server PID. A supervised waiter subscribes to
`tunnel:request:<request_id>` before notifying the server, so one slow request
does not block later channel messages.

The Python server forwards the assembled request to its local HTTP application.
Small text responses use `http_response`. Large text responses use
`http_response_init`, ordered `http_response_chunk`, and `http_response_end`.
The bridge republishes those events to the waiting app channel, and the SDK
reassembles the response.

The legacy path is bounded by per-app pending waiter count and request timeout.
The Python adapter enforces its configured chunked-body size while
reassembling. It remains a text-oriented compatibility protocol.

## HTTP v1 request path

### Control

The HTTP frontend:

1. checks `/bridge/v1/capabilities`;
2. discovers through `/bridge/v1/servers`;
3. pairs through request and confirmation routes, or validates a saved
   credential through the resume route.

The SDK never opens a frontend WebSocket in HTTP mode.

### Proxy transfer

For each authenticated proxy request:

1. `HttpRouter` verifies the pairing credential and resolves the active server.
2. It creates a request ID, direction-scoped transfer credentials, and a
   temporary `HttpTransfer` coordinator.
3. It sends `http_request_v2` metadata to the server WebSocket.
4. If a body is present, the Python server attaches to the request-body
   endpoint and downloads raw chunks while forwarding them into the local HTTP
   request.
5. The Python server sends `http_response_v2_init` with status and filtered
   headers.
6. It attaches to the response-body endpoint and uploads the local response as
   raw chunks.
7. The coordinator relays those chunks to the waiting frontend HTTP response.

The server metadata frame contains no body bytes. The same flow is used for
small and large bodies.

### Transfer coordination

The coordinator subscribes to `http_transfer:<request_id>` before the server is
notified. Request download and response upload handlers attach through PubSub,
so they may reach different bridge nodes from the frontend request and server
channel.

Exactly one request consumer and one response uploader may attach. Transfer
credentials bind request ID, server ID, direction, and expiry. The coordinator
also checks those claims against its state.

Chunk flow is demand/acknowledgement based:

- the request consumer attaches, then the coordinator demands one frontend
  chunk;
- the next request chunk is not demanded until the consumer acknowledges the
  previous one;
- response upload is not demanded until response metadata is available and the
  frontend chunked response is ready;
- the uploader receives the next demand only after the frontend acknowledges
  the previous response chunk.

This bounds in-flight chunk data while preserving raw bytes across nodes.

### Terminal behavior

The coordinator monitors the frontend process, registered server PID, request
consumer, and response uploader. It has one overall timeout and byte counters
for each direction.

Normal completion acknowledges the final response upload and terminates the
temporary coordinator. Failure sends the frontend an HTTP error when possible,
notifies attached peers, sends `http_request_v2_cancel` when server work may
still be running, and terminates.

The Python adapter tracks each v2 request by request ID. A repeated request ID
cancels the earlier task. Explicit cancel, WebSocket disconnect, server
supersession, or shutdown cancels tracked work.

The transfer DynamicSupervisor applies the configured limit through
`max_children`, making concurrent admission atomic. Transfer start translates
the supervisor's saturation result to the stable `too_many_transfers` outcome
used by the HTTP router's `429` response.

## Header and encoding boundaries

The frontend bridge token is consumed by the bridge and never forwarded. A
caller's `Authorization` header remains an application header.

The bridge removes request hop-by-hop headers, host, bridge control headers,
content length, and transfer encoding before sending metadata to the Python
server. The Python adapter additionally removes `Accept-Encoding` and requests
`identity` from the local application so viewer compression is applied once.

Local response `content-length`, `content-encoding`, transfer encoding, and
hop-by-hop headers are removed before the bridge starts its streamed frontend
response.

## Connection recovery

The Python server reconnects its control WebSocket after transient closure,
rejoins, and registers the same configured `server_id`. Takeover makes one
connection the active target.

The legacy frontend monitors Phoenix heartbeats. It can validate a suspect
socket, reconnect, and create a fresh ephemeral session from the pairing
credential. HTTP mode validates the credential and server availability on
connect or after `prepareForResume`. Hybrid applies both lifecycles.

The frontend does not replay a failed request through another transport.

## Verification boundaries

- Elixir unit tests own registries, pairing state, sessions, route
  authentication, coordinator transitions, token scope, and deployment
  configuration.
- Python unit tests own local forwarding, byte streaming, filtering, task
  tracking, and cancellation.
- SDK unit tests own mode selection, exact routing, parsing, timeout, and
  no-fallback behavior.
- One real SDK-to-bridge-to-Python E2E owns cross-runtime parity.
- One HAProxy cluster E2E owns no-affinity behavior.
- One secure hosted edge owns real TLS/HTTP2 and edge configuration evidence.
- Native tests own mobile mode selection and rollback, not protocol payload
  duplication.
