# Bridge Concurrent Proxied Requests

Fix bridge request head-of-line blocking so independent proxied HTTP requests from one app client can progress concurrently instead of serializing behind the first pending response.

## Requirements checklist

- [ ] Keep the existing bridge WebSocket protocol backward compatible for app and server clients.
- [ ] Change the bridge app channel so `http_request` handling does not block the channel process while waiting for the server response.
- [ ] Apply the same concurrency model to chunked request/response paths.
- [ ] Preserve timeout handling, PubSub unsubscribe cleanup, request correlation, and server-not-found behavior.
- [ ] Add tests proving a slow proxied request does not block a later fast proxied request on the same app channel.
- [ ] Verify existing bridge tests continue to pass.

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

For non-chunked responses, the channel may use Phoenix async replies, push response messages, or another local process that owns the waiting receive. For chunked responses, the current client expects pushed `http_response_init/chunk/end` messages followed by a final reply indicating `type: "http_response_chunked"`. Preserve that observable behavior unless coordinating SDK changes in the same task.

Tests should include:

- A slow request through the bridge followed immediately by a fast request on the same app channel. The fast request must complete before the slow request.
- A large chunked response still arrives in sequence and completes successfully.
- Timeout cleanup unsubscribes the PubSub topic and does not poison later requests.

Likely test locations:

- `bridge-elixir/test/bridge/app_channel_resume_test.exs`
- `bridge-elixir/test/bridge/server_channel_chunked_http_test.exs`
- `packages/frontend-sdk/src/transport/bridgeTransport.test.ts` if SDK behavior needs to be adjusted or guarded.