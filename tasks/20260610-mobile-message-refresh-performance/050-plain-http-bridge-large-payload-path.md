# Plain HTTP Bridge Large Payload Path

Add opt-in HTTP-only and hybrid bridge transports while preserving the existing WebSocket bridge transport as the stable default. In hybrid mode, only event polling uses the existing WebSocket request path; all other frontend bridge control and backend API requests use HTTP.

## Requirements checklist

- [x] Keep the existing `BridgeTransport`, its WebSocket wire messages, and its pairing/control/event/normal-request behavior fully intact and make WebSocket-only mode the default.
- [x] Expose explicit frontend bridge modes for WebSocket-only, HTTP-only, and hybrid operation without automatic request fallback between modes.
- [x] In hybrid mode, route only `GET /events` (with or without a query string) through the existing `BridgeTransport`; route discovery, pairing, resume/validation, and every other proxied backend request through HTTP.
- [x] Make HTTP-only mode complete: it must discover servers, pair, validate a saved pairing token, and proxy all backend requests—including `/events`—without opening a frontend WebSocket.
- [x] Preserve the existing SDK `Transport.request()` contract and the SDK-facing status/data/error behavior for JSON and text endpoints across all three modes.
- [x] Keep small control metadata on the Python server WebSocket, but transfer every request/response body selected for the new HTTP path as raw HTTP bytes, including a Python-to-bridge HTTP response upload path.
- [x] Support binary request and response bodies on the HTTP path without JSON text framing or base64 conversion.
- [ ] Bound, authenticate, time out, cancel, and clean up HTTP transfers safely across single-node and clustered bridge deployments.
- [x] Enable negotiated gzip for HTTP bridge responses, retain HTTP/2 at supported TLS edges, and allow Brotli at deployment edges that support it; do not require Brotli from the Phoenix origin.
- [x] Wire the mobile frontend through an opt-in mode factory so old saved connections remain WebSocket-only unless explicitly configured otherwise, and leave the permanent default switch out of this task.
- [x] Add unit, integration, clustered, and SDK-facing E2E evidence for all modes, path routing, large JSON, raw binary, compression, timeout/cancellation cleanup, and unchanged legacy WebSocket behavior.
- [ ] A formal cross-package bridge-connectivity specification and package-owned current documentation accurately cover the existing bridge subsystem, the HTTP/hybrid extension, directly connected frontend/server/deployment responsibilities, live requirements and evidence, and explicit exclusions without reconstructing clearly separate systems.

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
- [x] Capture the passing legacy WebSocket unit/E2E baseline and preserve existing `BridgeTransport` source and wire messages.
- [x] Add shared bridge mode/lifecycle types, URL derivation, and an explicit mode factory without changing `BridgeTransport`.
- [x] Add `HttpBridgeTransport` control, pairing-token validation, proxy, timeout/abort, JSON/text, and raw-binary behavior.
- [x] Add `HybridBridgeTransport` with exact event-only legacy routing and no automatic fallback.
- [x] Add versioned capabilities, discovery, pairing, resume, proxy, and transfer HTTP routes before body parsing.
- [x] Add dedicated frontend pairing authentication and short-lived signed transfer credentials.
- [x] Add the supervised, bounded, cluster-aware transfer coordinator and raw chunk backpressure protocol.
- [x] Add server-channel v2 request, response-init, and cancel metadata events while preserving legacy handlers.
- [x] Add Python v2 request-body download, local byte streaming, response upload, task tracking, cancellation, and HTTP-base override.
- [x] Add gzip origin configuration and update CloudFront/HAProxy edge settings without changing WebSocket compression behavior.
- [x] Add SDK unit tests for all modes, exact routing, token/errors, timeout/abort, parity, binary bodies, and no fallback.
- [x] Add Elixir route/coordinator/security/cleanup/compression tests.
- [x] Add Python byte-streaming, metadata-only WebSocket, cancellation, and legacy-regression tests.
- [x] Extend SDK-facing bridge E2E for HTTP-only, hybrid, large JSON, binary, compression, resume, and failure cleanup.
- [x] Add and run a multi-node HAProxy transfer E2E that crosses bridge nodes.
- [x] Add mobile opt-in mode persistence/factory wiring and migration/rollback tests while retaining the WebSocket default.
- [x] Update SDK, bridge protocol/deployment, terminal bridge, mobile rollout, and integration-test documentation.
- [x] Run the planned verification matrix, record blocked hosted/manual evidence separately, and leave the permanent default switch deferred.

## Implementation Notes

Added during implementation.

- The implementation is isolated on
  `task/20260610-plain-http-bridge-large-payload-path` in the dedicated
  worktree. The existing `BridgeTransport` source was not modified.
- HTTP pairing uses an opaque signed request handle that binds the server,
  client, owner node, and expiry. Transfer credentials bind request id, server,
  direction, and expiry. The frontend pairing token uses
  `X-Crystal-Bridge-Token`, leaving a proxied `Authorization` header intact.
- A supervised per-request Elixir coordinator relays request-download and
  response-upload chunks with acknowledgements, byte/concurrency limits,
  monitors, timeout cancellation, and clustered PubSub attachment.
- The Python bridge client handles v2 work in separately tracked tasks,
  downloads request bodies, streams local HTTP with identity encoding, sends
  only response metadata over WebSocket, and uploads raw response bytes.
- The first real E2E exposed gzip on the internal request-body download.
  Marking that internal response `Content-Encoding: identity` fixed the issue
  while retaining negotiated gzip on frontend-facing proxy responses.
- Post-merge local verification completed before the implementation commit:
  - `mix test`: 52 tests passed, 4 existing skips.
  - Python bridge and CLI environment suites: 50 passed with the worktree
    explicitly first on `PYTHONPATH`.
  - Frontend SDK default suite: 310 passed.
  - Mobile Jest suite: 115 passed.
  - Mobile TypeScript: passed.
  - Local external-mode bridge E2E: 4 applicable tests passed, including
    legacy large payload/concurrency, HTTP-only large JSON/binary/gzip/resume,
    and hybrid event-only WebSocket routing.
- Deferred verification:
  - Physical-device iOS/Android network checks remain a rollout gate before
    changing the compatibility default. Simulator checks are complete.
  - `test_cli_environment_isolation.py` is included in the 50-test Python
    result above.
- Follow-up verification completed after commit `61140c0e`:
  - The two-node Docker/HAProxy runner passed all three legacy registration,
    discovery, and pairing cases.
  - A new bridge-owned cluster E2E passed HTTP pairing and a 1.2 MB raw request
    plus 900 KB raw response. It asserts from HAProxy logs that the proxy,
    request-body download, and response-body upload for one transfer span
    `bridge-node-1` and `bridge-node-2`.
  - The SDK E2E passed all five cases in self-managed Docker mode, including
    unchanged legacy large bodies, HTTP-only JSON/binary/gzip/resume/events,
    hybrid event-only WebSocket routing, bridge restart/recovery, and legacy
    concurrency.
  - A fresh bridge image was built with the AWS CLI/CodeBuild path. The secure
    EC2 + CloudFront SDK E2E passed all five cases, then removed its origin and
    edge stacks. Only the pre-existing builder stack remains.
  - The hosted CloudFront edge independently negotiated HTTP/2 for `/health`.
    Its live AWS configuration reported HTTP/2, compression enabled, zero
    default TTL, all supported methods, and forwarding for both custom bridge
    headers plus `Authorization`.
  - iOS and Android Detox release/E2E builds passed. A focused production-UI
    test passed on the iPhone 17 Pro simulator and Medium Phone API 36.1
    emulator, proving WebSocket default selection and explicit HTTP, hybrid,
    and WebSocket rollback selection.
  - The Docker SDK harness now bounds each startup health probe so a published
    port that precedes Cowboy readiness cannot hang the test indefinitely.
    External mode explicitly skips the self-managed restart case.
- Coverage hardening remains proposed rather than claimed complete for the
  broad transfer-safety requirement: independently assert request-size and
  active-transfer bounds, peer disconnect cleanup, token/server mismatch,
  old-bridge capability failure, and saved mobile mode/token reconstruction.

## Follow-up execution plan — Bridge specification and documentation backfill

Status: Approved

This plan was explicitly approved after the initial implementation and
verification commits. It is a bounded backfill of the bridge-connectivity
subsystem, not documentation of only the new HTTP mechanism and not a
repository-wide reconstruction.

### Outcome and ownership

Create one cross-package target specification at
`docs/development/specifications/bridge-connectivity/`. Cross-package ownership
is required because the supported subsystem coordinates independently owned
Elixir bridge, frontend SDK, Python server adapter, mobile host, and deployment
edge behavior. Package documentation remains with each implementation owner.

The formal specification covers:

- bridge roles and end-to-end topology from frontend/app client through the
  bridge and registered Python server to the local HTTP application;
- server registration, cluster-visible discovery, identities, health,
  pairing, durable credentials, resume, heartbeat, disconnect, takeover, and
  recovery;
- the existing WebSocket-only frontend path, legacy request/response and
  chunking behavior, and its compatibility role;
- explicit WebSocket, HTTP, and hybrid modes, exact event routing, and the
  prohibition on automatic fallback;
- the continuing Python server control WebSocket, HTTP v1 control/proxy API,
  and v2 server control messages;
- raw request download and response upload, backpressure, limits, timeout,
  cancellation, cleanup, credentials, and header filtering;
- single-node and clustered routing through PubSub and HAProxy without
  affinity;
- gzip, edge-dependent Brotli, HTTP/2, TLS termination, no-store behavior, and
  deployment constraints;
- SDK behavior, mobile persistence/migration/rollback, verification
  boundaries, and gates before changing the default.

### Bounded discovery and exclusions

Derive claims from the directly connected current implementation, tests, and
deployment definitions:

- `bridge-elixir/lib/bridge/endpoint.ex`, socket/channels, registries, pairing
  and session managers, pairing tokens, HTTP router/transfer/token modules,
  configuration, Docker/HAProxy, and AWS edge definitions;
- frontend SDK bridge transports, connection records, and bridge integration
  harness/tests;
- `application/python/agent_terminal_app/bridge_client.py` plus its lifecycle
  wiring, CLI/environment configuration, and focused tests;
- mobile bridge connection selection, saved records, lifecycle hosting, and
  focused tests.

Do not discover or document proxied application endpoint semantics, event
payload/cadence or refresh orchestration, agent/provider/plugin/tool behavior,
cloud orchestrator connectivity, direct HTTP/Bonjour beyond a brief connection
method distinction, unrelated mobile UI, unwired desktop behavior, abandoned
design history, or deployment internals unrelated to bridge connectivity.
Label uncertainty rather than inferring unsupported behavior.

### Specification structure and live requirements

Create:

- `index.md` for scope, ownership, relationships, artifacts, current owners,
  and exclusions;
- `product-spec.md` for supported workflows, explicit modes, compatibility,
  rollout, and non-goals;
- `technical-spec.md` for architecture, state/lifecycles, routing,
  clustering, failure behavior, security, and verification boundaries;
- `protocol.md` for the legacy Phoenix channel contract, HTTP v1 API, v2
  server control events, headers, credentials, body lifecycle, and
  compatibility;
- `deployment-and-operations.md` for supported topology and edge/operations
  constraints without duplicating command-oriented deployment guides;
- `frontend-behavior.md` for SDK mode selection, routing, persistence,
  lifecycle hosting, and rollback;
- `requirements.md` with stable `BRG-*` IDs and separate implementation,
  verification, documentation, and evidence state.

Initial requirements:

- `BRG-001`: While a server is registered through its bridge control
  connection, the bridge maintains one cluster-visible server record keyed by
  its stable `server_id` and containing supported display metadata. Every
  bridge node exposes that record through supported discovery interfaces, the
  record is removed when registration ends, and health retains the established
  status, node, cluster-size, active-server, and active-session fields.
- `BRG-002`: A frontend can pair with an available server by completing the
  time-bounded code-verification flow and receiving a signed pairing credential
  bound to server and client identity. While valid and the server is available,
  the frontend can re-establish or validate access without another code through
  either supported control transport. Invalid, expired, tampered, or
  server-mismatched credentials do not grant access.
- `BRG-003`: legacy WebSocket proxying, chunking, concurrency, and
  compatibility;
- `BRG-004`: explicit frontend modes;
- `BRG-005`: exact hybrid event routing and no automatic fallback;
- `BRG-006`: HTTP control/proxy API and v2 server control protocol;
- `BRG-007`: raw streaming, binary behavior, and SDK response parity;
- `BRG-008`: authentication, credential scope, header isolation, and replay
  protection;
- `BRG-009`: backpressure, atomic bounds, timeout, cancellation, and cleanup;
- `BRG-010`: clustered operation without affinity;
- `BRG-011`: disconnect, restart, takeover, and recovery;
- `BRG-012`: compression, HTTP/2, TLS edges, and no-store behavior;
- `BRG-013`: frontend persistence, migration defaults, token reuse, and
  rollback;
- `BRG-014`: verification and permanent-default rollout gates.

Do not mark a requirement verified from implementation inspection alone.
Record partial evidence in the evidence column and leave the whole requirement
`Unverified` when its complete acceptance behavior is not covered. In
particular, `BRG-009` remains in progress/unverified until the separate testing
follow-up is complete.

### Implementation decisions and open questions

- Decision: the specification describes the existing bridge and the extension
  as one subsystem; the HTTP path is not a standalone specification.
- Decision: no separate ADRs initially. Material decisions are explicit in the
  technical specification; add an ADR only if a credible alternative is later
  reconsidered.
- Decision: `BRIDGE_PLAN.md` is a legacy implementation plan, not a current
  source of truth. Add a clear legacy-status pointer rather than rewriting its
  historical content.
- Decision: keep `PRODUCTION_DEPLOYMENT.md` as the current command-oriented
  deployment guide for this task; link it from the new package docs rather
  than moving it and creating URL/compatibility work.
- Decision: README files remain concise entry points and do not expose task,
  requirement-status, approval, or evidence vocabulary.
- No unresolved requirement question remains for documentation execution.

### Documentation

Create/update current documentation:

- `bridge-elixir/docs/index.md`
- `bridge-elixir/docs/quickstart.md`
- `bridge-elixir/docs/bridge-protocol.md`
- `bridge-elixir/docs/development/index.md`
- `bridge-elixir/docs/development/architecture.md`
- `bridge-elixir/docs/development/testing.md`
- `packages/frontend-sdk/docs/bridge-transports.md`
- `packages/frontend-sdk/docs/development/bridge-transport-implementation.md`
- `application/python/docs/development/bridge-server-adapter.md`
- the bridge connection section of
  `mobile/crystal-lattice-control-rn/docs/development/frontend-hosting.md`

Update package/root indexes and README pointers. Keep exact wire details
normative in the formal protocol artifact; package user pages provide
audience-compatible current guidance and examples without redefining the
target. Correct only stale README/legacy-plan claims encountered within this
bounded surface.

### Task checklist

- [ ] Inspect only the bounded implementation/test/deployment surface and
  record verified bridge behavior.
- [ ] Create the cross-package specification artifacts and `BRG-*`
  requirements.
- [ ] Create bridge package user/development docs and classify legacy/current
  source ownership.
- [ ] Create/update SDK, Python adapter, and mobile-host documentation.
- [ ] Update owning indexes and concise README/legacy-plan pointers.
- [ ] Validate touched examples and protocol names against code/tests.
- [ ] Run documentation preparation, MkDocs build, and focused link/path
  checks without editing generated output.
- [ ] Update requirement evidence and this task after verification.
- [ ] Commit the specification and current documentation together.

### Requirement verification

- Verify the new documentation requirement by checking that every formal and
  current page is reachable from its owning index, has one clear authority,
  accurately covers both legacy and new paths, and contains no excluded
  subsystem reconstruction.
- Verify `BRG-001` against registry/channel tests, HTTP and WebSocket discovery,
  two-node integration evidence, and health shape.
- Verify `BRG-002` only to the extent supported by legacy/HTTP pairing and
  resume tests; leave it unverified if the complete negative credential matrix
  is not yet covered.
- Map every remaining `BRG-*` row to concrete code, tests, current docs, this
  task, and delivery commits without treating the specification as evidence.

### Additional implementation verification

- `python docs_site/scripts/prepare_mkdocs_site.py`
- `(cd docs_site && mkdocs build)`
- focused relative-link and stale-path checks for newly added pages;
- `git diff --check`;
- inspection that `docs_site/prepared/` and `docs_site/dist/` remain generated
  outputs and are not committed.

## Follow-up execution plan — Transfer-safety hardening and focused coverage

Status: Approved

This plan closes the remaining transfer-safety requirement after the
documentation backfill. It adds focused state/failure evidence and does not
repeat the already passing large-payload, clustered, hosted, or simulator E2E
matrix.

### Scope and approach

- Make the DynamicSupervisor child limit the authoritative atomic
  active-transfer bound; the current count-before-start precheck is not atomic
  under simultaneous starts.
- Add Elixir coordinator/route tests for request-body limits, concurrent
  saturation, duplicate/invalid attachment, wrong server/direction/request ID,
  expired credentials, frontend/server/request-consumer/response-uploader
  termination, and terminal coordinator cleanup.
- Add SDK tests for old-bridge capability failure, HTTP-only operation with a
  throwing WebSocket factory, pairing-token/server mismatch, and
  representative non-2xx parity.
- Add Python tests for cancellation during request download, local backend
  streaming, response upload, bridge disconnect, supersession, and shutdown;
  assert `_inflight_v2_tasks` cleanup.
- Add a mobile component-level saved-connection reconstruction test for absent
  mode, explicit HTTP/hybrid, pairing-token reuse, and rollback.
- Reuse the existing five SDK E2E cases, one cross-node transfer E2E, one
  secure hosted edge, and one focused native selector test; do not add
  redundant payload permutations.

Physical-device network checks and a bounded concurrent load/soak run remain
rollout gates before changing the stable WebSocket default. They do not block
the current opt-in implementation unless the default-switch scope is separately
approved.

### Implementation decisions and open questions

- Decision: prefer deterministic unit/coordinator tests for terminal states and
  cleanup because E2E cannot reliably observe supervised children or Python
  task maps.
- Decision: keep one representative large JSON and binary E2E per relevant
  transport boundary.
- Decision: hosted evidence uses one secure EC2/CloudFront deployment; static
  template validation covers the parallel Fargate edge.
- Decision: do not change the permanent default in this follow-up.
- No unresolved requirement question remains for testing execution.

### Documentation

- Update `BRG-002`, `BRG-008`, `BRG-009`, `BRG-013`, and `BRG-014` live
  evidence after tests pass.
- Update bridge/SDK/mobile testing pages only for stable commands or coverage
  boundaries; do not copy test implementation detail into user guides.

### Task checklist

- [ ] Make active-transfer admission atomic and add saturation evidence.
- [ ] Add Elixir security, limit, peer-loss, and cleanup tests.
- [ ] Add SDK capability/no-WebSocket/mismatch/error tests.
- [ ] Add Python phase-specific cancellation and task-cleanup tests.
- [ ] Add saved mobile mode/token reconstruction coverage.
- [ ] Run focused suites, then the normal Elixir, Python bridge, SDK, and
  mobile suites.
- [ ] Rerun cluster/E2E only if a product path used by those boundaries changes.
- [ ] Update requirement/task evidence and commit the hardening follow-up.

### Requirement verification

- Verify the remaining transfer-safety task requirement through deterministic
  evidence that limits are atomic, credentials are scoped/rejected correctly,
  every monitored peer failure reaches one terminal state, and no coordinator
  or Python v2 task remains after completion, failure, cancellation, or
  shutdown.
- Verify the bridge documentation requirement remains accurate after any
  admission or cleanup implementation changes.

### Additional implementation verification

- `cd bridge-elixir && mix test`
- focused Python bridge transfer/cancellation tests with the worktree first on
  `PYTHONPATH`;
- `npm --workspace @crystal-lattice/frontend-sdk test`;
- mobile focused component tests, normal Jest suite, and TypeScript check;
- `git diff --check`.
