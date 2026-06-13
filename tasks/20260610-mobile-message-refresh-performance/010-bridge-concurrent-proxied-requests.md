# Bridge Concurrent Proxied Requests

Fix bridge request head-of-line blocking so independent proxied HTTP requests from one app client can progress concurrently instead of serializing behind the first pending response.

## Requirements checklist

- [ ] Try to keep the bridge WebSocket protocol between the SDK and bridge unchanged.
- [ ] Change the bridge app channel so `http_request` handling does not block the channel process while waiting for the server response.
- [ ] Apply the same concurrency model to chunked request/response paths.
- [ ] Preserve timeout handling, PubSub unsubscribe cleanup, request correlation, and server-not-found behavior.
- [ ] Add tests proving a slow proxied request does not block a later fast proxied request on the same app channel.
- [ ] Add or update the SDK-facing bridge E2E test for concurrent proxied requests.
- [ ] Rerun all existing SDK-facing bridge E2E cases.
- [ ] Rerun cheap `BridgeTransport` unit tests; if the SDK protocol/client code does not change, these may be redundant but should still be inexpensive.
- [ ] Add or update bridge/Python bridge-client tests needed by the implementation.

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