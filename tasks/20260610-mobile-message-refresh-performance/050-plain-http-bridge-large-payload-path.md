# Plain HTTP Bridge Large Payload Path

Add opt-in HTTP-only and hybrid bridge transports while preserving the existing WebSocket bridge transport as the stable default. In hybrid mode, only event polling uses the existing WebSocket request path; all other frontend bridge control and backend API requests use HTTP.

The original opt-in delivery below is completed historical scope. Current
execution is the approved **HTTP-only product bridge mode** follow-up later
in this file, which supersedes the original frontend-default rule. Mobile
implementation and automated verification are complete; human review remains
open. Desktop implementation follows confirmed human mobile review.

## Requirements checklist

- [x] Keep the existing `BridgeTransport`, its WebSocket wire messages, and its pairing/control/event/normal-request behavior fully intact and make WebSocket-only mode the default.
- [x] Expose explicit frontend bridge modes for WebSocket-only, HTTP-only, and hybrid operation without automatic request fallback between modes.
- [x] In hybrid mode, route only `GET /events` (with or without a query string) through the existing `BridgeTransport`; route discovery, pairing, resume/validation, and every other proxied backend request through HTTP.
- [x] Make HTTP-only mode complete: it must discover servers, pair, validate a saved pairing token, and proxy all backend requests—including `/events`—without opening a frontend WebSocket.
- [x] Preserve the existing SDK `Transport.request()` contract and the SDK-facing status/data/error behavior for JSON and text endpoints across all three modes.
- [x] Keep small control metadata on the Python server WebSocket, but transfer every request/response body selected for the new HTTP path as raw HTTP bytes, including a Python-to-bridge HTTP response upload path.
- [x] Support binary request and response bodies on the HTTP path without JSON text framing or base64 conversion.
- [x] Bound, authenticate, time out, cancel, and clean up HTTP transfers safely across single-node and clustered bridge deployments.
- [x] Enable negotiated gzip for HTTP bridge responses, retain HTTP/2 at supported TLS edges, and allow Brotli at deployment edges that support it; do not require Brotli from the Phoenix origin.
- [x] Wire the mobile frontend through an opt-in mode factory so old saved connections remain WebSocket-only unless explicitly configured otherwise, and leave the permanent default switch out of this task.
- [x] Add unit, integration, clustered, and SDK-facing E2E evidence for all modes, path routing, large JSON, raw binary, compression, timeout/cancellation cleanup, and unchanged legacy WebSocket behavior.
- [x] A formal cross-package bridge-connectivity specification and package-owned current documentation accurately cover the existing bridge subsystem, the HTTP/hybrid extension, directly connected frontend/server/deployment responsibilities, live requirements and evidence, and explicit exclusions without reconstructing clearly separate systems.

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
- Transfer-safety hardening completed:
  - `Bridge.HttpTransferSupervisor` atomically enforces the configured
    `max_children`; transfer start preserves the existing
    `too_many_transfers`/HTTP 429 behavior.
  - Elixir tests cover concurrent saturation, request/response limits,
    invalid and duplicate attachment, token expiry/direction/request/server
    scope, HTTP resume mismatch/invalid/unavailable cases, every monitored
    peer loss, and coordinator removal.
  - SDK tests cover old-bridge capability failure, HTTP-only operation with a
    throwing WebSocket factory, and saved-token HTTP error parity.
  - Python tests cancel real v2 work during request download, local stream
    setup, and response upload through explicit cancel, bridge close, stop,
    and supersession, then assert both task registries are empty.
  - A shared mobile helper reconstructs absent/WebSocket/HTTP/hybrid saved
    records with the same server identity and pairing token and is consumed by
    `App.tsx`.
- Documentation backfill completed after explicit approval:
  - Added the cross-package `bridge-connectivity` specification with product,
    technical, protocol, deployment/operations, frontend, and live
    requirements pages.
  - The specification covers the existing registration/discovery/pairing,
    stateless pairing credential, ephemeral session, legacy WebSocket proxy,
    HTTP/hybrid extension, clustered transfer, deployment edge, SDK, Python,
    and mobile-host responsibilities as one subsystem.
  - `BRG-001` through `BRG-013` are recorded with delivered implementation
    and evidence. `BRG-014` intentionally retains the human rollout gate for a
    separately approved permanent default switch.
  - Added package-owned bridge quickstart/protocol/architecture/testing,
    frontend SDK user/implementation, Python server-adapter, and mobile-host
    documentation.
  - Replaced the stale bridge README with a concise current entry point,
    classified `BRIDGE_PLAN.md` as a legacy document, and corrected directly
    affected package maintainer guidance.
  - `python docs_site/scripts/prepare_mkdocs_site.py` passed.
  - `mkdocs build` passed. It emitted only existing site navigation and
    `agent_core` API-doc warnings.
  - A focused link check covered every changed documentation Markdown file;
    every relative file target resolves. `git diff --check` passed.

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

- `index.md` for scope, ownership, relationships, documents, current owners,
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
normative in the formal protocol page; package user pages provide
audience-compatible current guidance and examples without redefining the
target. Correct only stale README/legacy-plan claims encountered within this
bounded surface.

### Task checklist

- [x] Inspect only the bounded implementation/test/deployment surface and
  record verified bridge behavior.
- [x] Create the cross-package specification documents and `BRG-*`
  requirements.
- [x] Create bridge package user/development docs and classify legacy/current
  source ownership.
- [x] Create/update SDK, Python adapter, and mobile-host documentation.
- [x] Update owning indexes and concise README/legacy-plan pointers.
- [x] Validate touched examples and protocol names against code/tests.
- [x] Run documentation preparation, MkDocs build, and focused link/path
  checks without editing generated output.
- [x] Update requirement evidence and this task after verification.
- [x] Commit the specification and current documentation together.

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

- [x] Make active-transfer admission atomic and add saturation evidence.
- [x] Add Elixir security, limit, peer-loss, and cleanup tests.
- [x] Add SDK capability/no-WebSocket/mismatch/error tests.
- [x] Add Python phase-specific cancellation and task-cleanup tests.
- [x] Add saved mobile mode/token reconstruction coverage.
- [x] Run focused suites, then the normal Elixir, Python bridge, SDK, and
  mobile suites.
- [x] Rerun cluster/E2E only if a product path used by those boundaries changes.
- [x] Update requirement/task evidence and commit the hardening follow-up.

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

## Completion Notes

- Outcome:
  - Existing and new frontends remain WebSocket-only by default and can select
    WebSocket, HTTP, or hybrid explicitly.
  - The existing `BridgeTransport` and legacy wire path remain intact.
  - HTTP-routed requests use raw body transfer with versioned server control
    metadata; hybrid sends only exact `GET /events` requests through the
    legacy frontend path.
  - Transfer admission, credentials, byte limits, backpressure, timeout,
    cancellation, and cleanup have deterministic focused evidence.
  - The bridge-connectivity specification and package-owned current docs cover
    the existing subsystem and the opt-in extension within the approved
    boundary.
- Final verification:
  - Elixir: 63 passed, 4 existing skips.
  - Python bridge/CLI environment: 56 passed.
  - Frontend SDK: 313 passed.
  - Mobile: 119 passed; TypeScript passed.
  - Two-node Docker/HAProxy: legacy registration/discovery/pairing/resume 3/3
    and cross-node HTTP pairing plus large raw transfer passed.
  - SDK E2E against the rebuilt two-node cluster: 4 applicable cases passed;
    the external-mode self-managed restart case was intentionally skipped and
    remains covered by the earlier five-case self-managed run.
  - Documentation preparation and MkDocs build passed; generated output
    remained ignored. Relative-link and `git diff --check` validation passed.
- Deviations and findings:
  - The first Docker wrapper run timed out during a silent cold build. A
    visible retry showed Erlang selecting Docker's unreachable NAT64 address
    for Hex even though IPv4 was available. The test image was built with
    command-line-only IPv4 host mappings; no repository networking workaround
    was added.
  - The fresh Hex build reported advisories for the currently locked
    `cowboy 2.17.0` and `cowlib 2.18.0`, including CVE-2026-65624,
    CVE-2026-43969, CVE-2026-43971, CVE-2026-43966, and CVE-2026-59248.
    Dependency remediation is separate security-maintenance scope.
  - Docker containers, images, and generated build cache were removed after
    verification; pre-existing Docker volumes were left untouched.
- Deferred scope:
  - Changing the permanent default, migrating existing records, physical-device
    network validation, and a bounded load/soak run remain rollout work that
    requires separate approval.

## Post-completion follow-up

- Merged local `develop` at `237e2e44` into the task branch.
- Resolved the documentation-site navigation conflict by retaining the newer
  package catalog and consolidated Development section, then adding the
  bridge-connectivity specification under Development → Specifications.
- Enabled publication of the Bridge Service's package-owned `docs/` and
  `docs/development/` pages through `docs_site/packages.toml`.
- Replaced the atomic-admission test's ad-hoc linked DynamicSupervisor cleanup
  with ExUnit-managed supervision. This removes a teardown race exposed by the
  main worktree's newer Elixir without changing bridge runtime behavior.
- Post-merge verification:
  - Elixir: 63 passed, 4 existing skips.
  - Python bridge/CLI environment: 56 passed.
  - Frontend SDK: 313 passed.
  - Mobile: 119 passed; TypeScript passed.
  - Documentation-site tests: 15 passed.
  - Documentation preparation and MkDocs build passed with existing
    navigation/reference warnings.

## Post-completion follow-up — HTTP-only product bridge mode

### Follow-up requirements checklist

- [x] HTTP is the only bridge transport presented in the normal frontend
  connection flow and is the effective default for new and existing saved
  bridge connections.
- [x] WebSocket and hybrid frontend transports remain implemented and
  testable, but are labeled legacy development overrides rather than normal
  product connection choices.
- [x] A dedicated Development Settings window is available from the Home menu
  and lets a developer select the product HTTP behavior, legacy WebSocket, or
  legacy hybrid for later bridge connection construction. The window supports
  additional independent development settings; bridge transport is its first
  setting.
- [x] The development override is stored separately from connection records,
  applies app-wide, survives relaunch, and can be reset to the HTTP product
  default.
- [x] The bridge wizard in the app-owned modal opened from Home presents
  saved bridge URLs first. Selecting one immediately connects and lists
  available servers; Add New Bridge enables manual entry, and successful
  bridge discovery saves the URL for reuse without requiring server pairing.
- [x] Saved bridge URLs persist separately from paired server connections and
  development preferences, retain optional labels and last-use timestamps,
  and can be removed without deleting paired connections or their credentials.
- [x] Existing records with a missing, WebSocket, or hybrid `transportMode`
  reconnect through HTTP when no development override is active, while
  retaining their server identity and pairing credential.
- [x] Changing the development override does not replay, fall back, or mutate
  an in-flight request and does not silently replace an already-open runtime;
  it takes effect when a bridge transport is next constructed.
- [x] Older bridges without HTTP protocol v1 fail with a clear compatibility
  error in normal operation, and the Development Settings window remains the
  explicit route to a legacy WebSocket diagnostic connection.
- [x] The shared SDK, mobile host, formal bridge specification, mobile
  lifecycle target, and package documentation consistently describe HTTP as
  the product default and WebSocket/hybrid as development-only overrides.
- [x] Automated SDK, mobile component, persistence, integration, and native
  tests prove the HTTP default, saved-record migration, Home-menu settings
  flow, saved/add/remove bridge URL workflow, explicit legacy diagnostics, and
  absence of automatic fallback.
- [x] The normal Bridge address input accepts a bare domain as the preferred
  format and shows a bare-domain placeholder. Bare addresses use HTTPS;
  explicit HTTP(S)/WS(S) addresses and saved legacy URLs remain compatible
  with product and development modes.
- [x] Connection setup uses keyboard avoidance on iOS and Android so the
  focused field and connection/pairing controls remain usable above the
  software keyboard.
- [ ] The mobile bridge UX is human-tested, with the user's confirmation
  recorded before desktop bridge implementation starts. Automated test
  results alone do not satisfy this gate.
- [ ] After the mobile review gate, the macOS desktop application can discover
  bridge servers, pair, save and reopen paired connections, and use its
  existing sessions/chat UI through the HTTP bridge. It reuses the accepted
  saved-endpoint workflow and preserves manual direct connections.

### Follow-up prerequisite and navigation ownership

Depends On:
tasks/20261006-mobile-home-and-contextual-content/010-home-connection-section-and-navigation.md

Begin this follow-up implementation only after that prerequisite is completed
and verified. It owns moving connection management to Home, removing the
Connections bottom tab, and presenting the existing wizard in an app-owned
modal opened from Home. This follow-up adds the saved bridge picker and HTTP
behavior inside that delivered modal; it must not recreate the old tab or
introduce a second wizard host.

Use the prerequisite's delivered connection callbacks, modal coordination,
production selectors, and navigation behavior. Preserve its wizard
cancellation and saved-connection/session compatibility. The separate Home
menu → Development Settings window remains part of this follow-up.

### User-approved direction

- Retire WebSocket and hybrid from the normal product connection experience.
- Keep both implementations available for development diagnosis and explicit
  rollback through a dedicated settings window opened from the Home menu.
- Make HTTP the normal bridge path for control, pairing, events, and every
  proxied application request.
- Reconcile this rollout with the saved-bridge-URL workflow approved in
  `tasks/20260628-cli-simplification-and-bridge-ux/040-frontend-saved-bridge-urls.md`.
- Make Development Settings a general window capable of holding other
  development settings, not a bridge-specific window.
- Add desktop bridge connectivity as a later stage, after the mobile bridge
  UX has been human-tested.
- Perform this follow-up after
  `tasks/20261006-mobile-home-and-contextual-content/010-home-connection-section-and-navigation.md`,
  using its Home connection modal as the wizard host.

This direction supersedes the earlier rollout rule that made WebSocket the
compatibility default and exposed all three modes in the connection wizard. It
does not remove the legacy transports, their wire protocols, or the registered
Python server's control WebSocket.

### Current findings and planning baseline

- `createBridgeConnectionTransport()` currently defaults to WebSocket, while
  explicit `http` and `hybrid` modes construct their separate implementations.
- Mobile currently defaults missing saved modes to WebSocket, persists a mode
  per bridge record, and renders all three selectors directly in the normal
  bridge wizard.
- `HomeScreen` already owns a Home menu with a production
  `home-menu-global-settings` action. `ConnectedRoot` owns presentation of
  Home-level modal windows, so a dedicated development modal fits the existing
  ownership boundary without coupling transport logic to `HomeScreen`.
- The existing `BridgeConnectionRecord.transportMode` must remain readable for
  storage and downgrade compatibility, but a legacy per-record value must not
  silently keep production traffic on a retired mode.
- Saved paired server records do not fulfill the earlier saved-bridge-URL
  task. Current SDK/mobile code has no `SavedBridgeUrl` type, saved URL store,
  or saved-first bridge picker. A bridge endpoint must be reusable before a
  server is selected or paired.
- Desktop's `ConnectionEditorWindow` creates manual host/port records,
  `useOpenConnections` opens only manual records through `FetchTransport`,
  and its closed-connection status reader also supports only manual records.
  The desktop stage therefore needs editor/discovery/pairing, runtime, and
  existing status-consumer integration, not merely a Bridge button.
- Desktop already consumes the shared SDK connection store and has separate
  native React windows with connection-editor save/cancel events. Reuse those
  boundaries while adding bridge records.
- Mobile has Detox iOS and Android scripts and an existing bridge-selector
  scenario. Desktop uses Jest, real-backend integration tests, and macOS
  XCUITest; no desktop Detox setup is currently present.
- The completed bridge specification still defines WebSocket as the default
  in `BRG-003`, `BRG-004`, `BRG-013`, and `BRG-014`. The mobile lifecycle
  target repeats that behavior in `MCL-014`; both targets must be updated
  before changing code.
- The earlier planning worktree was verified before planning and has since
  been removed; its task changes were merged into `develop`. Historical
  readiness evidence:
  - root and mobile `npm ci` completed;
  - the pinned Ruby 3.4.10/Bundler 4.0.15 bundle and iOS Pods installed;
  - mobile TypeScript passed;
  - 11 focused Home and bridge-record Jest tests passed;
  - a fresh iOS Detox release build passed;
  - the focused bridge-mode Detox test passed on an uncontended iPhone Air
    simulator.
- The broad Home Detox scenario reached the production app but exceeded its
  existing 180-second test timeout. A later trace showed a shared iPhone 17
  Pro simulator spent ten minutes in `simctl uninstall`; use an uncontended
  simulator type for follow-up native runs and keep the focused development
  settings scenario small.

### Saved bridge URL task reconciliation

Execute the remaining saved-URL requirements through this follow-up plan while
retaining their acceptance tracking in
`tasks/20260628-cli-simplification-and-bridge-ux/040-frontend-saved-bridge-urls.md`.
That task remains incomplete until its existing checklist has concrete
evidence. Do not equate merging a plan with completing either implementation.

| Earlier requirement group | Owning delivery in this follow-up |
| --- | --- |
| SDK `SavedBridgeUrl`, load/save functions, exports, and store tests | Separate SDK saved-URL store using `KeyValueStore`, with `{url, label?, lastUsedAt}` entries and round-trip/removal evidence. |
| Saved URLs shown first; tap connects and lists servers | Normal mobile bridge picker invokes the production mode resolver and bridge adapter with the selected URL. |
| Add New Bridge and automatic saving after successful connection | Manual-entry path upserts the endpoint after connect and server-list retrieval succeed; it does not wait for pairing or save a failed attempt. Successful paired-server connection also retains the endpoint for reuse. |
| Remove saved bridge URL | Explicit URL-list removal affects only the endpoint entry and persists across relaunch. |
| Mobile UI and SDK verification | Component and native picker tests plus a real SDK/bridge discovery test through the production frontend adapter; SDK default suite remains required. |

Endpoint reuse and transport choice are independent. Saved entries store the
configured URL, label, and last-use time, with no pairing credential or
transport-mode preference. Selecting any saved URL uses HTTP unless the
developer has explicitly set a global legacy override.

### Scope boundaries

- Do not delete `BridgeTransport`, `HybridBridgeTransport`, legacy Elixir app
  channel messages, Python legacy request handling, or their focused
  regression tests.
- Do not replace the Python server registration/control WebSocket; “HTTP-only”
  describes the frontend bridge mode.
- Do not add automatic transport fallback, retry, or request replay.
- Do not reconnect or replace an active bridge runtime when the development
  preference changes.
- Do not fold development controls into global user settings or the normal
  connection wizard; use a separately titled Home-menu window.
- Do not expand this follow-up into the broader multi-runtime mobile
  connection-lifecycle implementation.
- Do not duplicate the prerequisite's Home connection-section/navigation
  work or restore Connections-tab entry points.
- Do not begin desktop bridge implementation until the human mobile UX review
  gate is satisfied. The later stage adds bridge support to desktop's existing
  host and does not require the broader target lifecycle-controller migration.

## Follow-up execution plan — HTTP-only product bridge mode

Status: Approved

Update the formal target first, then change the SDK default and mobile host in
small checkpoints. Preserve explicit legacy constructors throughout so every
checkpoint can compare HTTP product behavior with WebSocket/hybrid diagnostic
behavior.

Delivery has three ordered stages: mobile implementation and automated
verification, human mobile UX review, then desktop bridge implementation.
All follow-up implementation starts after the declared Home-navigation
prerequisite is complete and verified. Shared SDK changes needed by mobile
belong to the first stage; their
availability does not authorize starting desktop product work before review.

Keep three persistence responsibilities separate: SDK saved bridge URLs for
endpoint discovery/reuse, paired server connection records for identity and
credentials, and mobile development preferences for app-wide diagnostics.
`HomeScreen` opens the general settings window, `ConnectedRoot` owns modal
presentation, and the app-level connection host consumes hydrated preferences
and saved endpoints through shared helpers.

Use a versioned `DevelopmentSettings` value and a shared preference
provider/store with field-specific updates. `DevelopmentSettingsModal` renders
named sections, beginning with a Bridge section. A transport change/reset
updates only its preference and preserves other development settings. Future
sections can add their own controls and preferences without replacing the
window, storage key, or unrelated values; no generic plugin/schema framework
or placeholder controls are required.

### Stage 1 — Mobile implementation and automated verification

Rebase the implementation baseline onto the completed Home-navigation task
and use its app-owned wizard modal. Its navigation relocation is a
prerequisite result, not work to repeat in this stage.

1. Revise the bridge-connectivity and mobile connection-lifecycle
   specifications so HTTP is the product default, omitted modes resolve to
   HTTP, legacy modes are development-only overrides, and the new rollout
   direction is distinguished from still-pending verification evidence.
2. Change the shared SDK factory's omitted-mode behavior to HTTP while keeping
   all three `BridgeTransportMode` values and concrete implementations
   available to explicit callers. Keep the no-fallback rule unchanged.
3. Introduce general mobile development-preference state with a versioned
   AsyncStorage key and an effective bridge mode of HTTP when the transport
   setting is absent, malformed, or reset. The initial preference is an
   app-wide optional legacy override; updates preserve other settings.
   Do not derive production behavior from a connection record's historical mode.
4. Centralize mobile bridge construction around
   `effective mode = development override ?? http`. New pairing records store
   the product mode, while existing record IDs, URLs, server IDs, names,
   pairing credentials, caches, and workspace ownership remain unchanged.
5. Add/export the SDK `SavedBridgeUrl` type and
   `loadSavedBridgeUrls`/`saveSavedBridgeUrls` functions using the earlier
   task's independent `clc_saved_bridges_v1` key. Add store tests. Hydrate
   before writes so initial empty state cannot overwrite stored endpoints.
6. Make the bridge wizard inside the existing Home connection modal show
   saved endpoints and Add New Bridge.
   Tapping an endpoint connects and lists servers immediately. Manual entry
   uses the same connection helper; upsert URLs and refresh `lastUsedAt`
   after successful discovery and successful paired-server connection.
   Provide URL-list removal without changing paired records. Remove the
   transport selectors and experimental copy from this flow. Preserve
   existing saved `ws`/`wss` URLs because the HTTP transport already derives
   their HTTP origin.
7. Add a general `DevelopmentSettingsModal` presented by `ConnectedRoot`.
   Add a stable `home-menu-development-settings` entry to `HomeScreen`; the
   Bridge section shows HTTP as “Product default” and WebSocket/hybrid as
   clearly labeled legacy diagnostics, includes a transport-scoped reset
   action, and explains that a selection applies to the next bridge open.
8. Route saved-endpoint discovery, new connection, saved paired-server open,
   repair, and later transport reconstruction through the same effective-mode
   resolver. Foreground work on an already-created transport continues through
   that instance, so a preference change cannot switch or replay an active request.
9. Replace the existing native mode-selector scenario with a production Home
   menu → Development Settings scenario and retain lower-level SDK legacy-mode
   coverage. Add the Home → connection modal →
   saved-first/add/remove/relaunch discovery scenario.
   Run the affected verification matrix before updating current user and
   maintainer documentation and both tasks' completion evidence.

### Stage 2 — Human mobile UX review and desktop gate

Provide a runnable mobile build and concise review steps starting on Home and
opening its connection modal, then exercising the saved-first picker, manual
addition, server discovery, pairing, modal cancellation, reopen after
relaunch, independent URL removal, and Home → Development Settings. Include
selecting and resetting a legacy override and checking that an open connection
is left untouched.

Record the reviewed build/revision, platform/device, feedback, any resulting
fixes, and the user's confirmation that the mobile UX has been human-tested
and is ready to carry into desktop. Rerun affected automated checks after
fixes. Keep the human-verification requirement and desktop-start checklist
item incomplete until confirmation arrives; a successful Detox run, elapsed
time, or lack of feedback cannot satisfy the gate.

### Stage 3 — Desktop bridge connectivity

Start only after Stage 2. Carry the accepted endpoint/discovery/pairing UX into
the existing macOS connection editor and Connections panel. Reuse the shared
SDK saved-URL store, connection records, HTTP bridge adapter, and backend
instead of duplicating the bridge protocol. Saved endpoints and credentials
remain local to each application; this stage does not add cross-device sync.

The connection editor owns discovery/pairing presentation and submits a
completed bridge record through the existing native save/cancel boundary.
`DesktopRoot` remains the authority for saved connections and open runtimes;
coordinate saved-endpoint updates with it so separate native windows cannot
overwrite stale storage. Cancellation must dispose of the editor's pending
bridge transport and must not submit an incomplete paired record.

1. Extend the desktop connection editor with a Bridge route containing the
   accepted saved-first picker, Add New Bridge, discovery, server selection,
   and pairing. Keep the existing manual editor available, including when
   editing manual records; editing a bridge record must not convert it into
   a manual connection.
2. Extend desktop connection persistence/event handling to save paired bridge
   records and endpoint changes independently. Preserve server IDs and
   pairing credentials when reopening; apply the accepted endpoint-removal
   semantics without deleting paired connections.
3. Generalize open-runtime transport typing and construction in
   `useOpenConnections` to support the shared HTTP bridge adapter alongside
   `FetchTransport`. Connect/resume pairing before backend verification, and
   dispose of bridge transports on close or unsuccessful open. Keep existing
   several-open-runtime, focused-connection, and session-tab behavior.
4. Integrate bridge records into production panel labels, Home/status
   consumers, and the existing sessions/chat/event paths. Support the closed
   bridge status reader through the HTTP adapter with saved credentials.
   Apply the same HTTP capability error and no-fallback/no-replay rules.
5. Add focused desktop component/persistence/runtime tests and a real bridge
   integration through the production editor/host, public discovery/pairing,
   saved reopen, and `RestAgentBackend` session/message/event path.
6. Add focused macOS XCUITest for native editor discovery/pairing presentation,
   save/cancel, and saved bridge reopen, with stable production selectors.
   Use real-network integration separately from deterministic native
   presentation checks; do not label a fake backend harness as network E2E.
7. Update desktop package-user and hosting documentation and any affected
   lifecycle target boundary to distinguish delivered bridge support from the
   still-separate lifecycle-controller migration. Run desktop TypeScript,
   focused then affected Jest/integration suites, native build/UI tests, and
   manual-connection regression coverage.

### Risks and mitigations

- **Legacy records remain on a retired mode:** ignore historical record mode
  for effective production selection and test missing, WebSocket, hybrid, and
  HTTP records under an absent development override.
- **A diagnostic override leaks into saved product state:** persist it under a
  separate development-settings key; new connection records remain HTTP.
- **Preference hydration races a saved connection open:** expose hydration
  state and prevent bridge construction until the setting has resolved to a
  valid value.
- **A saved URL is confused with a paired server connection:** use separate
  stores and verify that URL-list removal preserves saved server credentials.
- **Adding future settings overwrites transport or unrelated preferences:**
  update/reset fields independently within general development preferences.
- **Changing a setting duplicates a write:** apply it only to newly
  constructed transports and retain the existing prohibition on fallback.
- **Older bridge deployment cannot serve HTTP v1:** keep the capability error
  actionable and make legacy WebSocket selectable through Development
  Settings without silently falling back.
- **Home-menu regression is hidden by a large native suite:** add one focused
  production-screen Detox scenario with stable selectors, then retain the
  broader Home test as separate regression coverage.
- **Future connection-lifecycle work restores the old default:** update
  `MCL-014` and its technical compatibility section in the same change.
- **Bridge tests or UI restore the removed Connections tab:** build on the
  prerequisite's Home modal and update native entry points; preserve its
  production navigation and cancellation regressions.
- **Desktop repeats an unreviewed mobile interaction:** block desktop product
  implementation on explicit human review, then carry accepted behavior and
  feedback into the native desktop window.
- **Desktop native windows race endpoint persistence:** retain one authoritative
  host for updates and test save/cancel across the actual window event boundary.
- **A bridge runtime is retained after desktop close/cancel:** add disposal
  coverage while preserving multiple unrelated open connections.

### Implementation decisions and open questions

- Decision: “retired” means removed from normal product selection and default
  behavior, not deleting the legacy implementations or protocol.
- Decision: the development mode override is one app-wide local preference,
  not a per-connection property.
- Decision: Development Settings is a general window and preference store,
  with bridge transport as the first section. Transport reset is scoped to
  that setting and preserves other values.
- Decision: the Development Settings entry is visible in the Home menu in
  normal builds. This keeps emergency rollback and field diagnosis available;
  it is explicitly labeled development-only rather than hidden behind
  `__DEV__` or a gesture.
- Decision: changing the override affects only later transport construction.
  The modal does not reconnect, close, or replace an active runtime.
- Decision: existing `transportMode` fields remain readable for compatibility
  but do not select a retired mode when the development override is absent.
  New mobile records persist HTTP, not the active diagnostic override.
- Decision: continue accepting existing `ws`/`wss` bridge URLs in the normal
  wizard and saved records; URL-shape migration is not required to make the
  frontend use HTTP.
- Decision: explicit SDK `mode: "websocket"` and `mode: "hybrid"` remain
  supported for development tools and tests. Omitted SDK mode becomes HTTP.
- Decision: implement the earlier saved-bridge-URL workflow in the same
  follow-up delivery and keep its original requirements checklist as the
  acceptance record. Saved endpoints, paired credentials, and development
  settings stay separate.
- Decision: desktop delivery follows human mobile UX confirmation. Mobile
  Detox and desktop macOS XCUITest are separate native verification boundaries,
  complemented by real bridge integration tests.
- Decision: Home connection placement and modal ownership are supplied by
  `tasks/20261006-mobile-home-and-contextual-content/010-home-connection-section-and-navigation.md`.
  This follow-up starts afterward and changes the bridge content/transport
  within that host.
- The user approved bare-domain input and its placeholder on 2026-10-12.
  Bare addresses use HTTPS, with explicit `http://` for plaintext local
  deployments. Existing WS(S) addresses remain valid. Desktop must reuse this
  accepted input contract after the human mobile review gate.
- The visibility and app-wide scope of Development Settings are highlighted
  for approval because they
  materially define the diagnostic escape hatch.

### Documentation

- Update the bridge-connectivity specification index, product behavior,
  frontend behavior, and requirements/evidence rows `BRG-003`, `BRG-004`,
  `BRG-005`, `BRG-013`, and `BRG-014` before implementation claims change.
- Update mobile connection-lifecycle `MCL-014` and its technical compatibility
  section so future lifecycle work preserves the HTTP product default and
  app-wide development override.
- Update the frontend SDK bridge user and implementation docs with the new
  omitted-mode behavior and development-only status of explicit legacy modes.
- Update mobile bridge-hosting and Home documentation with the dedicated
  general Development Settings route, Bridge section, persistence scope,
  next-open semantics, migration behavior, and saved/add/remove endpoint
  workflow through the Home connection modal. Keep the prerequisite's
  navigation documentation authoritative; remove obsolete tab-based
  instructions rather than documenting a parallel wizard.
- Document the SDK saved-URL type, store functions, and credential-independent
  endpoint reuse with the owning connection documentation.
- After human mobile review, update desktop package-user documentation with
  bridge discovery/pairing and saved reopen, and developer documentation with
  runtime/window ownership and native/integration verification. Preserve the
  broader desktop lifecycle target's separate scope.
- Update concise package README statements that currently call WebSocket the
  default or show the old normal-wizard selector. Do not expose task status or
  requirement IDs in user documentation.

### Task checklist

- [x] Confirm completion/evidence of
  `tasks/20261006-mobile-home-and-contextual-content/010-home-connection-section-and-navigation.md`
  and use its delivered Home connection modal before starting implementation.
- [x] Update the bridge and mobile lifecycle target specifications first.
- [x] Change the SDK factory default to HTTP and retain explicit legacy modes.
- [x] Add versioned general development preference persistence with
  independent field updates and a transport-scoped reset.
- [x] Make saved-record reconstruction default every historical record shape
  to HTTP unless a development override is active.
- [x] Keep new records on HTTP without persisting the diagnostic override.
- [x] Add/export the saved bridge URL type/store and SDK persistence tests
  required by the earlier saved-URL task.
- [x] Add the saved-first bridge picker, Add New Bridge, successful discovery
  auto-save, and independent URL removal/persistence inside the Home modal.
- [x] Remove transport choices from the normal bridge connection wizard.
- [x] Add the general Home-menu Development Settings modal with its initial
  Bridge section and transport-scoped reset.
- [x] Route saved-endpoint discovery, new, saved, and repair construction
  through one effective-mode resolver.
- [x] Add SDK default/explicit-mode/no-fallback regression tests.
- [x] Add mobile preference parsing, hydration, persistence, migration, and
  reconstruction tests.
- [x] Add Home menu/modal component tests and saved/add/remove wizard tests
  through the Home connection modal, including cancellation, preference
  hydration, and saved-endpoint hydration.
- [x] Replace the old selector Detox scenario with focused Home development
  settings and HTTP-only normal-wizard coverage on iOS and Android.
- [x] Verify saved URL selection through real discovery using the production
  frontend bridge adapter.
- [x] Update the earlier saved-URL task's acceptance checklist after native
  verification is complete.
- [x] Run the existing HTTP, WebSocket, hybrid, cluster, and bridge-restart
  regression suites appropriate to the unchanged protocol boundary.
- [x] Update current package documentation and live requirement evidence.
- [x] Run documentation preparation/build and focused link checks.
- [ ] Provide a mobile review build and walkthrough, resolve feedback, and
  record the user's human-testing confirmation.
- [ ] Start the desktop stage only after that confirmation is recorded.
- [ ] Add desktop bridge picker/discovery/pairing and authoritative saved
  endpoint/paired-record persistence through native window events.
- [ ] Support bridge open/reopen/close in desktop runtime and existing
  sessions/chat/status consumers without regressing manual connections.
- [ ] Add and run desktop component, real-bridge integration, and focused
  macOS XCUITest coverage, then update desktop documentation/evidence.

### Requirement verification

- **Prerequisite and Home wizard integration:** record the completed navigation
  task's revision and evidence. Component/Detox tests enter the production
  connection modal from Home, exercise and cancel the bridge wizard, and prove
  no removed Connections-tab path is required.
- **HTTP-only normal product flow:** component and native tests enter the
  Home connection modal and its saved-first bridge wizard, find no
  WebSocket/hybrid selector, pair/reopen using HTTP, and prove no frontend
  WebSocket factory is invoked.
- **Saved bridge URLs:** SDK tests prove independent round-trip/removal
  persistence and preserved labels/timestamps. Mobile component/native tests
  add an endpoint, discover servers before pairing, relaunch, select the saved
  entry without retyping, and remove it. Test that failed discovery does not
  save an endpoint, successful discovery with no available servers still saves
  it, repeated successful use upserts it, and removal leaves paired server
  records/tokens intact. At least one mobile integration test
  starts from Home and takes a saved URL from the modal's production picker
  through its real connection handler, mode factory, and adapter to the
  bridge's public discovery API;
  a mocked server list or store-only test is not decisive evidence for this
  connection.
- **Development-only legacy modes:** Home menu/component/Detox tests open the
  dedicated modal, select each labeled legacy mode, reconstruct a later bridge
  transport with the same server/token, and reset to HTTP. SDK tests continue
  to prove explicit legacy construction and exact hybrid event routing.
- **Saved-record migration:** table-driven tests load records with absent,
  HTTP, WebSocket, hybrid, and malformed mode values and prove HTTP is
  effective without an override. Separate tests prove no ID, URL, server
  identity, pairing token, cache key, or workspace ownership changes.
- **Preference lifecycle:** persistence tests cover first install, relaunch,
  reset, malformed storage, hydration-before-open, and app-wide use across
  multiple bridge records. A store/component fixture with a second independent
  preference proves that changing/resetting bridge transport preserves it;
  the fixture does not add an unsolicited product setting.
- **No replay or active mutation:** tests start an HTTP request or retain an
  open transport, change the development preference, and prove the current
  instance is untouched and the override applies only after reconstruction.
- **Compatibility failure:** SDK/mobile tests show a clear HTTP capability
  error for an older bridge and prove that only an explicit development
  setting enables a later legacy diagnostic connection.
- **Regression boundary:** rerun SDK unit suites, HTTP-only SDK E2E, explicit
  legacy/hybrid E2E, bridge restart/cluster coverage, mobile Jest/TypeScript,
  and focused iOS/Android Detox scenarios. Existing server-control WebSocket
  and backend protocol tests remain unchanged.
- **Human review and sequencing:** retain the user's confirmation against the
  reviewed mobile build/device and record addressed feedback. Desktop
  implementation must not precede that evidence. This requirement remains
  incomplete until human verification is confirmed.
- **Desktop bridge capability:** after the gate, a real-bridge integration
  test exercises the production desktop editor/host and SDK adapter through
  discovery, normal pairing, persisted reopen, session/message retrieval,
  sending, and event updates. It proves credential reuse and no frontend
  WebSocket in normal mode; manual-connection tests prove preserved direct
  operation. Separate component/native tests cover endpoint deletion without
  paired-record deletion, native save/cancel, close/disposal, and independent
  simultaneous runtimes. A direct SDK test or deterministic native harness
  alone is not decisive evidence for desktop host connectivity.
- **Documentation consistency:** specification and package pages agree on the
  HTTP default, development-only legacy modes, general settings window,
  saved URL reuse, migration, and next-open behavior; stale “WebSocket
  default” and normal-selector claims are absent from maintained sources.

### Additional implementation verification

- `npm --workspace @crystal-lattice/frontend-sdk test`
- `npm --workspace @crystal-lattice/frontend-sdk run integration:bridge`
- `cd mobile/crystal-lattice-control-rn && npm run tsc`
- focused mobile Jest tests followed by
  `cd mobile/crystal-lattice-control-rn && npm test -- --runInBand`
- `cd mobile/crystal-lattice-control-rn && npm run detox:build:ios`
- focused development-settings Detox on an uncontended iOS simulator and
  `npm run detox:build:android` plus its Android scenario
- Focused saved/add/remove/relaunch Detox scenarios on iOS and Android;
  deterministic native tests supplement the real bridge integration tests.
- After human mobile confirmation, from
  `desktop/crystal-lattice-control-desktop-rn`: `npm run tsc`, focused Jest then
  `npm test -- --runInBand`, focused `npm run test:integration`, and focused
  `npm run test:macos-ui` coverage for the new bridge editor. Run macOS UI
  automation sequentially with mobile simulator automation and preserve
  pre-existing application/test processes per desktop native testing guidance.
- `cd bridge-elixir && mix test`
- focused Python bridge-client suites with the worktree first on `PYTHONPATH`
- `python docs_site/scripts/prepare_mkdocs_site.py`
- `(cd docs_site && mkdocs build)`
- focused relative-link/stale-default checks and `git diff --check`

## Follow-up Implementation Notes

- Execution approved by the user on 2026-10-07. Implementation is isolated in
  `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20261007-http-bridge-mobile-ux`
  on branch `task/20261007-http-bridge-mobile-ux`, based on `develop` at
  `768fe0f7`. The latest task drafts were copied from the main worktree;
  unrelated main-worktree changes remain intact.
- The Home-navigation prerequisite is complete in this baseline. Its checked
  requirements and completion/follow-up evidence include the production HTTP
  Detox journey, setup cancellation/failure retention, native Home/settings,
  and bridge selection within the delivered modal.
- Stage 1 is authorized. Stage 3 remains gated on human mobile review.
  Short-address input was unresolved at this checkpoint; the later
  2026-10-12 feedback section records its approval and implementation.
- Implemented the HTTP SDK default, separate endpoint/development stores,
  saved-first Home-modal bridge flow, and general Development Settings window.
  Legacy transport implementations and Python/server wire behavior are intact.
  Repair reuses the original connection ID for the same server and retains the
  active connection until candidate promotion, preserving cache ownership.
- Current automated evidence:
  - SDK: 52 suites / 381 tests pass, including default/no-socket, legacy,
    hybrid, endpoint storage, and 404/405 capability errors.
  - Mobile: 61 suites / 334 tests pass; the added repair identity regression
    also passes in the focused 9-test App bridge suite. TypeScript passes.
  - Real mobile App integration passes through Home discovery, save before
    pairing, pairing, relaunch/same-token reopen, and session creation after
    selecting a legacy preference while the HTTP runtime remains open.
  - Real SDK bridge E2E against a local production Phoenix process: 4 pass;
    the Docker-managed restart case is intentionally skipped in external mode.
  - Python bridge/CLI regression: 55 pass. Elixir: 63 tests, no failures,
    4 pre-existing skips.
  - iOS Release simulator and Android E2E builds pass in this worktree.
    Documentation preparation/build and 17 preparation tests pass.
- Docker-managed regression first failed before assertions because Docker's
  filesystem rejects build leases as read-only. A local `mix run --no-halt`
  bridge on port 4400 provides the real production API for remaining tests.
  Docker restart/cluster verification has not been rerun.
- The first iOS native run timed out while `simctl launch` was blocked before
  the app's first bridge request. Task-owned processes were stopped; a fresh
  `HTTP-Bridge-Review` simulator (`562E9666-900C-4BA0-8400-15E1C2F7962B`)
  is being used for a focused retry. Native results remain incomplete.
- Native retries did not complete successfully:
  - the fresh iOS simulator also stalled in `simctl launch` before application
    requests; task-owned automation was stopped and the device shut down;
  - Android's initial run reported no activities, then stalled during failure
    capture and lost its settings service;
  - a cold, headless software-rendered Android retry reached Home but failed
    with an Espresso window-focus error while opening Development Settings;
  - a synchronized retry exposed System UI nonresponsiveness and an app ANR
    blocked in the platform `WindowManager.hasNavigationBar` binder call
    during React-root creation.
  Native checks remain unresolved and are not counted as passing. Retrying on
  a healthy runtime must resolve both startup and the observed modal-focus
  failure. Global simulator/Docker service resets were not performed because
  other existing applications/processes are outside this task.
- The final real-bridge component integration additionally sends a message
  through the production composer and observes an assistant response through
  the public backend. A pending real HTTP event request remains un-aborted
  when the development preference changes.
- Saved opens now disconnect the previous transport only after the candidate
  succeeds. A focused App regression proves that pending and cancelled repair
  of another server leave the active HTTP event request intact.
- Saved-connection details omit per-record transport labels: stored product
  metadata cannot accurately describe an already-open diagnostic transport.
- Root connection-lifecycle targets were also corrected to the HTTP default,
  preventing a later shared-controller migration from restoring the retired
  default.
- Final mobile regression passes: 62 suites / 336 tests, including repair
  retention, with no lingering Jest-handle warning. TypeScript and the final
  real-bridge integration (including send/assistant response) pass. Both review
  builds were rebuilt after the final source changes.
- Review artifacts:
  - `artifacts/bridge-mobile-review/CrystalLattice-HTTP-Bridge-Simulator.zip`
    (iOS simulator application bundle, 40 MB);
  - `artifacts/bridge-mobile-review/CrystalLattice-HTTP-Bridge-E2E.apk`
    (Android E2E application, 77 MB).
- Implementation is ready for continued native verification and review.
  Native acceptance, human feedback/confirmation, and all desktop delivery
  remain incomplete. No follow-up completion notes are recorded because those
  gates are still open.

### Verification retry — 2026-10-08

- After the user's Docker restart, the Docker-backed SDK suite passes all five
  cases, including managed bridge restart/resume. The earlier read-only build
  failure is resolved.
- The two-node Docker/HAProxy runner passes all three legacy scenarios and the
  HTTP pairing/raw-transfer scenario. Its assertions prove a 1.2 MB request
  and 900 KB response traverse both bridge nodes.
- The production mobile App integration also passes against that two-node
  bridge, including discovery, pairing, saved-token reopen, sending/assistant
  response, and the retained in-flight request after preference change.
- iOS Development Settings Detox passes on the dedicated review simulator:
  HTTP default, explicit legacy selections, relaunch persistence, reset,
  and the normal wizard's absence of legacy selectors.
- The iOS real-bridge Detox journey also passes against the two-node bridge:
  saves discovery before pairing, reuses the saved endpoint after relaunch,
  pairs, sends through the production composer and observes the assistant
  response, removes only endpoint history, and reopens the paired server
  without another code. It creates both expected backend sessions.
- Native test timing was corrected to wait for enabled controls and completed
  alert/agent-picker transitions when synchronization is disabled. One
  attempted wait matcher was unsupported by this Detox version and was replaced
  by polling the documented native `enabled` attribute; TypeScript passes.
  No product behavior, mocks, or transport shortcuts were changed.
- The real CLI-to-bridge integration passes against the cluster. Android native
  verification was retried through the documented emulator preparation:
  both native suites fail before the Home entry points can be exercised.
  The failure screenshot shows the emulator's “System UI isn't responding”
  dialog stealing window focus; this is not counted as passing Android
  coverage. A healthy Android runtime remains necessary for acceptance.
- Final retry results: Docker SDK 5/5; cluster legacy 3/3 plus cross-node HTTP
  transfer; real CLI 1/1; real mobile App integration 1/1; iOS native settings
  1/1 and real bridge journey 1/1. TypeScript and `git diff --check` pass.
  Product source and review binaries are unchanged; only native test waits
  and task/specification evidence were updated.

### Android verification retry — 2026-10-10

- The user requested another Android check. Existing APKs were reused, and
  the original AVD was retried with a cold boot, four CPU cores, and 3 GB RAM
  instead of its saved one-core/2 GB profile. Instrumentation did not become
  ready and failed before feature assertions.
- The host had only 2.8 GB of free space. Removed generated
  `ios/build/Build/Intermediates.noindex` and
  `android/app/build/intermediates` from this task worktree, reclaiming about
  5 GB. APKs, the simulator application, and review archives were preserved.
  No unrelated source/worktree or global cache cleanup was performed.
- Created the separate `CLC_HTTP_Bridge_20261010` AVD using the installed API
  36.1 image, four cores, 3 GB RAM, and fresh data. The original AVD was
  preserved. Applied the documented emulator preparation so first-run
  immersive-mode confirmation was recorded before testing.
- Final prepared clean-AVD run: both collected scenarios failed. Settings
  reached Home and opened its menu; the screenshot shows the Development
  Settings item, but Espresso failed to select a focused window while waiting
  for that item. The real bridge journey failed to find the initial New
  connection control after startup. Logs also report native ANRs in Android
  Settings/content-provider access and UI automation.
- Android acceptance remains incomplete. The run does not establish whether
  the remaining modal-focus issue is confined to runtime/automation or exposes
  an Android product issue; successful native verification is still required.
  No product code or test assertions were changed in this retry.

### Android blocker resolution and mobile review handoff — 2026-10-10

- The user resolved the host disk constraint and authorized continuing
  investigation with web research. The generated APKs had been removed during
  cleanup, so rebuilt the app and instrumentation with the supported
  `-PreactNativeArchitectures=arm64-v8a` setting.
- Installed the API 35 plain AOSP ARM64 image and created the isolated
  `CLC_HTTP_Bridge_AOSP35_20261010` AVD. Original/user-created AVDs were
  preserved. Research into the AndroidX window-focus issue was a diagnostic
  lead; the actual blocker was identified from the native failure screenshot
  and app source.
- The plain-image screenshot showed Android's first-run fullscreen
  confirmation covering Home. `MainActivity.onCreate` already skips immersive
  mode for `IS_DETOX_E2E`, but its focus callback re-enabled it. Applied the same
  existing E2E guard to `onWindowFocusChanged`; normal builds retain their
  existing behavior. This fixes test infrastructure without replacing UI,
  transport, backend, or assertions.
- Android native verification now passes in one complete command: 2 suites,
  2 tests, successful cleanup/exit. It covers Home → Development Settings,
  legacy selection/persistence/reset, HTTP-only normal setup, discovery saved
  before pairing, native pairing, send/assistant response, relaunch,
  independent endpoint removal, and saved-server reopen through the real
  Docker bridge and Python backend.
- Verified invocation, from the mobile package:
  `DETOX_ANDROID_AVD=CLC_HTTP_Bridge_AOSP35_20261010 BRIDGE_E2E_MODE=external BRIDGE_E2E_URL=ws://127.0.0.1:4000/ws/websocket node_modules/.bin/detox test -c android.emu.e2e e2e/bridgeTransportMode.e2e.test.ts e2e/bridgeConnection.e2e.test.ts --device-boot-args='-no-snapshot -cores 4 -memory 3072' --cleanup`.
- The Android review APK was refreshed with the tested ARM64 build. The iOS
  review archive remains the previously verified build. Automated mobile
  requirements are satisfied; this does not constitute human UX confirmation.
- Post-fix verification: mobile TypeScript passes; all 62 component suites /
  336 tests pass with successful exit; documentation preparation, 17 site
  preparation tests, and MkDocs build pass with existing unrelated link
  warnings. `git diff --check` passes. The ARM64 Android review APK is 31 MB;
  the unchanged iOS simulator archive is 40 MB.

#### Human review walkthrough

Use the review builds under `artifacts/bridge-mobile-review/` with a registered
server on an HTTP-v1-capable bridge:

1. Home → New connection → Bridge. Verify the saved-first picker and Add New
   Bridge, then discover servers. Close setup before pairing, reopen, and use
   the saved endpoint without retyping.
2. Pair using the server's normal six-digit code. Create/send in a session and
   relaunch to reopen the paired server without another code.
3. Remove the endpoint from the picker. Verify the paired server card and its
   authorization remain available.
4. Home menu → Development Settings. Review the general window and Bridge
   section, legacy diagnostic labels, persistence/reset, and next-open wording.
   Changing the setting must leave an already-open connection running.
5. Confirm the mobile UX is acceptable, or report feedback. Desktop bridge
   implementation remains blocked until that confirmation is recorded.

### Integration before develop merge — 2026-10-11

- The user requested a `--no-ff` merge into `develop`. Committed the verified
  implementation as `d076ddf2`, then integrated `develop` at `750b0ea7`
  in the isolated task worktree before the final target-branch merge.
- Conflicts were limited to the earlier Draft task records. Preserved the
  approved execution status, completed evidence, and original completion
  notes, and removed a duplicated saved-URL reconciliation section.
- Combined-state verification passes: SDK 381 tests, shared React Native UI
  76 tests, mobile 63 suites / 340 tests, and mobile TypeScript. The feature
  diff against `develop` passes whitespace checks. Incoming unrelated changes
  were preserved without edits.
- Merging the code does not constitute human mobile UX confirmation; desktop
  bridge implementation remains gated as recorded above.

### Mobile UX feedback implementation — 2026-10-12

- The user requested preferred bare-domain entry/placeholder and correction
  of keyboard overlap in the connection modal. Execution of these changes is
  authorized by that request; human acceptance and desktop remain pending.
- Added shared address normalization: omitted scheme means HTTPS, explicit
  HTTP(S)/WS(S) remains supported, and legacy diagnostic factories derive the
  standard WebSocket endpoint from a bare domain or HTTP origin. Existing
  configured WebSocket endpoint paths/queries are preserved.
- The mobile form validates through the shared helper, keeps the trimmed
  entered address in endpoint history, and shows `bridge.example.com` as the
  placeholder. Connectivity testing uses the same HTTP-base derivation.
- The wizard already requested `KeyboardAvoidingView`. Its Android behavior
  was unset, and modal size was tied to the outer view. Keyboard avoidance now
  uses explicit platform behavior and an inner viewport so modal bounds and
  scrolling follow the remaining height.
- Focused SDK address/transport and mobile App input tests pass. Native
  verification uses real software-keyboard viewport assertions and the public
  bridge discovery/pairing/send/reopen path.
- Feedback implementation verified: SDK 54 suites / 400 tests; mobile 64
  suites / 349 tests; mobile TypeScript; real App-to-bridge integration; and
  Docker SDK transport regressions 5/5 pass.
- iOS native real-bridge journey and Android settings/real-bridge journeys
  pass. The tests open the software keyboard, verify the available viewport
  shrinks, assert the modal stays within it, and use the visible Connect
  action. They continue through real discovery/pairing, send/response, and
  saved reopen.
- Setup cancellation/completion now dismisses the keyboard. The stronger
  keyboard scenario also exposed the chat keyboard offset under the safe
  area; that offset was corrected, and the normal native Send action passes
  while the keyboard is open.
- The user requested committing these feedback changes on `develop`.
  Unrelated concurrent workspace changes were preserved. Human mobile UX
  acceptance and the desktop stage remain open.
- Documentation preparation/build pass with existing unrelated link warnings;
  whitespace checks pass.
