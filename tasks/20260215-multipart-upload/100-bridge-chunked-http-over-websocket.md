# Bridge: Chunked HTTP request + response bodies over Phoenix WebSockets (large JSON/base64 attachments)

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Support large JSON payloads (notably base64-encoded attachments inside `multipartContent`) **and large JSON responses** when using the Elixir bridge transport by introducing an application-level chunking protocol for proxied HTTP requests over Phoenix Channels.

The goal is that:

- Mobile/desktop code continues to call the backend as if it is making a single HTTP request with a large JSON body.
- FastAPI continues to receive a single HTTP request with the full (reassembled) JSON body.
- The intermediary bridge layers (TS `BridgeTransport`, Elixir channels, Python `BridgeClient`) break the body into multiple smaller WebSocket messages and reassemble it.
- For large responses, FastAPI still returns a normal single HTTP response, but the bridge layers chunk and reassemble the response body across multiple WebSocket messages.

Elixir should remain a simple forwarder (**no request/response reassembly in Elixir**), but it must be updated to forward new events.

## Depends On

- None strictly, but it is motivated by multipart/base64 attachments.

## Background / Current State (End-to-end flow today)

### App-side (TypeScript)

- The frontend SDK transport `BridgeTransport` sends proxied HTTP requests via Phoenix messages.
- It embeds the HTTP body as a JSON string inside the Phoenix payload:
  - `payload.body = req.body === undefined ? null : JSON.stringify(req.body)`
  - File: `packages/frontend-sdk/src/transport/bridgeTransport.ts:104`

- It then wraps `{topic,event,payload,ref}` into a single WebSocket text frame.

- Default request timeout for Phoenix request/reply is 30s:
  - File: `packages/frontend-sdk/src/transport/bridgeTransport.ts:248`

### Elixir bridge

- `Bridge.AppChannel.handle_in("http_request", ...)` broadcasts to the paired server and waits for a response for up to 60s:
  - File: `bridge-elixir/lib/bridge/app_channel.ex:141`

- Phoenix WebSocket endpoint config includes a 45s websocket timeout (idle/heartbeat semantics):
  - File: `bridge-elixir/lib/bridge/endpoint.ex:4`

### Server-side (Python)

- `BridgeClient` connects with `websockets.connect(ws_url)` defaults:
  - File: `application/python/agent_terminal_app/bridge_client.py:136`

Important limitation:

- Python `websockets` has a default `max_size` of 1 MiB for incoming messages. Large base64 payloads will exceed this and the connection will close.

- The local proxy to FastAPI uses `httpx.AsyncClient(timeout=10.0)`:
  - File: `application/python/agent_terminal_app/bridge_client.py:344`
  - This makes the effective end-to-end timeout often 10s for bridged calls.

### Missing/correctness issues already observed

- Large payloads fail due to WebSocket message size limits (Python `max_size` default and likely Cowboy limits).
- `BridgeTransport` always returns `{ status: 200, data }` and does not propagate real HTTP status codes:
  - File: `packages/frontend-sdk/src/transport/bridgeTransport.ts:141`
- Python bridge client ignores incoming proxied headers and forwards only JSON Content-Type.

## Problem Statement

We need to support large attachments encoded as base64 in JSON while using the Elixir bridge.

Simply increasing max WS message size across clients/servers is brittle and still has practical limits. Because WebSocket implementations enforce `max_size` on the reassembled message, relying on lower-level frame fragmentation is insufficient.

We need an application-level chunking protocol.

Additionally, even if we chunk requests, **large responses can still exceed WebSocket message size limits** (particularly Python `websockets` default `max_size`). We need response chunking as well.

## Proposed Approach (Recommended)

### Overview

Introduce a new chunked request protocol and a new chunked response protocol while maintaining compatibility with the existing `http_request` / `http_response` events.

- App (TS) splits the HTTP request body into chunks and sends:
  - `http_request_init`
  - `http_request_chunk` (repeated)
  - `http_request_end`

- Elixir forwards these events (no reassembly).

- Python `BridgeClient` buffers request chunks keyed by `request_id`, reassembles the body string at `end`, then proxies to FastAPI exactly as today.

- For small responses, the server responds with `http_response` exactly as today.
- For large responses, the server responds with a new chunked response protocol:
  - `http_response_init`
  - `http_response_chunk` (repeated)
  - `http_response_end`

The TS `BridgeTransport` reassembles chunked responses and returns them to callers as a normal `{ status, data }` transport result.

### Protocol Details (v1)

All messages include `request_id` and `session_id`.

### Request chunking (app → bridge → server)

#### 1) `http_request_init`

Payload fields (suggested):

- `request_id`: UUID
- `session_id`: bridge session id
- `method`, `path`, `headers`
- `body_encoding`: `"utf8-json"` (body represents JSON text encoded as a UTF-8 string)
- `body_length_bytes`: total UTF-8 byte length (recommended)
- `chunk_size_bytes`: client chunk size (recommended)

#### 2) `http_request_chunk`

Payload fields (suggested):

- `request_id`
- `session_id`
- `seq`: integer starting at 0
- `chunk`: string (a slice of the full body string)

#### 3) `http_request_end`

Payload fields (suggested):

- `request_id`
- `session_id`
- `final_seq`: last sequence number (recommended)

Reply semantics:

- The app should await the reply to `http_request_init` and each `http_request_chunk` as a lightweight pacing mechanism.
  - This is the v1 “backpressure” mechanism: the client only sends the next chunk after the bridge has acknowledged receipt.
  - In v1 this ack is **Elixir-level** (it means “Elixir forwarded/broadcasted it”), not a durable “Python buffered it”.
- The app awaits the reply to `http_request_end` as the request’s terminal result.
  - For small responses, the reply should contain the normal `http_response` payload (as today).
  - For chunked responses, the reply should contain a small summary payload (see “Response chunking”) while the body arrives via `http_response_*` pushes.

### Backpressure / flow control (v1 decision)

For v1, use **per-message Phoenix request/reply as pacing**:

- TS uses `sendMessageRaw(...).await` for:
  - `http_request_init`
  - each `http_request_chunk`
  - `http_request_end`

This provides simple client-side backpressure without adding a new ACK event.

Future enhancement (not required for v1): add `http_request_chunk_ack` pushed from Python (durable buffering acknowledgement).

### Compatibility

- Keep existing `http_request` event working for small payloads.
- Add a threshold in `BridgeTransport`: if body size > N bytes, use chunked protocol.
- Server-side bridge client should accept both legacy and chunked requests.

Response compatibility:

- For small response bodies, keep sending legacy `http_response`.
- For large response bodies, send `http_response_init/chunk/end` and have TS reassemble.

## Component Changes

### 1) TS: `BridgeTransport` (frontend SDK)

Files:

- `packages/frontend-sdk/src/transport/bridgeTransport.ts`

Changes:

- Compute request body string exactly as today (`JSON.stringify(req.body)`).
- If body is large (> threshold):
  - send `http_request_init`
  - send chunk messages, awaiting the reply after each one (pacing)
  - send `http_request_end` and await reply

Add support for receiving and reassembling **chunked responses**:

- Extend the WebSocket `onmessage` handler to route *non-reply pushes* (messages that do not match an in-flight `ref`) into a per-`request_id` response assembler.
- Implement assemblers keyed by `request_id` that accept:
  - `http_response_init` (captures `status`, `headers`, expected total length if provided)
  - `http_response_chunk` (append by `seq`)
  - `http_response_end` (finalize and resolve)

When finalizing, parse response body as JSON when applicable, and return `{ status, data }`.

Recommendations:

- Make chunk size configurable (defaults: 16–64KB) and ensure each Phoenix frame stays comfortably below 1 MiB.
- Surface request timeout config:
  - `BridgeTransport.request` already accepts `timeoutMs`; ensure it applies to the entire chunked operation.

Response chunking threshold:

- Support response chunking whenever the response `body` string exceeds the same threshold used for requests (or a separate configurable value).

Also consider addressing correctness gap:

- Return real HTTP status and throw on non-2xx (match `FetchTransport` behavior).

Note: The end-to-end tests for this task only require `200` responses, but it is strongly recommended to make BridgeTransport status propagation correct while touching this code.

### 2) Elixir: forward chunked events

Files:

- `bridge-elixir/lib/bridge/app_channel.ex`
- `bridge-elixir/lib/bridge/server_channel.ex`

Changes:

- Add `handle_in` handlers in `Bridge.AppChannel` for:
  - `http_request_init`
  - `http_request_chunk`
  - `http_request_end`

Implementation concept:

- Lookup session (same as today) and broadcast to `tunnel:server:<server_id>`.
- Subscribe to `tunnel:request:<request_id>` at `http_request_init`.
- `http_request_init` and each `http_request_chunk` should reply quickly with `{:ok, %{}}` (pacing).
- `http_request_end` should broadcast the `end` event and then block/wait for the final response:
  - If a single `{:http_response, response}` arrives: reply with it as today.
  - If chunked response events arrive:
    - forward them to the app via `push(socket, "http_response_init"|"http_response_chunk"|"http_response_end", payload)` as they arrive
    - reply only after `http_response_end` has been forwarded.

Add forwarding of chunked response events in `Bridge.ServerChannel`:

- Add `handle_in` handlers for:
  - `http_response_init`
  - `http_response_chunk`
  - `http_response_end`
- These should broadcast to `tunnel:request:<request_id>` with distinct PubSub messages:
  - `{:http_response_init, payload}` / `{:http_response_chunk, payload}` / `{:http_response_end, payload}`

Update `Bridge.ServerChannel.handle_info/2` to push chunked request events to the server WebSocket connection:

- When `Bridge.AppChannel` broadcasts `{:http_request_init, ...}` / `{:http_request_chunk, ...}` / `{:http_request_end, ...}` to `tunnel:server:<server_id>`, the server channel should forward them as events `"http_request_init"`, `"http_request_chunk"`, `"http_request_end"`.

If implementing ACK:

- Accept `http_request_chunk_ack` from server-side and route it to app.

Timeouts:

- Make the `60_000` wait configurable (env var), because chunking increases end-to-end duration.

Recommended env vars (names are suggestions; implementer may choose repo-consistent names):

- `BRIDGE_HTTP_WAIT_TIMEOUT_MS` (default 120_000)

### 3) Python: `BridgeClient` buffering + reassembly

Files:

- `application/python/agent_terminal_app/bridge_client.py`

Changes:

- Extend `_handle_messages` to handle:
  - `http_request_init`: create buffer entry
  - `http_request_chunk`: append to list by `seq`
  - `http_request_end`: validate, reassemble full body string, proxy via httpx, respond

Add **response chunking** in Python:

- After proxying to FastAPI, decide whether to return:
  - legacy `http_response` (small body), OR
  - chunked `http_response_init/chunk/end` (large body)

Elixir remains a forwarder; TS reassembles responses.

Recommendations:

- Enforce size limits (max total bytes) with clear error response.
- Clean up buffers on:
  - completion
  - timeout waiting for next chunk
  - WS disconnect
- Update `websockets.connect` to set `max_size` to a higher value or `None`.
  - Even with chunking, you still need to accept chunk messages bigger than default.

Timeout alignment:

- Make `httpx` timeout configurable (and likely higher than 10s) for bridged requests.

Recommended env vars (names are suggestions; implementer may choose repo-consistent names):

- `BRIDGE_WS_MAX_SIZE_BYTES` (default e.g. 16_777_216; or allow `0`/empty for unlimited)
- `BRIDGE_HTTPX_TIMEOUT_S` (default 120)
- `BRIDGE_MAX_BODY_BYTES` (default 10_485_760)

### 4) Tests / validation

Add a targeted test plan:

- Elixir unit/integration tests:
  - Ensure init/chunk/end are forwarded and correlated by `request_id`.
- Python test mode:
  - Simulate a chunked request and verify reassembled body matches original.

#### End-to-end test (required; TS SDK → Elixir bridge → Python server → FastAPI)

Add a full E2E integration test that exercises the entire bridge stack for both:

- large request (forces request chunking)
- large response (forces response chunking)

Proposed implementation:

- New test file: `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts`
- Gate it behind an env var so it doesn’t run by default:
  - `RUN_BRIDGE_E2E_INTEGRATION=1`

Test orchestration (within the Vitest test):

1) Start the Elixir bridge service.
   - Preferred: Docker Compose (hermetic):
     - `docker compose -f bridge-elixir/docker-compose.single-node.yml up -d`
     - bridge WS URL: `ws://127.0.0.1:4000/ws/websocket` (adjust if compose differs)
   - Alternative (local dev): `cd bridge-elixir && mix phx.server` (requires Elixir deps).
   - The test should check readiness (e.g. attempt a WS join to an app topic, or reuse an existing “hello” style check if available).

2) Start the FastAPI backend server using the existing TS integration runner.
   - Reuse `scripts/run_backend_server_for_ts_integration_tests.py` (already used by `backend.integration.test.ts`).
   - Provide env vars so the Python server registers with the bridge automatically:
     - `BRIDGE_URL=ws://127.0.0.1:4000/ws/websocket`
     - `BRIDGE_SERVER_ID=<fixed id chosen by the test>`
     - optional: `BRIDGE_DISPLAY_NAME=Bridge E2E Test Server`

3) Pair TS to the Python server automatically.
   - Construct a `BridgeTransport({ bridgeUrl, serverId })`.
   - Wait until `transport.listServers()` includes the server id.
   - Call `transport.requestPairing(serverId)`.
   - Capture the pairing code by parsing the Python backend process stdout.
     - Python prints a stable banner including `PAIRING CODE: <code>`.
   - Call `transport.submitPairingCode(serverId, code)`.

4) Execute a large request + large response.
   - Use the existing FastAPI endpoints:
     - `PUT /api/data` (body is JSON)
     - `GET /api/data` (response is JSON)
   - Generate a payload that exceeds the chunk threshold (example: a single string field of ~0.8–2MB).
   - Assertions:
     - `PUT /api/data` returns `{ success: true, updated: { blob: <same string> } }`.
     - `GET /api/data` returns `{ success: true, data: { blob: <same string> } }`.

This ensures:

- TS request chunking works (large `PUT` body)
- Python request reassembly works (FastAPI receives one big JSON body)
- Python response chunking works (large `GET` response)
- TS response reassembly works (app receives full JSON)

Implementation notes for the harness:

- Extend the existing TS integration harness to:
  - spawn the backend with additional environment variables
  - capture backend stdout (for pairing code parsing)
  - optionally start/stop docker compose for the bridge

## Recommendations / Defaults

- Chunk size default: 32KB.
- Chunking threshold: 256KB (UTF-8 bytes of JSON string).
- Max total body size (bridge): start with 10MB configurable.
- Align timeouts:
  - BridgeTransport default: >= 120s for chunked requests/responses
  - Elixir wait timeout: configurable, >= 120s
  - Python httpx timeout: configurable, >= 120s for bridged calls

## Open Questions

1) ACK/backpressure: v1 uses per-message `phx_reply` pacing (Elixir-level ack). Do we also want a Python-level `http_request_chunk_ack` in v2?
2) Concurrency: allow multiple concurrent chunked requests per app connection, or enforce one at a time (recommended for v1)?
3) Ordering: assume in-order delivery per WebSocket, but still validate `seq` and `final_seq` to catch protocol bugs.
4) Error handling:
  - How should Python indicate mid-upload errors (oversize, invalid seq)?
  - Recommended v1: return an error reply to `http_request_end` (so the initiating TS call rejects).
5) Status propagation:
  - Strongly recommended: fix `BridgeTransport` to return real HTTP status and throw on non-2xx.
6) Security limits:
  - What max payload size is acceptable by default?
  - Should size caps vary by endpoint (append vs send)?

---

## Implementation Notes (added 2026-02-16)

This subtask was implemented end-to-end (TS SDK → Elixir bridge → Python BridgeClient → FastAPI) with both **request chunking** and **response chunking**, plus a Docker-based E2E test.

### Protocol implemented

- **Request chunking (app → bridge → server)**
  - `http_request_init` (reply `{:ok, ...}`)
  - `http_request_chunk` (reply `{:ok, ...}`; used as simple pacing/backpressure)
  - `http_request_end` (blocks for terminal result)
- **Response chunking (server → bridge → app)**
  - `http_response_init` (pushed to app socket)
  - `http_response_chunk` (pushed to app socket)
  - `http_response_end` (pushed to app socket)
  - The `phx_reply` to the terminal request (`http_request` or `http_request_end`) returns a small summary payload:
    - `%{type: "http_response_chunked", request_id: request_id}`

Elixir remains a forwarder (no reassembly).

### TypeScript (frontend-sdk) implementation

- File: `packages/frontend-sdk/src/transport/bridgeTransport.ts`
- Implemented:
  - Threshold-based request body chunking.
  - Chunked response reassembly keyed by `request_id` via WebSocket pushes.
  - Correct HTTP status propagation + error behavior (throws on non-2xx, similar to `FetchTransport`).
  - Debug logging hooks (opt-in) and stronger timeout/error messages including `HTTP <METHOD> <PATH>` + phase.
  - Added cleanup of in-flight chunked response assemblers (`streamingResponses`) on request errors/timeouts to reduce **unhandled promise rejections** (“uncaught in promise”).
    - **Note:** A separate unhandled rejection scenario still exists due to how `BridgeTransport` currently creates a "streaming response" promise + timeout even for legacy (non-chunked) requests (see **P0.1** below).
- **Deviation from the suggested defaults:** chunk size default was increased to ~900 KiB (instead of 32 KiB) to keep each Phoenix message under ~1 MiB while minimizing chunk count for 10–15 MiB payloads.

### Elixir bridge implementation

- Files:
  - `bridge-elixir/lib/bridge/app_channel.ex`
  - `bridge-elixir/lib/bridge/server_channel.ex`
- Implemented:
  - `Bridge.AppChannel` now handles `http_request_init/chunk/end` and forwards them to the paired server via PubSub.
  - `Bridge.ServerChannel` forwards `http_request_init/chunk/end` to server WebSocket clients.
  - `Bridge.ServerChannel` accepts `http_response_init/chunk/end` and broadcasts them to `tunnel:request:<request_id>`.
  - `Bridge.AppChannel` waits for and forwards `http_response_init/chunk/end` to the app via `push/3` and only replies after the terminal response has completed.
  - Timeout made configurable and increased for chunked flows.
- **Deviation from suggested env var name:** implemented `BRIDGE_HTTP_TIMEOUT_MS` (default `120_000`) instead of `BRIDGE_HTTP_WAIT_TIMEOUT_MS`.

### Python (agent_terminal_app) implementation

- File: `application/python/agent_terminal_app/bridge_client.py`
- Implemented:
  - WebSocket `max_size` is explicitly configured (default 16 MiB) to avoid the Python `websockets` default 1 MiB limit.
  - Chunked request buffering keyed by `request_id` with strict `seq` validation and a max body size cap.
  - Local proxy timeout is configurable and defaulted higher (120s) for bridged calls.
  - Response chunking: large `resp.text` bodies are emitted as `http_response_init/chunk/end`.
  - Correctness fix from the plan: proxied request headers are now forwarded (legacy and chunked). Content-Type is only defaulted when missing.
  - Debug print statements gated by `BRIDGE_DEBUG=1`.
- Env vars implemented (names differ slightly from the draft suggestions):
  - `BRIDGE_WS_MAX_SIZE_BYTES` (default `16 * 1024 * 1024`)
  - `BRIDGE_HTTP_TIMEOUT_SECONDS` (default `120.0`)
  - `BRIDGE_HTTP_CHUNK_SIZE_BYTES` (default `900 * 1024`)
  - `BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES` (default `256 * 1024`)
  - `BRIDGE_HTTP_MAX_BODY_BYTES` (default `10 * 1024 * 1024`)
  - `BRIDGE_DEBUG` (`1/true/yes` enables prints)

### Tests added

- TS unit tests:
  - `packages/frontend-sdk/src/transport/bridgeTransport.test.ts`
- Elixir unit test (focused on response chunk forwarding):
  - `bridge-elixir/test/bridge/server_channel_chunked_http_test.exs`
- Python unit tests:
  - `application/python/tests/test_bridge_client_chunked_http.py`
- Required E2E test (Docker bridge + real FastAPI backend):
  - `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts`
  - Harness additions for Docker orchestration + stdout pairing-code parsing:
    - `packages/frontend-sdk/src/integration/harness.ts`
  - Vitest parallelism was disabled for integration runs to avoid race conditions between the backend integration suite and the bridge Docker lifecycle:
    - `packages/frontend-sdk/vitest.config.ts`

### Additional (out-of-scope) change made alongside this task

- Added `agent_terminal_app` CLI support for routing uvicorn/FastAPI logs to a separate file when running server+console:
  - `--fastapi-log-file <path>`
  - Files: `application/python/agent_terminal_app/__main__.py`, `application/python/agent_terminal_app/server.py`

### Items from the plan that were *not* implemented

- No Python-level durable ACK (`http_request_chunk_ack`) – v1 uses Elixir-level `phx_reply` pacing only.
- No explicit per-request buffer timeout/cleanup for “stalled uploads” (e.g. init received but end never arrives). Buffers are cleaned on completion; protocol errors clear the buffer for that `request_id`.
- No explicit “single in-flight chunked request” enforcement (multiple `request_id`s can be buffered concurrently).
- No per-endpoint max payload policies; a single global `BRIDGE_HTTP_MAX_BODY_BYTES` cap is enforced.
- Elixir tests cover `ServerChannel` chunked response forwarding, but there is not a dedicated Elixir unit test for `AppChannel` chunked request forwarding/pacing behavior.

### Follow-up implementation plan (prioritized; required for production/mobile reliability)

This section is written as a handoff plan for an agent to complete the remaining work.

#### Background: mobile `/events` polling + screen-off issues

The React Native app uses the chat controller event polling loop which calls `GET /events` roughly every second.

When the phone screen turns off, React Native can pause the JavaScript thread. If a bridged `/events` request is in-flight, it may not resolve until the configured timeout. With the current 120s default timeout for bridged HTTP requests, this causes two user-visible issues:

- **Problem 1 (lower priority):** when the screen turns back on, polling may not resume until the previous request finishes timing out.
- **Problem 2 (higher priority):** when that timeout fires, React Native can show an **"unhandled promise rejection"** style error instead of surfacing it as a normal caught error / popup.

Root cause (high confidence): `BridgeTransport.request()` currently creates an internal "streaming response" promise + timeout (`createStreamingResponsePromise`) for *every* request, including legacy (non-chunked) requests like `GET /events`. That promise can reject on its own timer even when the main request promise is still pending, and it is not always awaited/handled.

Relevant code to read:

- `packages/frontend-sdk/src/transport/bridgeTransport.ts:125` (request flow)
- `packages/frontend-sdk/src/transport/bridgeTransport.ts:149` (creates `responsePromise` unconditionally)
- `packages/frontend-sdk/src/transport/bridgeTransport.ts:457` (createStreamingResponsePromise + timer)
- `packages/frontend-sdk/src/events/pollingEventSource.ts:64` and `packages/frontend-sdk/src/events/pollingEventSource.ts:76` (poll loop is sequential; no cancellation)
- `packages/frontend-sdk/src/chat/chatController.ts:258` and `packages/frontend-sdk/src/chat/chatController.ts:287` (starts/stops polling)
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:253` (`eventsEnabled` gating; currently not tied to app background/foreground)

#### P0 (must-fix)

These items should be completed before treating bridge chunking as stable for mobile.

1) **Fix unhandled promise rejection in TS `BridgeTransport`**
   - Goal: ensure no internal promise created by `BridgeTransport.request()` can reject "unhandled".
   - Files:
     - `packages/frontend-sdk/src/transport/bridgeTransport.ts:125`
     - `packages/frontend-sdk/src/transport/bridgeTransport.ts:457`
   - Suggested approaches (pick one):
     - **Minimal safety:** immediately attach a no-op handler to `responsePromise` (e.g. `responsePromise.catch(() => {})`) so it can never be unhandled.
     - **Better design:** only create/start the streaming response timer once a chunked response is confirmed (e.g. after receiving `http_response_init` push or a `{type:"http_response_chunked"}` reply).
   - Add a regression test if possible:
     - `packages/frontend-sdk/src/transport/bridgeTransport.test.ts` (listen for `process.on('unhandledRejection', ...)` during the test, trigger the timeout, and assert it does not fire).

2) **Fail fast for in-flight requests on WebSocket close/error (TS)**
   - Goal: if the WS closes (or app goes background and we deliberately close), all pending requests should reject immediately (not after 120s).
   - Files:
     - `packages/frontend-sdk/src/transport/bridgeTransport.ts:370` (`ws.onclose`)
     - `packages/frontend-sdk/src/transport/bridgeTransport.ts:399` (`sendMessageRaw`, `responseHandlers`)
     - `packages/frontend-sdk/src/transport/bridgeTransport.ts:497` (`streamingResponses`)
   - Implementation notes:
     - Today `responseHandlers` stores callbacks; refactor so you can reject all pending refs on close, or synthesize a failure reply into each handler.
     - For `streamingResponses`, iterate all entries, `clearTimeout(timeoutId)`, and call `reject(new Error("Connection closed"))`.

3) **Mobile: stop/restart event polling on app background/foreground**
   - Goal: avoid waiting for a long `/events` timeout when the JS thread resumes; polling should resume promptly.
   - Files:
     - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:253` (current `eventsEnabled`)
     - `packages/frontend-sdk-react/src/useChatController.ts:73` and `packages/frontend-sdk-react/src/useChatController.ts:99` (starts/stops streaming based on `eventsEnabled`)
   - Implementation notes:
     - Add a React Native `AppState` listener and incorporate it into the `eventsEnabled` computation.
     - Optional but recommended: on background **disconnect** the `BridgeTransport` (if in use) so any in-flight request fails immediately once P0.2 is implemented.
     - On resume, reconnect (or rely on `ensureConnected()` to reconnect on demand) and restart streaming.

4) **Shorten `/events` timeout without shortening upload timeouts**
   - Goal: keep 120s+ timeouts for large requests/responses, but keep `/events` polling fast.
   - Mechanism: use `BridgeTransport.timeoutMsByPathPrefix`.
   - Files:
     - `mobile/crystal-lattice-control-rn/App.tsx:497` (bridge connect flow)
     - `mobile/crystal-lattice-control-rn/App.tsx:912` (reconnect saved bridge connection)
     - `packages/frontend-sdk/src/transport/bridgeTransport.ts:75` and `packages/frontend-sdk/src/transport/bridgeTransport.ts:666` (supports `timeoutMsByPathPrefix`)
   - Suggested default:
     - `/events` timeout: 5s–15s (choose based on expected latency)

#### P1 (high priority hardening)

5) **Heartbeat / WS idle timeout alignment (Elixir + clients)**
   - Problem: Phoenix WS endpoint uses `timeout: 45_000` (`bridge-elixir/lib/bridge/endpoint.ex:6`). Long-running flows can exceed this if no messages are sent.
   - Options:
     - Add Phoenix `heartbeat` messages from TS + Python clients.
     - Or increase the endpoint websocket timeout to exceed the max request timeout.
   - Files:
     - `bridge-elixir/lib/bridge/endpoint.ex:6`
     - `packages/frontend-sdk/src/transport/bridgeTransport.ts` (WS connection)
     - `application/python/agent_terminal_app/bridge_client.py` (WS connection loop)

6) **Python: fix env parsing helpers**
   - `BRIDGE_WS_MAX_SIZE_BYTES` currently cannot be set reliably due to `_parse_optional_int`.
   - Files:
     - `application/python/agent_terminal_app/bridge_client.py:666` (`_parse_optional_int`)
     - `application/python/agent_terminal_app/bridge_client.py:671` (`_parse_float`)

7) **Python: stalled chunked request cleanup / TTL**
   - Files:
     - `application/python/agent_terminal_app/bridge_client.py:105` (`_chunked_requests`)
   - Implement:
     - Drop stale entries after N seconds.
     - Clear all buffered requests on WS disconnect/reconnect.
     - Optional: cap concurrent buffered requests.

#### P2 (robustness / v2 improvements; ok to do after P0/P1)

These items overlap with the earlier "not implemented" list above and are kept here as actionable backlog.

8) **Size-aware chunking based on actual serialized Phoenix message size**
   - Implement in TS request chunking and Python response chunking.

9) **Head-of-line blocking mitigation**
   - Current Elixir `handle_in` blocks while waiting for responses (`bridge-elixir/lib/bridge/app_channel.ex:17` and `bridge-elixir/lib/bridge/app_channel.ex:297`).
   - Options:
     - Client-side single in-flight queue.
     - Protocol change: always reply `accepted` and deliver responses only via pushes.

10) **Stricter response chunk ordering + better error reporting (TS)**
   - Make out-of-order chunks fail fast with a clear error (instead of ignoring and timing out).

11) **Durable ACK (`http_request_chunk_ack`) (optional v2)**
   - Not required for v1; consider if we need Python-level durable buffering acknowledgement.

12) **More Elixir tests**
   - Add a unit test for `Bridge.AppChannel` chunked request forwarding/pacing.

13) **Per-endpoint size policies**
   - Currently only a global `BRIDGE_HTTP_MAX_BODY_BYTES` cap exists.
   - Consider different caps for `/events` vs `/sessions/.../messages` vs `/send`.

## Follow-up status audit (added 2026-04-08)

This section records the current implementation status of the follow-up plan above based on repository inspection after the original handoff was written.

### Completed since the handoff

#### P0.1 `BridgeTransport`: prevent unhandled promise rejection

- Implemented with the "minimal safety" approach.
- `BridgeTransport.request()` still creates the internal streaming-response promise up front, but now immediately attaches a no-op `.catch()` so its timeout cannot surface as an unhandled rejection:
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts:160`
- Regression test added:
  - `packages/frontend-sdk/src/transport/bridgeTransport.test.ts:219`

#### P0.2 `BridgeTransport`: fail fast on WebSocket close/error

- Implemented.
- Pending reply handlers and streaming response assemblers are now rejected on:
  - explicit `disconnect()`
    - `packages/frontend-sdk/src/transport/bridgeTransport.ts:126`
  - `ws.onerror`
    - `packages/frontend-sdk/src/transport/bridgeTransport.ts:400`
  - `ws.onclose`
    - `packages/frontend-sdk/src/transport/bridgeTransport.ts:415`
- Supporting helpers:
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts:434`
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts:451`
- Regression test added:
  - `packages/frontend-sdk/src/transport/bridgeTransport.test.ts:251`

#### P0.3 Mobile: stop/restart event polling on app background/foreground

- Implemented.
- `SessionChatScreen` now tracks React Native `AppState` and includes it in `eventsEnabled`:
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:184`
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:347`
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:356`
- `useChatController` already stops polling when `eventsEnabled` becomes false and restarts when it becomes true:
  - `packages/frontend-sdk-react/src/useChatController.ts:70`
- The optional follow-up from the plan was also implemented: bridge transports are disconnected when the app backgrounds:
  - `mobile/crystal-lattice-control-rn/App.tsx:137`

#### P0.4 Shorten `/events` timeout without shortening upload timeouts

- Implemented.
- Bridge connection setup now passes a shorter timeout for `/events` using `timeoutMsByPathPrefix`:
  - `mobile/crystal-lattice-control-rn/App.tsx:522`
  - `mobile/crystal-lattice-control-rn/App.tsx:941`
- Current configured timeout: `10_000` ms.

#### P1.6 Python: env parsing helpers

- Appears implemented in code.
- `BRIDGE_WS_MAX_SIZE_BYTES` still flows through `_parse_optional_int`, and the helper now simply returns `int(value)` or the default:
  - `application/python/agent_terminal_app/bridge_client.py:853`
  - `application/python/agent_terminal_app/bridge_client.py:868`
- `_parse_float` follows the same straightforward pattern:
  - `application/python/agent_terminal_app/bridge_client.py:883`
- No dedicated regression test for this helper behavior was found during this review.

### Partially completed

#### P0.1 `BridgeTransport` cleanup/design improvement

- The immediate bug is mitigated, but the cleaner design proposed in the plan was not implemented.
- `BridgeTransport.request()` still creates the streaming-response promise for every request, including legacy non-chunked requests:
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts:160`
- The current status is therefore:
  - unhandled rejection symptom: fixed
  - unnecessary always-on streaming-response promise/timer: still present

#### P2.10 Stricter response chunk ordering + better error reporting

- Partially implemented.
- Invalid `final_seq` fails fast with a clear error:
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts:628`
- But out-of-order chunks are still ignored rather than rejected immediately:
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts:607`
- That means the "fail fast on out-of-order chunk" part remains open.

#### P2.12 More Elixir tests

- Partially implemented.
- There is now an Elixir test covering `Bridge.AppChannel` forwarding of `http_request_init` to the active server:
  - `bridge-elixir/test/bridge/single_target_routing_test.exs:100`
- However, there is still no dedicated unit test covering the full chunked request pacing flow (`http_request_chunk`) and terminal `http_request_end` behavior in `Bridge.AppChannel`.

### Still remaining

#### P1.5 Heartbeat / WS idle timeout alignment

- Still open.
- Phoenix endpoint websocket timeout is still `45_000`:
  - `bridge-elixir/lib/bridge/endpoint.ex:4`
- No TS or Python heartbeat mechanism was found during this review.

#### P1.7 Python: stalled chunked request cleanup / TTL

- Still open.
- `_chunked_requests` remains an in-memory dictionary with normal add/pop behavior only:
  - `application/python/agent_terminal_app/bridge_client.py:114`
- No TTL, stale-request scavenging, or explicit "clear all buffered requests on disconnect/reconnect" logic was found.

#### P2.8 Size-aware chunking based on actual serialized Phoenix message size

- Still open.
- TS still uses approximate string slicing with headroom:
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts:724`
- Python response chunking likewise uses approximate chunking rather than measuring actual serialized Phoenix payload size:
  - `application/python/agent_terminal_app/bridge_client.py:586`

#### P2.9 Head-of-line blocking mitigation

- Still open.
- `Bridge.AppChannel` still blocks inside `await_http_response/2` while waiting for the proxied response:
  - `bridge-elixir/lib/bridge/app_channel.ex:27`

#### P2.11 Durable ACK (`http_request_chunk_ack`)

- Still open.
- No `http_request_chunk_ack` protocol support was found during this review.

#### P2.13 Per-endpoint size policies

- Still open.
- The Python bridge client still exposes only a single global body-size cap:
  - `application/python/agent_terminal_app/bridge_client.py:66`

### Summary

At the time of this audit:

- The original "must-fix" follow-up items (`P0`) are effectively complete, with `P0.1` solved via the minimal safety fix rather than the more structural redesign.
- `P1` is partially complete: env parsing helpers look fixed, but heartbeat/idle-timeout alignment and stalled-buffer cleanup remain open.
- `P2` remains mostly backlog, with partial progress on response validation and Elixir test coverage.

This audit was based on task-file and code inspection only; no test suite was executed as part of the review.

## Overlap with newer task set (added 2026-04-08)

There is limited overlap with the newer connection-recovery task set:

- `tasks/20260408-connection-recovery/010-transport-reliability-and-recovery.md`
  - Expected completion path for remaining item `P1.5 Heartbeat / WS idle timeout alignment`
  - Partial overlap with remaining item `P1.7 Python: stalled chunked request cleanup / TTL`
- `tasks/20260408-connection-recovery/020-mobile-resume-lifecycle-and-chat-recovery.md`
  - No substantial overlap with the still-remaining bridge chunking backlog in this file

Interpretation:

- If `010` is completed with bridge heartbeat / idle-timeout alignment work, `P1.5` should be considered completed via that task.
- `P1.7` should remain open unless the `010` implementation explicitly includes Python-side chunk-buffer TTL / stale-request scavenging and disconnect cleanup.



