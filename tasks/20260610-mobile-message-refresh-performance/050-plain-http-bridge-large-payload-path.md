# Plain HTTP Bridge Large Payload Path

Add an optional plain HTTP path for selected bridge transport requests so large payloads can use HTTP transfer behavior such as compression, HTTP/2, and binary-safe streaming instead of JSON-over-WebSocket text frames.

## Requirements checklist

- [ ] Keep the existing WebSocket bridge path working for pairing, control, events, and normal proxied requests.
- [ ] Add a frontend-to-bridge HTTP option for selected SDK requests.
- [ ] Let the SDK choose the HTTP path for large/read-heavy requests while preserving the existing `Transport` API.
- [ ] Explore or implement gzip/br compression for HTTP bridge responses.
- [ ] Design a server-to-bridge large-response path where the Python bridge client can send large response bodies via HTTP while the WebSocket remains the control channel.
- [ ] Avoid unnecessary base64/text conversion for binary payloads where HTTP can carry bytes directly.
- [ ] Add integration/E2E tests that prove SDK-facing behavior is unchanged for both WebSocket and HTTP bridge paths.

Parent Task: tasks/20260610-mobile-message-refresh-performance/000-main.md

Depends On: tasks/20260610-mobile-message-refresh-performance/010-bridge-concurrent-proxied-requests.md

## Background

This is a later-stage transport improvement. It should follow the immediate bridge head-of-line blocking fix, because concurrency correctness matters even before large-payload transfer optimization.

Current bridge transport uses WebSocket/Phoenix channel messages for HTTP proxying. That works, but large payloads pay extra costs:

- payloads are serialized into JSON text frames;
- large responses must be chunked and reassembled in app code;
- normal HTTP compression and HTTP/2 behavior are not available for the tunneled payload body;
- binary payloads tend to require text-safe encodings such as base64.

The desired direction is a hybrid protocol:

- WebSocket remains the control plane for app/server registration, pairing, request coordination, resume, heartbeat, and events.
- Frontend can send specific proxied HTTP requests to the bridge via plain HTTP.
- Backend/Python bridge client can still receive request instructions via WebSocket.
- For large responses, backend can choose to upload or stream the response body to the bridge over HTTP using a request token, and the bridge can serve/stream that response body to the frontend over HTTP.

## Design Questions

Resolve these during task execution:

- Which requests should choose HTTP automatically? Candidate paths include `/sessions/{id}/messages` and asset/binary endpoints.
- How does the SDK negotiate or discover HTTP bridge support?
- Should the WebSocket request message return a signed/opaque upload or download token?
- How should timeout, cancellation, and cleanup work if the control channel disconnects while an HTTP body transfer is in progress?
- How should this behave behind local Docker, direct LAN bridge, and deployed bridge environments?
- How can gzip/br be enabled consistently in local Phoenix, HAProxy, and cloud deployments?

## Testing Guidance

Add SDK-facing E2E coverage, not only protocol/unit tests. The tests should run through `BridgeTransport`/`RestAgentBackend` where possible and verify that callers still see the same `Transport` response shape.

Suggested tests:

- Small requests still use the existing WebSocket path.
- A large message/data response can use the HTTP path and returns the same parsed data as the WebSocket path.
- Compression is active where the test environment can reliably assert it.
- Binary payload transfer avoids base64 when using HTTP.
- Disconnection/timeout cleanup does not leak pending transfer state.

Likely files:

- `packages/frontend-sdk/src/transport/bridgeTransport.ts`
- `packages/frontend-sdk/src/transport/bridgeTransport.test.ts`
- `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts`
- `bridge-elixir/lib/bridge/router.ex`
- `bridge-elixir/lib/bridge/app_channel.ex`
- `bridge-elixir/lib/bridge/server_channel.ex`
- `application/python/agent_terminal_app/bridge_client.py`