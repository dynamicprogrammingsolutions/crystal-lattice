# Transport Reliability And Recovery

Strengthen both direct HTTP and bridge transport behavior so hung or stale connections are detected, surfaced, and recoverable without restarting the mobile app.

## Requirements checklist

- [x] Add direct HTTP timeout support so `FetchTransport` does not allow requests to hang forever.
- [x] Improve bridge liveness handling for stale or half-open sockets.
- [x] Ensure timed-out bridge requests do not keep reusing a dead socket forever.
- [x] Add transport-level observability for timeout, liveness, reconnect, and socket reset paths.
- [x] Add related integration tests in the same subtask for direct HTTP timeout and bridge recovery scenarios.

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

## Execution plan

Added during completion planning on 2026-04-09 after plan approval.

1. Unify SDK timeout configuration and matching
   - Extend `FetchTransport` to support transport-level timeout configuration instead of only ad hoc per-request `timeoutMs`.
   - Extend the existing bridge timeout override mechanism into a shared method-aware matcher shape so timeout rules can consider both HTTP method and path, not just path prefix.
   - Support exact method matching alongside path-prefix and regex-style matching so the SDK can distinguish cases like `GET /sessions/{id}/messages` from `POST /sessions/{id}/messages`.
   - Keep precedence consistent across transports:
     - explicit `req.timeoutMs`
     - matched transport rule
     - transport default timeout
   - Keep direct HTTP and bridge transports aligned on timeout/error wording so callers can react consistently.

2. Add real direct HTTP timeout handling in `FetchTransport`
   - Implement request aborts with `AbortController`.
   - Start and clear per-request timers safely so stalled requests do not hang forever and timers do not leak.
   - Convert timeout aborts into transport-level timeout errors that include method, path, and duration.
   - Add transport observability for direct HTTP:
     - request start
     - request success
     - request timeout
     - request failure

3. Add bridge socket liveness detection and health tracking
   - Add an explicit socket lifecycle layer in `BridgeTransport` with helpers such as socket reset/teardown, connection generation tracking, and heartbeat start/stop management.
   - Implement Phoenix heartbeats on the app socket while connected.
   - Use a heartbeat interval comfortably below the bridge websocket idle timeout so half-open sockets are detected proactively.
   - Treat missed heartbeat replies as a dead connection:
     - fail in-flight bridge work
     - clear the socket
     - clear `sessionId`
     - retain `serverId` and `pairingToken` so reconnect can resume cleanly
   - Add bridge observability for:
     - connect start/open
     - join/resume success
     - heartbeat send/success/timeout
     - socket close
     - socket reset reason
     - reconnect attempts/results

4. Make bridge timeouts trigger recovery when they imply a dead socket
   - On control-plane timeouts such as `phx_join`, `resume_session`, pairing calls, and bridge HTTP request control messages, reset the socket immediately because those operations should not stall on a healthy connection.
   - On non-polling HTTP request timeouts, reset the socket and clear `sessionId` so the next request cannot reuse a dead websocket.
   - Keep `/events` handling conservative to avoid poll/reconnect thrash:
     - a single `/events` timeout should remain a poll failure, not automatically poison the connection
     - dead-socket detection should come from heartbeat failure rather than every polling timeout
   - Preserve the existing reconnect-and-resume behavior by retaining pairing/session resume inputs across resets.

5. Preserve longer timeouts for heavy and synchronous operations
   - Do not apply a blanket short timeout to all requests.
   - Keep normal requests on a shorter default timeout.
   - Assign longer timeouts to known heavy or synchronous paths that legitimately need more time:
     - `POST /sessions/{id}/messages` for append flows that may include inline multipart/image payloads
     - `POST /sessions/{id}/send_message` for atomic append+send flows with multipart payloads
     - `POST /actions` for synchronous application actions that may run for longer on the server side
   - Leave `POST /sessions/{id}/send` on the normal timeout unless testing shows request admission itself can be slow, because the actual model work happens in the background after the acknowledgement response.
   - Prefer setting these longer timeouts from `RestAgentBackend` call sites or via method-aware transport rules rather than path-prefix-only matching, because method distinction is required for dynamic session routes.

6. Normalize mobile transport construction around shared timeout policy
   - Refactor transport creation in the React Native app so direct HTTP and bridge transports are created through small helpers instead of repeated constructor calls.
   - Apply the shared timeout policy across:
     - manual connections
     - discovery connections
     - saved direct reconnects
     - bridge connect/reconnect paths
   - Keep `/events` on its shorter poll timeout while preserving longer allowances for append/send_message/action flows.

7. Keep bridge-server changes minimal in this subtask
   - Do not reduce the Elixir bridge’s `await_http_response` default timeout as part of the first implementation pass unless recovery tests show it is safe.
   - Add bridge-side observability around timeout paths where useful for debugging transport recovery.
   - Rely on Phoenix heartbeat semantics where possible instead of expanding server-side protocol surface unnecessarily.

8. Add focused tests for timeout and recovery behavior
   - Add `FetchTransport` unit tests for:
     - request timeout aborts
     - timeout cleanup on success
     - per-request timeout override precedence
     - method-aware timeout rule matching
   - Expand `BridgeTransport` unit tests for:
     - healthy heartbeat flow
     - missed heartbeat causing socket reset
     - timed-out non-poll request causing reconnect on next use
     - reconnect resuming the existing pairing/session
     - `/events` timeout remaining non-fatal if heartbeat is still healthy
   - Add direct HTTP integration coverage using test-control server hooks to intentionally stall a request and verify timeout behavior against the real FastAPI server.
   - Add bridge recovery integration coverage that exercises:
     - successful pairing
     - bridge outage or dead connection
     - request failure plus socket reset
     - bridge restart
     - successful reconnect and resumed request flow without recreating the mobile-side transport
   - Keep the existing `/events` overlap/reload integration tests green while introducing recovery logic.

## Completion Notes

Added during completion on 2026-04-09.

- Implemented shared method-aware transport timeout matching in `packages/frontend-sdk/src/transport/transport.ts` and applied it to both `FetchTransport` and `BridgeTransport`.
- Added real direct HTTP timeout handling with `AbortController` plus timeout/start/success/error logging in `packages/frontend-sdk/src/transport/fetchTransport.ts`.
- Added bridge heartbeat-based liveness detection, socket reset/teardown handling, timeout-triggered socket poisoning for non-poll requests, and reconnect/resume support improvements in `packages/frontend-sdk/src/transport/bridgeTransport.ts`.
- Preserved longer timeouts for heavy synchronous operations by passing explicit `timeoutMs` for append, send_message, and executeAction in `packages/frontend-sdk/src/backend/restBackend.ts`.
- Centralized mobile transport construction and shared timeout policy in `mobile/crystal-lattice-control-rn/App.tsx`.
- Added a test-only delayed backend route in `application/python/agent_terminal_app/server.py` and bridge timeout logging in `bridge-elixir/lib/bridge/app_channel.ex`.
- Added/updated tests:
  - `packages/frontend-sdk/src/transport/fetchTransport.test.ts`
  - `packages/frontend-sdk/src/transport/bridgeTransport.test.ts`
  - `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`
  - `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts`
- Verification performed:
  - `npx vitest run src/transport/fetchTransport.test.ts src/transport/bridgeTransport.test.ts src/backend/restBackend.idempotency.test.ts`
  - `RUN_BACKEND_INTEGRATION=1 npx vitest run src/integration/__tests__/backend.integration.test.ts -t "G: FetchTransport times out cleanly against a delayed backend response"`
- Verification gaps / environment notes:
  - Full `backend.integration.test.ts` still reports unrelated failures in scenarios `A` and `D` in this environment.
  - `RUN_BRIDGE_E2E_INTEGRATION=1 npx vitest run src/integration/__tests__/bridge.e2e.integration.test.ts -t "reconnects and resumes after the bridge restarts"` could not run because the local Docker daemon was unavailable.

Follow-up on 2026-04-09:

- Fixed Phoenix bridge error extraction so `resume_session` failures surface their real `reason` values instead of the generic `"Request failed"` text.
- Improved mobile saved-bridge reconnection flow in `mobile/crystal-lattice-control-rn/App.tsx`:
  - stale or invalid saved pairings now open the bridge re-pair flow instead of stopping at a generic alert
  - invalid pairing tokens and server mismatches clear the stored pairing token so the app does not keep retrying a known-bad resume path
- Verification performed for the follow-up:
  - `npx vitest run src/transport/bridgeTransport.test.ts`
  - `npm test` in `packages/frontend-sdk`
  - `npx tsc --noEmit --project tsconfig.json 2>&1 | rg "App\\.tsx|bridgeTransport|transport\\.ts"` in `mobile/crystal-lattice-control-rn` returned no errors for the touched files, while the full mobile TypeScript check still has unrelated existing errors elsewhere.