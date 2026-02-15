# Bridge: Chunked HTTP request bodies over Phoenix WebSockets (large base64 attachments)

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Support large JSON payloads (notably base64-encoded attachments inside `multipartContent`) when using the Elixir bridge transport by introducing an application-level chunking protocol for proxied HTTP requests over Phoenix Channels.

The goal is that:

- Mobile/desktop code continues to call the backend as if it is making a single HTTP request with a large JSON body.
- FastAPI continues to receive a single HTTP request with the full (reassembled) JSON body.
- The intermediary bridge layers (TS `BridgeTransport`, Elixir channels, Python `BridgeClient`) break the body into multiple smaller WebSocket messages and reassemble it.

Elixir should remain a simple forwarder (no reassembly in Elixir), but it must be updated to forward new events.

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

## Proposed Approach (Recommended)

### Overview

Introduce a new chunked request protocol while maintaining compatibility with the existing `http_request` event.

- App (TS) splits the HTTP body into chunks and sends:
  - `http_request_init`
  - `http_request_chunk` (repeated)
  - `http_request_end`

- Elixir forwards these events (no reassembly).

- Python `BridgeClient` buffers chunks keyed by `request_id`, reassembles the body string at `end`, then proxies to FastAPI exactly as today.

- The server responds with `http_response` exactly as today.

### Protocol Details (v1)

All messages include `request_id` and `session_id`.

1) `http_request_init`

Payload fields (suggested):

- `request_id`: UUID
- `session_id`: bridge session id
- `method`, `path`, `headers`
- `body_encoding`: `"json"` (body represents JSON text)
- `body_length`: total UTF-8 byte length (optional but recommended)
- `chunk_size`: client chunk size (optional)

2) `http_request_chunk`

Payload fields (suggested):

- `request_id`
- `seq`: integer starting at 0
- `chunk`: string (a slice of the full body string)

3) `http_request_end`

Payload fields (suggested):

- `request_id`
- `final_seq`: last sequence number (optional but recommended)

Reply semantics:

- The app only awaits the reply to `http_request_end`.
- Elixir implements the same `receive ... after 60_000` wait, but associated with the `request_id` and triggered from `end`.

### Backpressure / flow control (strongly recommended)

Without flow control, large chunk streams can overwhelm:

- WebSocket internal buffers
- Elixir channel mailbox
- Python process memory

Recommended simple ACK protocol:

- App sends `http_request_chunk`.
- Server-side bridge client (Python) pushes `http_request_chunk_ack` back (via Elixir forward) when chunk is buffered.
- App sends next chunk only after ack.

This requires Elixir to forward `http_request_chunk_ack` from server to app on the request topic.

If implementing ACK feels too heavy for v1, enforce a strict "single in-flight chunked request" and a conservative chunk size (e.g. 16KB) and accept some risk.

### Compatibility

- Keep existing `http_request` event working for small payloads.
- Add a threshold in `BridgeTransport`: if body size > N bytes, use chunked protocol.
- Server-side bridge client should accept both legacy and chunked requests.

## Component Changes

### 1) TS: `BridgeTransport` (frontend SDK)

Files:

- `packages/frontend-sdk/src/transport/bridgeTransport.ts`

Changes:

- Compute request body string exactly as today.
- If body is large (> threshold):
  - send `http_request_init`
  - send chunk messages (with optional ack)
  - send `http_request_end` and await reply

Recommendations:

- Make chunk size configurable (defaults: 16–64KB) and ensure each Phoenix frame stays comfortably below 1 MiB.
- Surface request timeout config:
  - `BridgeTransport.request` already accepts `timeoutMs`; ensure it applies to the entire chunked operation.

Also consider addressing correctness gap:

- Return real HTTP status and throw on non-2xx (match `FetchTransport` behavior).

### 2) Elixir: forward chunked events

Files:

- `bridge-elixir/lib/bridge/app_channel.ex`
- `bridge-elixir/lib/bridge/server_channel.ex`

Changes:

- Add `handle_in` handlers for:
  - `http_request_init`
  - `http_request_chunk`
  - `http_request_end`

Implementation concept:

- Lookup session (same as today) and broadcast to `tunnel:server:<server_id>`.
- Subscribe to `tunnel:request:<request_id>` at init.
- Only block/wait for final response on `end`.

If implementing ACK:

- Accept `http_request_chunk_ack` from server-side and route it to app.

Timeouts:

- Make the `60_000` wait configurable (env var), because chunking increases end-to-end duration.

### 3) Python: `BridgeClient` buffering + reassembly

Files:

- `application/python/agent_terminal_app/bridge_client.py`

Changes:

- Extend `_handle_messages` / `_handle_http_request` to handle:
  - init: create buffer entry
  - chunk: append to list by seq
  - end: validate, reassemble full body string, proxy via httpx, respond

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

### 4) Tests / validation

Add a targeted test plan:

- Elixir unit/integration tests:
  - Ensure init/chunk/end are forwarded and correlated by `request_id`.
- Python test mode:
  - Simulate a chunked request and verify reassembled body matches original.
- End-to-end (optional):
  - Create a test that sends a large JSON body via `BridgeTransport` and verify FastAPI receives it.

## Recommendations / Defaults

- Chunk size default: 32KB.
- Chunking threshold: 256KB (body size above this uses chunking).
- Max total body size (bridge): start with 10MB configurable.
- Align timeouts:
  - BridgeTransport default: >= 120s for chunked requests
  - Elixir wait timeout: configurable, >= 120s
  - Python httpx timeout: configurable, >= 120s for `/send` and maybe less for append

## Open Questions

1) ACK/backpressure: do we require chunk ACK for v1 or accept best-effort sending?
2) Concurrency: allow multiple concurrent chunked requests per connection, or enforce one at a time?
3) Ordering: is out-of-order chunk delivery possible in Phoenix channels? (Typically ordered per connection, but don’t assume; seq validation is still recommended.)
4) Error responses:
  - How should the server indicate mid-upload errors (oversize, invalid seq)?
  - Should errors be returned as a reply to `http_request_end` or as an async push?
5) Status propagation:
  - Should we fix `BridgeTransport` to return real HTTP status as part of this task?
6) Security limits:
  - What max payload size is acceptable?
  - Should size caps vary by endpoint (append vs send)?
