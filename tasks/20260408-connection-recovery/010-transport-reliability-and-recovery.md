# Transport Reliability And Recovery

Strengthen both direct HTTP and bridge transport behavior so hung or stale connections are detected, surfaced, and recoverable without restarting the mobile app.

## Requirements checklist

- [ ] Add direct HTTP timeout support so `FetchTransport` does not allow requests to hang forever.
- [ ] Improve bridge liveness handling for stale or half-open sockets.
- [ ] Ensure timed-out bridge requests do not keep reusing a dead socket forever.
- [ ] Add transport-level observability for timeout, liveness, reconnect, and socket reset paths.
- [ ] Add related integration tests in the same subtask for direct HTTP timeout and bridge recovery scenarios.

Parent Task: `tasks/20260408-connection-recovery/000-main.md`

## Declared overlap

- Overlaps `tasks/20260215-multipart-upload/100-bridge-chunked-http-over-websocket.md`
- Intended to absorb remaining item `P1.5 Heartbeat / WS idle timeout alignment`
- Only partially overlaps remaining item `P1.7 Python: stalled chunked request cleanup / TTL`

## Problems discovered

### 1. Direct HTTP transport ignores timeout configuration

- `packages/frontend-sdk/src/transport/transport.ts:3-10` includes `timeoutMs` in the transport contract.
- `packages/frontend-sdk/src/transport/fetchTransport.ts:12-35` never uses `timeoutMs`, never creates an `AbortController`, and never aborts a stalled request.
- Result: in non-bridge mode, a request after device wake can hang forever at the transport layer.

### 2. Bridge has no proactive liveness detection

- `packages/frontend-sdk/src/transport/bridgeTransport.ts:318-331` only checks `readyState === 1`.
- No heartbeat, ping/pong, or periodic health probe was found in the transport.
- No `phx_heartbeat` implementation was found in the bridge client code path.
- Result: a half-open socket can appear healthy forever while requests time out.

### 3. Timed-out bridge requests do not poison the connection

- `packages/frontend-sdk/src/transport/bridgeTransport.ts:484-529` rejects an individual pending request on timeout.
- That path does not reset `ws`, does not clear pairing/session state beyond the specific request, and does not force reconnect on the next request.
- Result: retries may continue using the same stale WebSocket.

### 4. Two-minute timeout is present on both sides of the bridge path

- Client default: `packages/frontend-sdk/src/transport/bridgeTransport.ts:94` sets `defaultRequestTimeoutMs` to `120_000`.
- Server-side bridge wait: `bridge-elixir/lib/bridge/app_channel.ex:15-29` and `bridge-elixir/lib/bridge/app_channel.ex:31-53` also default to `120_000`.
- Result: many bridge operations can appear frozen for roughly two minutes before any failure becomes visible.

## Implementation guidance

- Keep direct HTTP and bridge work together in this subtask because both are transport-layer reliability concerns.
- Prefer one consistent timeout/error model that frontends can react to similarly.
- For bridge recovery, include explicit logic for:
  - liveness checks while connected
  - deciding when a timeout means "drop this socket"
  - reconnecting and resuming pairing/session cleanly
- Observability should be transport-focused here:
  - request start/end/timeout
  - bridge heartbeat failures
  - reconnect attempts and results
  - socket reset reasons

## Suggested test coverage

- Direct HTTP integration test where `send_message` or `/messages` stalls and times out cleanly.
- Bridge integration test where a request times out and the next request reconnects successfully.
- Bridge integration test for a stale/half-open socket or simulated dead connection.
- Keep existing `/events` overlap/reload behavior green while adding recovery logic.

## Starting references

- `packages/frontend-sdk/src/transport/fetchTransport.ts:1-57`
- `packages/frontend-sdk/src/transport/bridgeTransport.ts:32-168`
- `packages/frontend-sdk/src/transport/bridgeTransport.ts:318-430`
- `packages/frontend-sdk/src/transport/bridgeTransport.ts:484-560`
- `packages/frontend-sdk/src/transport/bridgeTransport.ts:782-798`
- `bridge-elixir/lib/bridge/app_channel.ex:15-53`
- `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts:150-240`