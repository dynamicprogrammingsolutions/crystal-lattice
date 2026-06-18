# Bridge Concurrent Proxied Requests

Fix bridge request head-of-line blocking so independent proxied HTTP requests from one app client can progress concurrently instead of serializing behind the first pending response.

## Requirements checklist

- [x] Try to keep the bridge WebSocket protocol between the SDK and bridge unchanged.
- [x] Change the bridge app channel so `http_request` handling does not block the channel process while waiting for the server response.
- [x] Apply the same concurrency model to chunked request/response paths.
- [x] Preserve timeout handling, PubSub unsubscribe cleanup, request correlation, and server-not-found behavior.
- [x] Add tests proving a slow proxied request does not block a later fast proxied request on the same app channel.
- [x] Add or update the SDK-facing bridge E2E test for concurrent proxied requests.
- [x] Rerun all existing SDK-facing bridge E2E cases.
- [x] Rerun cheap `BridgeTransport` unit tests; if the SDK protocol/client code does not change, these may be redundant but should still be inexpensive.
- [x] Add or update bridge/Python bridge-client tests needed by the implementation.

Parent Task: tasks/20260610-mobile-message-refresh-performance/000-main.md

## Background

This is the first and highest-priority fix. In bridge mode, mobile refresh can send multiple requests close together. The bridge currently handles one proxied HTTP request and waits for its response before the channel can process the next incoming request from that app.

Relevant code:

- `bridge-elixir/lib/bridge/app_channel.ex`
  - `handle_in("http_request", ...)` forwards to the server and calls `await_http_response(socket, request_id)` before returning.
  - `handle_in("http_request_end", ...)` does the same for chunked request completion.
  - `await_http_response/2` receives response messages and only then returns the channel reply.
- `bridge-elixir/lib/bridge/server_channel.ex`
  - Forwards `http_request`, `http_request_init`, `http_request_chunk`, and `http_request_end` messages to the Python server channel.
- `application/python/agent_terminal_app/bridge_client.py`
  - Handles bridge-originated requests and sends `http_response`, `http_response_init`, `http_response_chunk`, and `http_response_end` back.

Observed behavior:

- A single bridged full `/messages` request was acceptable locally, about 0.32s.
- A burst of schema/settings requests followed by `/messages` on one app WebSocket delayed the message response start until about 2.09s after the message request was sent.
- The measured reply order was all schema/settings requests first, then the messages request, confirming app-channel head-of-line blocking.

## Implementation Guidance

Prefer a design where the channel quickly accepts and forwards each HTTP proxy request, then uses an async task/process or explicit pending-request state to complete the response later. The implementation must keep per-request correlation by `request_id`.

For non-chunked responses, the channel may use Phoenix async replies, push response messages, or another local process that owns the waiting receive. For chunked responses, the current client expects pushed `http_response_init/chunk/end` messages followed by a final reply indicating `type: "http_response_chunked"`.

Try to preserve the protocol between bridge and SDK. If the protocol must change to make concurrency correct, it is acceptable to adjust the SDK in the same task because there are no other external bridge clients yet. In that case, the SDK-facing E2E tests must prove the externally supported SDK behavior remains correct.

Tests should include:

- A slow request through the bridge followed immediately by a fast request on the same app channel. The fast request must complete before the slow request.
- A large chunked response still arrives in sequence and completes successfully.
- Timeout cleanup unsubscribes the PubSub topic and does not poison later requests.

SDK-facing E2E coverage:

- Existing suite: `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts`.
- Existing cases in that suite should all be rerun:
  - `supports large request + large response bodies`
  - `reconnects and resumes after the bridge restarts`
- Add a new case in the same suite:
  - `allows a fast proxied request to complete while an earlier slow request is pending`
  - Suggested shape: pair a real `BridgeTransport`, send `GET /__test/sleep?ms=500`, immediately send `GET /api/hello`, and assert `/api/hello` completes before the slow request.

Likely test locations:

- `bridge-elixir/test/bridge/app_channel_resume_test.exs`
- `bridge-elixir/test/bridge/server_channel_chunked_http_test.exs`
- `packages/frontend-sdk/src/transport/bridgeTransport.test.ts` if SDK behavior needs to be adjusted or guarded.
- `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts` for the required SDK-facing concurrency case.

Verification commands to consider:

- `cd packages/frontend-sdk && npm run integration:bridge`
- `cd packages/frontend-sdk && npm test -- src/transport/bridgeTransport.test.ts`
- `cd bridge-elixir && mix test`
- Relevant Python bridge-client tests, for example `pytest application/python/tests/test_bridge_client_chunked_http.py application/python/tests/test_bridge_client_local_request.py -q`

## Execution plan

Added during task completion after user approval.

Use a staged checkpoint implementation. First fix the Elixir app-channel wait model and prove it with bridge-local tests. Then fix the Python bridge client receive loop so the real SDK E2E path benefits. Finally add the SDK-facing concurrent request test and rerun the requested suites.

## Task checklist

- [x] Add the approved execution plan to this task file before implementation.
- [x] Add supervised async response waiters in `Bridge.AppChannel`.
- [x] Preserve current bridge protocol events and replies.
- [x] Preserve server-not-found and invalid-session behavior.
- [x] Preserve PubSub unsubscribe cleanup for success, timeout, send failure, channel shutdown, and worker shutdown.
- [x] Ensure every accepted proxied request receives exactly one final reply via `reply(socket_ref, ...)`.
- [x] Subscribe each waiter to `tunnel:request:<request_id>` before forwarding to avoid missing fast responses.
- [x] Apply async waiter behavior to both `http_request` and `http_request_end`.
- [x] Keep worker processes from calling `push/3` directly; send push/reply instructions back to the app channel.
- [x] Add a small shared helper for starting async waiters so full and chunked completion paths do not drift apart.
- [x] Add a bounded concurrency guard or task tracking for app-channel waiters.
- [x] Add Elixir tests proving a fast full request completes while an earlier slow full request is pending on the same app channel.
- [x] Add Elixir tests proving chunked request completion does not block a later fast request.
- [x] Add Elixir tests proving chunked response init/chunk/end still arrives in order and final reply completes.
- [x] Add Elixir timeout cleanup regression coverage.
- [x] Make Python `BridgeClient` dispatch local request execution concurrently.
- [x] Keep Python `http_request_init` and `http_request_chunk` inline to preserve chunk buffer ordering.
- [x] Add Python WebSocket send serialization so concurrent response tasks keep per-request response frame order.
- [x] Add Python in-flight task cleanup on connection close, superseded, and stop.
- [x] Ensure chunked request completion pops each request exactly once and clears failure paths.
- [x] Add Python tests for full and chunked slow-then-fast bridge-client behavior.
- [x] Add SDK bridge E2E test for `GET /__test/sleep` followed by `GET /api/hello` on the same `BridgeTransport`.
- [x] Run `cd bridge-elixir && mix test`.
- [x] Run `pytest application/python/tests/test_bridge_client_chunked_http.py application/python/tests/test_bridge_client_local_request.py -q`.
- [x] Run `cd packages/frontend-sdk && npm test -- src/transport/bridgeTransport.test.ts`.
- [x] Run `cd packages/frontend-sdk && npm run integration:bridge`.
- [x] Mark task requirements complete and add completion notes after implementation and verification.

Implementation notes:

- In Elixir, use `Phoenix.Channel.socket_ref/1` and `Phoenix.Channel.reply/2` for asynchronous replies. A worker should subscribe before forwarding, then wait for response PubSub events or timeout. It should send channel-owned push instructions back to `Bridge.AppChannel.handle_info/2`; it must not call `push/3` directly.
- The app channel should return `{:noreply, socket}` only after a worker has accepted ownership of the final reply path. Client `BridgeTransport.sendMessage()` depends on exactly one final `phx_reply` for each original push.
- In Python, `_handle_messages()` should keep reading WebSocket messages while long local HTTP requests are pending. Dispatch `http_request` and `http_request_end` work into tracked tasks, but keep `http_request_init` and `http_request_chunk` inline.
- Protect WebSocket sends in Python with a lock. Holding the lock for the whole chunked response send is acceptable and keeps `init -> chunks -> end` contiguous for a request; response interleaving across request IDs is not required for correctness.

## Completion Notes

Added during task completion.

Implemented bridge proxy concurrency without changing the SDK-facing WebSocket protocol. `Bridge.AppChannel` now starts supervised response waiters for full requests and chunked request completion, while the channel process remains free to accept later app messages. Waiters subscribe before forwarding, preserve timeout replies and PubSub cleanup, and send push/reply instructions back to the app channel so `push/3` remains channel-owned.

Updated the Python `BridgeClient` to keep reading bridge WebSocket events while local HTTP requests are pending. Full requests and completed chunked requests now run in tracked tasks; chunk init/chunk ingestion remains inline. Response sends are serialized with a lock so each chunked response keeps `init -> chunks -> end` ordering.

Added Elixir, Python, and SDK E2E regression coverage for slow-then-fast proxied requests. Also fixed the frontend integration harness so bridge E2E backends set `SERVER_PORT`/`BRIDGE_LOCAL_HTTP_BASE` to the random test server port and Docker-mode bridge E2E rebuilds the local bridge image.

Verification completed:

- `cd bridge-elixir && mix test`
- `PYTHONPATH=/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/010-bridge-concurrent-proxied-requests/application/python:/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/010-bridge-concurrent-proxied-requests/core/python pytest application/python/tests/test_bridge_client_chunked_http.py application/python/tests/test_bridge_client_local_request.py -q`
- `cd packages/frontend-sdk && npm test -- src/transport/bridgeTransport.test.ts`
- `PYTHONPATH=/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/010-bridge-concurrent-proxied-requests/application/python:/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/010-bridge-concurrent-proxied-requests/core/python npm run integration:bridge`