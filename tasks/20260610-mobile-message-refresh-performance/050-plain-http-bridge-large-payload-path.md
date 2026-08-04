# Plain HTTP Bridge Large Payload Path

Add opt-in HTTP-only and hybrid bridge transports while preserving the existing WebSocket bridge transport as the stable default. In hybrid mode, only event polling uses the existing WebSocket request path; all other frontend bridge control and backend API requests use HTTP.

## Requirements checklist

- [ ] Keep the existing `BridgeTransport`, its WebSocket wire messages, and its pairing/control/event/normal-request behavior fully intact and make WebSocket-only mode the default.
- [ ] Expose explicit frontend bridge modes for WebSocket-only, HTTP-only, and hybrid operation without automatic request fallback between modes.
- [ ] In hybrid mode, route only `GET /events` (with or without a query string) through the existing `BridgeTransport`; route discovery, pairing, resume/validation, and every other proxied backend request through HTTP.
- [ ] Make HTTP-only mode complete: it must discover servers, pair, validate a saved pairing token, and proxy all backend requests—including `/events`—without opening a frontend WebSocket.
- [ ] Preserve the existing SDK `Transport.request()` contract and the SDK-facing status/data/error behavior for JSON and text endpoints across all three modes.
- [ ] Keep small control metadata on the Python server WebSocket, but transfer every request/response body selected for the new HTTP path as raw HTTP bytes, including a Python-to-bridge HTTP response upload path.
- [ ] Support binary request and response bodies on the HTTP path without JSON text framing or base64 conversion.
- [ ] Bound, authenticate, time out, cancel, and clean up HTTP transfers safely across single-node and clustered bridge deployments.
- [ ] Enable negotiated gzip for HTTP bridge responses, retain HTTP/2 at supported TLS edges, and allow Brotli at deployment edges that support it; do not require Brotli from the Phoenix origin.
- [ ] Wire the mobile frontend through an opt-in mode factory so old saved connections remain WebSocket-only unless explicitly configured otherwise, and leave the permanent default switch out of this task.
- [ ] Add unit, integration, clustered, and SDK-facing E2E evidence for all modes, path routing, large JSON, raw binary, compression, timeout/cancellation cleanup, and unchanged legacy WebSocket behavior.

Parent Task: tasks/20260610-mobile-message-refresh-performance/000-main.md

Depends On: tasks/20260610-mobile-message-refresh-performance/010-bridge-concurrent-proxied-requests.md

## User-approved scope clarification

- The new HTTP path is opt-in. Shipping this task must not switch existing or new frontends away from the stable WebSocket-only default.
- The frontend must be able to select WebSocket-only, HTTP-only, or hybrid mode explicitly.
- There is no size-based or read-heavy-path heuristic in the first version. In hybrid mode, the routing rule is deterministic: only event polling uses the legacy proxied WebSocket path and all other backend requests use HTTP.
- “Only events use the old path” applies to proxied backend requests. A hybrid transport still opens the legacy WebSocket and uses its join, resume, and heartbeat control frames so it can issue `/events` requests.
- Do not silently fall back from HTTP to WebSocket. Automatic fallback could duplicate non-idempotent writes and would hide HTTP-path defects during rollout. Switching mode is the explicit rollback mechanism.

## Background

This is a later-stage transport improvement. It should follow the immediate bridge head-of-line blocking fix, because concurrency correctness matters even before large-payload transfer optimization.

The concurrency prerequisite is complete. Current bridge transport still uses Phoenix channel messages for HTTP proxying. That works, but large payloads pay extra costs:

- payloads are serialized into JSON text frames;
- large responses must be chunked and reassembled in app code;
- normal HTTP compression and HTTP/2 behavior are not available for the tunneled payload body;
- binary payloads tend to require text-safe encodings such as base64.

## Current-state findings

- `packages/frontend-sdk/src/transport/bridgeTransport.ts` owns WebSocket connection, pairing, resume, heartbeat, request chunking, and response reassembly. Preserve this file and its public behavior rather than adding HTTP branches to it.
- The shared `Transport` surface is only `request(...) -> {status, data}`. `RestAgentBackend` polls events with ordinary `GET /events` calls, so a wrapper can route events without changing backend/controller APIs.
- `Bridge.PairingToken` already issues stateless signed tokens containing the target `server_id`; the HTTP path can authenticate requests from that token without relying on node-local ephemeral `SessionManager` state.
- `Bridge.Router` currently exposes only `/health`, and `Bridge.Endpoint` runs `Plug.Parsers` before the router. Raw proxy and transfer routes must be dispatched before JSON body parsing consumes their bytes.
- The completed concurrency task made `Bridge.AppChannel` waits asynchronous and made the Python bridge client execute legacy proxied requests concurrently. Those legacy handlers and messages remain the regression baseline.
- The Python `BridgeClient` currently converts local responses to `.text` and sends `http_response*` WebSocket messages. The new byte-streaming flow needs separate versioned handlers so this legacy path remains unchanged.
- `Bridge.ServerRegistry` distributes active server PIDs through PubSub. New transfer peers may land on different load-balanced bridge nodes, so transfer coordination cannot assume sticky sessions or node-local HTTP requests.
- Plug/Cowboy already supports negotiated streaming gzip via its compression stream handler. The secure CloudFront deployments advertise HTTP/2 but currently set `Compress: false`; the local HAProxy configs do not provide Brotli.
- The adjacent metadata/event and refresh-orchestration subtasks own event contents and refresh behavior. This task only chooses the transport used for the existing `/events` HTTP contract.

## Resolved design

### Frontend mode contract

Add new SDK types alongside, not inside, the existing transport:

| Mode | Bridge control operations | `/events` backend requests | Other backend requests |
| --- | --- | --- | --- |
| `websocket` | Existing WebSocket path | Existing WebSocket path | Existing WebSocket path |
| `http` | New HTTP API | New HTTP proxy | New HTTP proxy |
| `hybrid` | New HTTP API | Existing `BridgeTransport` | New HTTP proxy |

- Add a structural bridge-connection interface for the existing lifecycle/pairing methods and a factory accepting an explicit mode.
- Add `HttpBridgeTransport` for HTTP control and proxying.
- Add `HybridBridgeTransport` that owns an `HttpBridgeTransport` and lazily creates an unmodified `BridgeTransport` with the same `serverId` and pairing token for event polling.
- Match the legacy event path only when the method is `GET` and the path is exactly `/events` or begins `/events?`.
- Keep the factory default at `websocket`. An absent mode on a persisted mobile bridge record resolves to that default.
- Do not retry an HTTP-routed request over WebSocket. Callers may reconstruct the connection in `websocket` mode to roll back.

### Public HTTP bridge API

Add a versioned, no-store HTTP API, dispatched before the general JSON parser:

- `GET /bridge/v1/capabilities`: advertise protocol version and HTTP transfer support so an opt-in client fails clearly against an older bridge.
- `GET /bridge/v1/servers`: HTTP equivalent of `list_servers`.
- `POST /bridge/v1/pairings/request`: create a pairing request from `server_id` and `client_id`, then return an opaque, signed pairing-request handle bound to the owner node and expiry (never the six-digit code).
- `POST /bridge/v1/pairings/confirm`: accept that handle and the user-entered code, validate on the node that owns the pending pairing, and return the existing signed pairing token.
- `POST /bridge/v1/pairings/resume`: validate a saved token, optional expected `server_id`, and current server availability without creating a frontend WebSocket session.
- `MATCH /bridge/v1/proxy/*path`: authenticate the pairing token, derive the target server from its claims, preserve the proxied path/query/method, and start one versioned HTTP transfer.
- `GET /bridge/v1/transfers/:request_id/request-body` and `PUT /bridge/v1/transfers/:request_id/response-body`: one-time, direction-scoped endpoints used only by the Python bridge client.

Use a dedicated `X-Crystal-Bridge-Token` header for frontend pairing authentication so a caller-supplied `Authorization` header can still be forwarded to the local backend. Transfer endpoints use short-lived bearer tokens sent only over the authenticated server WebSocket. Strip hop-by-hop, bridge-authentication, host, transfer-encoding, and stale content-length headers at each boundary.

`HttpBridgeTransport` accepts the existing WebSocket-shaped bridge URL for drop-in configuration, derives the HTTP origin by converting `ws`/`wss` to `http`/`https` and removing `/ws` or `/ws/websocket`, and accepts an explicit HTTP-base override for nonstandard deployments.

HTTP pairing must not depend on load-balancer affinity. The signed pairing-request handle identifies an already-known cluster node without creating atoms from untrusted input; a confirm request received elsewhere dispatches validation to that node. If the owner node disappears, confirmation fails explicitly and the frontend requests a new code. This leaves the legacy channel-local pairing flow unchanged.

### Body transfer and coordination

All requests selected for HTTP use the versioned transfer flow, regardless of body size:

1. The frontend opens the HTTP proxy request. The bridge authenticates the pairing token, starts a bounded transfer coordinator, subscribes it before notifying the server, and keeps the frontend HTTP request open.
2. The bridge sends a new `http_request_v2` control event to the registered Python server. It contains only request metadata plus short-lived, signed request-download and response-upload credentials; it never embeds body bytes.
3. When a request has a body, the Python client downloads it from the transfer endpoint and streams it into the local FastAPI request. The frontend request handler and Python download handler relay raw chunks through the coordinator with per-chunk acknowledgement/backpressure.
4. The Python client opens the local response as a byte stream, sends `http_response_v2_init` with status and filtered headers over the server WebSocket, and streams the raw response bytes to the bridge with HTTP `PUT`.
5. The coordinator forwards uploaded chunks to the waiting frontend HTTP response with backpressure. The frontend SDK parses JSON/text as today and returns raw `ArrayBuffer` data for non-text content types.
6. Completion, timeout, disconnect, over-limit, or protocol error closes all peers, invalidates the one-time transfer directions, and sends `http_request_v2_cancel` to the Python client when work may still be running.

Use a supervised per-request coordinator and the existing clustered PubSub for peer attachment so the frontend request, server WebSocket, body download, and response upload may terminate on different bridge nodes. Payloads crossing bridge nodes remain Erlang binaries rather than JSON/base64 text. Enforce active-transfer count, request/response byte limits, one consumer/uploader per direction, transfer expiry, sequence/order, server identity, and a single terminal result.

The Python client keeps the legacy `http_request*` handlers unchanged and adds separately tracked v2 tasks. It must stream bytes with `httpx` iterators rather than `.text`, force identity encoding on the local hop so the bridge owns viewer compression, serialize only the small WebSocket metadata frame, and cancel v2 tasks during disconnect, supersession, stop, or an explicit cancel event.

### Compression and deployment behavior

- Enable Cowboy response compression with a documented threshold. This supplies gzip for both full and chunked HTTP responses when the client advertises it.
- Remove stale upstream `content-length`/`content-encoding` values before the bridge emits a streamed response.
- Enable CloudFront compression on secure bridge distributions so supported viewer/response combinations can use gzip or Brotli; keep caching disabled for control/proxy/transfer paths.
- Forward the custom frontend bridge-token header, transfer authorization, query strings, and all supported methods through CloudFront/HAProxy while preventing those credentials from being cached or logged.
- Retain the existing CloudFront HTTP/2 setting and advertise `h2,http/1.1` on the TLS HAProxy listener. Plain local HTTP remains HTTP/1.1 unless the selected edge supports h2/h2c.
- Do not add an in-process Brotli dependency to Phoenix in this task. Document Brotli as edge-dependent and gzip as the portable guaranteed compression.

### Mobile rollout

- Add an optional bridge transport-mode override to the saved bridge connection shape and centralize construction in one mode-aware factory.
- Treat old records and records without an override as `websocket`.
- Expose HTTP and hybrid as experimental opt-ins in the bridge connection flow; persist an explicit override only when selected.
- Reuse the same pairing token when changing modes. Generalize foreground resume/disconnect handling to the structural bridge interface rather than `instanceof BridgeTransport`.
- Keep the application-wide default `websocket`. Changing that default or migrating existing records permanently is a separate, explicitly approved rollout after the HTTP/hybrid test matrix and real-device checks pass.

## Scope boundaries

- Do not change `BridgeTransport` internals or remove any legacy WebSocket messages, chunking, pairing, resume, heartbeat, or recovery behavior.
- Do not add size-based automatic routing or transparent fallback.
- Do not change `/events` semantics, event payloads, polling cadence, metadata invalidation, or message refresh orchestration.
- Do not replace the Python server WebSocket registration/control connection; only large/body data moves to HTTP.
- Do not add a new binary application feature. A deterministic byte fixture may be added to the existing integration test-control surface solely to verify the transport boundary.
- Do not make hybrid or HTTP mode the default as part of this task.

## Execution plan

Status: Approved

Use staged checkpoints because this change crosses public SDK configuration, bridge authentication/routing, clustered stream coordination, Python networking, mobile connection persistence, and deployment edges. Preserve a runnable legacy baseline at every checkpoint.

### Requirement verification

- **Legacy stability and explicit modes:** keep all existing `BridgeTransport` unit tests unchanged, rerun the complete existing bridge E2E suite in WebSocket-only mode, and add SDK factory/routing tests proving that mode selection is explicit and has no fallback.
- **HTTP control and authentication:** add Plug-level route tests for capabilities, discovery, pairing, resume, token/server mismatch, expired/invalid tokens, header filtering, CORS/preflight where applicable, and old-bridge capability failure from the SDK.
- **Hybrid routing:** use recording fetch/WebSocket adapters in SDK tests to prove only `GET /events` reaches `BridgeTransport`; in a real SDK-facing E2E, spy on production adapter calls while `RestAgentBackend` performs an event poll and normal API calls.
- **HTTP-only operation:** run discovery, pairing, token resume, `/api/hello`, `/events`, and a normal write through `HttpBridgeTransport` while a WebSocket factory that throws verifies that the frontend never opens a socket.
- **Large JSON and SDK parity:** request the same multi-megabyte response through WebSocket-only and HTTP modes using `RestAgentBackend`, then compare the parsed SDK-visible result and status.
- **Raw binary and streaming:** add byte-for-byte request/response tests across the Elixir coordinator and Python v2 client, plus a real E2E using a deterministic binary fixture. Assert that v2 WebSocket frames contain metadata/URLs only and no body/chunk/base64 fields.
- **Backpressure, limits, and cleanup:** add bridge/Python tests for slow consumers, out-of-order or duplicate attachment, request/response limits, timeout before and after response headers, frontend abort, response-upload failure, server WebSocket loss, supersession, and late one-time-token reuse. Assert no coordinator/task remains registered afterward.
- **Cluster behavior:** run HTTP pairing request/confirm and the v2 data path through the multi-node HAProxy Docker deployment with pairing, request, control, and upload legs landing on different nodes; verify successful token issuance, transfer, and cleanup without sticky sessions.
- **Compression and edge behavior:** use a raw HTTP client with `Accept-Encoding: gzip` to verify compressed wire bytes and successful decompression of a large response. Add configuration tests for CloudFront compression/HTTP2 and HAProxy ALPN. Treat a hosted Brotli/HTTP2 smoke test as deployment evidence when credentials are available, not as a prerequisite for local unit collection.
- **Mobile opt-in and migration:** add mobile tests for absent-mode migration to WebSocket, explicit HTTP/hybrid selection, saved-mode reconstruction, pairing-token reuse, foreground resume, and rollback to WebSocket. Perform a human real-device/simulator smoke check in all three modes before considering a later default switch.

Planned verification commands include:

- `cd bridge-elixir && mix test`
- `cd bridge-elixir && ./run-integration-tests.sh` for the clustered Docker boundary
- `pytest application/python/tests/test_bridge_client_chunked_http.py application/python/tests/test_bridge_client_local_request.py application/python/tests/test_bridge_client_http_transfer.py -q`
- `npm --workspace @crystal-lattice/frontend-sdk test`
- `npm --workspace @crystal-lattice/frontend-sdk run integration:bridge`
- the focused mobile Jest command for the new connection-mode tests, followed by the package’s normal `npm test`

### Documentation

- Update the frontend SDK README/API exports with the three modes, exact hybrid event matcher, URL derivation/override, binary response behavior, timeout behavior, and explicit no-fallback rule.
- Update bridge protocol and deployment documentation with the HTTP v1 endpoints, authentication headers, v2 control frames, transfer lifecycle, limits, gzip behavior, edge-dependent Brotli, HTTP/2 expectations, and rollback instructions.
- Update the terminal application bridge documentation and CLI/environment reference for an optional bridge HTTP-base override and transfer-related limits.
- Update the frontend integration-test guide with the WebSocket, HTTP-only, hybrid, cluster, compression, and optional hosted-edge commands.
- Document the mobile mode as experimental, WebSocket as the compatibility default, and the verification gate required before changing that default.

### Risks and mitigations

- **Duplicate non-idempotent writes:** never auto-fallback after an HTTP request starts; mode changes apply only to later requests.
- **Cross-node stream stalls:** subscribe/register the coordinator before server notification, use explicit attach/ack messages and monitors, and test through round-robin HAProxy.
- **Unbounded memory/mailboxes:** stream with demand/backpressure, enforce byte/concurrency limits, and never assemble v2 bodies in Elixir or Python.
- **Response already started when failure occurs:** return a structured HTTP error before headers; after headers, terminate the stream and surface a network/parse error rather than fabricating a second response.
- **Compression/header corruption:** force identity on the local Python hop, strip stale length/encoding headers, and let the viewer-facing bridge/edge negotiate encoding once.
- **React Native fetch differences:** keep JSON/text behavior identical, isolate raw-binary handling, and require iOS/Android smoke evidence before a default change.
- **Protocol drift:** version endpoints/control events, leave all legacy clauses in place, and document capability negotiation.

### Task checklist

- [x] After explicit user approval, change this plan status to `Approved` before implementation.
- [ ] Capture the passing legacy WebSocket unit/E2E baseline and preserve existing `BridgeTransport` source and wire messages.
- [ ] Add shared bridge mode/lifecycle types, URL derivation, and an explicit mode factory without changing `BridgeTransport`.
- [ ] Add `HttpBridgeTransport` control, pairing-token validation, proxy, timeout/abort, JSON/text, and raw-binary behavior.
- [ ] Add `HybridBridgeTransport` with exact event-only legacy routing and no automatic fallback.
- [ ] Add versioned capabilities, discovery, pairing, resume, proxy, and transfer HTTP routes before body parsing.
- [ ] Add dedicated frontend pairing authentication and short-lived signed transfer credentials.
- [ ] Add the supervised, bounded, cluster-aware transfer coordinator and raw chunk backpressure protocol.
- [ ] Add server-channel v2 request, response-init, and cancel metadata events while preserving legacy handlers.
- [ ] Add Python v2 request-body download, local byte streaming, response upload, task tracking, cancellation, and HTTP-base override.
- [ ] Add gzip origin configuration and update CloudFront/HAProxy edge settings without changing WebSocket compression behavior.
- [ ] Add SDK unit tests for all modes, exact routing, token/errors, timeout/abort, parity, binary bodies, and no fallback.
- [ ] Add Elixir route/coordinator/security/cleanup/compression tests.
- [ ] Add Python byte-streaming, metadata-only WebSocket, cancellation, and legacy-regression tests.
- [ ] Extend SDK-facing bridge E2E for HTTP-only, hybrid, large JSON, binary, compression, resume, and failure cleanup.
- [ ] Add and run a multi-node HAProxy transfer E2E that crosses bridge nodes.
- [ ] Add mobile opt-in mode persistence/factory wiring and migration/rollback tests while retaining the WebSocket default.
- [ ] Update SDK, bridge protocol/deployment, terminal bridge, mobile rollout, and integration-test documentation.
- [ ] Run the planned verification matrix, record blocked hosted/manual evidence separately, and leave the permanent default switch deferred.