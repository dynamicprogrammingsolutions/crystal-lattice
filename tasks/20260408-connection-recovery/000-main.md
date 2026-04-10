# Connection Recovery Across Transport and Mobile Lifecycle

Document the transport and mobile-app reliability problems discovered around hung requests, screen lock/unlock, and stale bridge connections, then implement and verify a compact two-part fix.

## Task checklist

- [x] `tasks/20260408-connection-recovery/010-transport-reliability-and-recovery.md`
- OVERLAP with `tasks/20260215-multipart-upload/100-bridge-chunked-http-over-websocket.md`
  - Expected to absorb remaining item `P1.5 Heartbeat / WS idle timeout alignment`.
  - Partially overlaps remaining item `P1.7 Python: stalled chunked request cleanup / TTL`, but does not fully replace it unless `010` is explicitly expanded to cover Python chunk-buffer TTL/scavenging.
- [x] `tasks/20260408-connection-recovery/020-mobile-resume-lifecycle-and-chat-recovery.md`

## Problem summary

The current failures are not limited to the bridge transport. Two related classes of problems were found:

1. Direct HTTP requests can hang indefinitely.
   - `packages/frontend-sdk/src/transport/fetchTransport.ts:12-35` accepts `timeoutMs` in the transport interface but ignores it and performs a bare `fetch(...)`.
   - When `send_message` hangs before returning a `request_id`, the chat screen keeps `sendInProgress = true` and shows a spinner indefinitely.
   - In that state, cancel is not available because the UI disables cancel while `sendInProgress` is true and there is no `activeRequestId` yet.

2. Bridge WebSocket liveness is weak.
   - `packages/frontend-sdk/src/transport/bridgeTransport.ts:318-331` treats any socket with `readyState === 1` as healthy.
   - There is no heartbeat or periodic health probe in the bridge client.
   - If the socket becomes half-open and never emits `close` or `error`, requests can keep timing out against the same stale socket instead of forcing a reconnect.
   - Most bridge requests default to `120_000ms` timeouts (`packages/frontend-sdk/src/transport/bridgeTransport.ts:156-159`), while only `/events` gets a shorter timeout in the mobile app (`mobile/crystal-lattice-control-rn/App.tsx:522-526`, `mobile/crystal-lattice-control-rn/App.tsx:941-946`).

3. Mobile foreground/background handling is incomplete.
   - The app disconnects transports whenever app state leaves `active` in `mobile/crystal-lattice-control-rn/App.tsx:137-153`.
   - On returning to the foreground, there is no root-level eager reconnect.
   - Recovery is mostly lazy and depends on later requests or polling.

4. Chat recovery depends heavily on events.
   - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1610-1623` relies on later `request_cancelled` / `request_completed` events to clear request state after cancel.
   - `packages/frontend-sdk/src/chat/streamingStateReducer.ts:129-137` only clears `activeRequestId` on those lifecycle events.
   - If polling is disrupted after device lock/unlock, request state can remain stuck longer than intended.

## Key references

- Direct HTTP transport: `packages/frontend-sdk/src/transport/fetchTransport.ts`
- Bridge transport lifecycle: `packages/frontend-sdk/src/transport/bridgeTransport.ts`
- Bridge server timeout behavior: `bridge-elixir/lib/bridge/app_channel.ex`
- Chat controller polling/reload logic: `packages/frontend-sdk/src/chat/chatController.ts`
- Chat UI send/cancel state: `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- Mobile app background disconnect behavior: `mobile/crystal-lattice-control-rn/App.tsx`
- Existing overlap/reload integration tests: `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`

## Overlap notes

This task set overlaps the remaining bridge backlog in `tasks/20260215-multipart-upload/100-bridge-chunked-http-over-websocket.md` only in a limited way:

- `010-transport-reliability-and-recovery` should be treated as the likely completion path for the remaining `P1.5 Heartbeat / WS idle timeout alignment` item in that task.
- `010-transport-reliability-and-recovery` only partially overlaps `P1.7 Python: stalled chunked request cleanup / TTL`; that Python chunk-buffer cleanup item should remain open unless the `010` implementation explicitly includes it.
- `020-mobile-resume-lifecycle-and-chat-recovery` has no substantial overlap with the still-remaining bridge chunking backlog items.