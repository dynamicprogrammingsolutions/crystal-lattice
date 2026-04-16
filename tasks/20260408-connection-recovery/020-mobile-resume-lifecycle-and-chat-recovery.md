# Mobile Resume Lifecycle And Chat Recovery

Make the React Native app recover cleanly after lock/unlock or background/foreground transitions, including chat send/cancel/reload behavior when transport requests fail before a request id is known.

## Requirements checklist

- [x] Improve mobile foreground/background recovery for direct HTTP and bridge usage.
- [x] Make chat send state recoverable when a request fails or times out before `request_id` is returned.
- [x] Ensure cancel/reload/retry behavior remains usable after wake-from-lock scenarios.
- [x] Add mobile-focused observability for resume/reconnect/send-state transitions.
- [x] Add related integration tests in the same subtask for resume and stuck-chat-state scenarios.

Parent Task: `tasks/20260408-connection-recovery/000-main.md`

Depends On: `tasks/20260408-connection-recovery/010-transport-reliability-and-recovery.md`

## Problems discovered

### 1. The app disconnects on background but does not eagerly reconnect on foreground

- `mobile/crystal-lattice-control-rn/App.tsx:137-153` disconnects active transports whenever app state is not `active`.
- There is no matching root-level "on foreground, reconnect now" path in `App.tsx`.
- Recovery currently depends on later requests or polling attempts.

### 2. Chat polling is paused/resumed by app state, but request recovery is indirect

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:347-366` toggles `eventsEnabled` based on app activity and screen activity.
- `packages/frontend-sdk-react/src/useChatController.ts:70-100` starts polling only after the controller has an initial snapshot and when events are enabled.
- This is fine for normal polling, but not enough for a wake-from-lock transport failure where reconnect or revalidation should happen deliberately.

### 3. The stuck spinner / non-working cancel path still exists

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1539-1588` sets `sendInProgress = true` before awaiting `chatController.sendMessage(...)`.
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:2408-2410` shows a spinner whenever `sendInProgress || activeRequestId`.
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1661-1663` disables cancel when `sendInProgress || !activeRequestId`.
- If the send fails before returning `request_id`, the user can see an indefinite spinner with no usable cancel path until the request eventually rejects or the app is restarted.

### 4. Cancel relies on later events to clear state

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1619-1623` explicitly relies on later lifecycle events after cancel.
- `packages/frontend-sdk/src/chat/streamingStateReducer.ts:129-137` clears `activeRequestId` only on `request_completed` or `request_cancelled`.
- After wake-from-lock, if polling is disrupted or transport recovery is delayed, request state can remain stale in the UI.

## Implementation guidance

- Keep this subtask focused on the mobile app and chat controller interaction, not low-level transport internals.
- After foregrounding, the app should explicitly recover connection/session state rather than waiting for the user to stumble into a failing request.
- The chat UI should distinguish:
  - request not acknowledged yet
  - request acknowledged and active
  - transport failure before request id
- Observability here should stay mobile-specific:
  - app resume and reconnect attempts
  - polling restart after resume
  - send state transitions around pre-`request_id` failures

## Suggested test coverage

- Resume/foreground integration test for bridge recovery from an existing paired session.
- Resume/foreground test for direct HTTP where first request after wake fails or times out cleanly.
- Regression test for "spinner forever": send fails before `request_id`, UI leaves loading state and offers recovery.
- Regression test for cancel/reload/retry behavior after resume and after transport-level failure.

## Starting references

- `mobile/crystal-lattice-control-rn/App.tsx:137-153`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:347-372`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:754-777`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1539-1628`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1653-1668`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:2403-2419`
- `packages/frontend-sdk-react/src/useChatController.ts:70-100`
- `packages/frontend-sdk/src/chat/streamingStateReducer.ts:46-137`

## Execution plan

Added during completion.

1. Add explicit foreground recovery orchestration in the mobile root.
   - Extract the current bridge repair flow in `mobile/crystal-lattice-control-rn/App.tsx`.
   - Reconnect active bridge transports eagerly on foreground instead of waiting for a later request.
   - Propagate a resume signal to active screens so direct HTTP and bridge sessions can both revalidate on wake.

2. Add deliberate chat-controller recovery after resume.
   - Extend the chat controller with a resume/revalidation path that reloads the active message window and reconciles `activeRequestId` from the server.
   - Trigger that path from the chat screen after app foregrounding and after recovery-oriented reload actions.

3. Make pre-`request_id` send failures recoverable.
   - Keep explicit local state for a send that failed before ack.
   - Preserve and reuse the original idempotency key for retry.
   - Surface recovery actions in the chat UI so the user can check status or retry without duplicating accepted sends.

4. Add mobile-focused observability.
   - Record resume, reconnect, polling-restart, send, pre-ack failure, and recovery events in a lightweight mobile debug timeline.
   - Expose that timeline alongside the existing event debug view.

5. Add regression coverage.
   - Add SDK-level tests for resume reconciliation and pre-ack send recovery behavior.
   - Add mobile-side Jest coverage for the new recovery helper logic and debug timeline rendering where practical.

## Completion Notes

Added during completion.

- Implemented root-level mobile foreground recovery in `mobile/crystal-lattice-control-rn/App.tsx`, including eager bridge reconnect attempts on foreground, bridge repair-flow reuse, resume epoch propagation to screens, and a shared mobile debug timeline.
- Added `ChatController.recoverAfterResume()` in `packages/frontend-sdk/src/chat/chatController.ts` and used it from `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` so wake-from-lock triggers an explicit message-window reload and `activeRequestId` reconciliation instead of relying only on polling restart.
- Reworked the chat screen send lifecycle to preserve a pending pre-ack recovery state with the original idempotency key, expose `Check status` and `Retry` recovery actions, clear the spinner after ack failures, and record recovery transitions in the mobile debug timeline.
- Extended the debug modal to render both mobile timeline notes and streamed backend events, using `mobile/crystal-lattice-control-rn/src/components/DebugEventsView.tsx` plus the new helper modules `mobile/crystal-lattice-control-rn/src/debugTimeline.ts` and `mobile/crystal-lattice-control-rn/src/chatRecovery.ts`.
- Added regression coverage:
  - `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts` now covers `recoverAfterResume()` against the real FastAPI backend.
  - `mobile/crystal-lattice-control-rn/__tests__/chatRecovery.test.ts` covers pending-send recovery helpers.
  - `mobile/crystal-lattice-control-rn/__tests__/DebugEventsView.test.tsx` covers the combined debug timeline/event view.
- Follow-up adjustment:
  - Removed automatic full chat reload on app foreground.
  - Kept transport-level foreground reconnect in the mobile root.
  - Changed session-open bootstrap so every newly opened chat performs one initial server reload, even when hydrated from cache.
  - Added explicit `ensureEventStreamingStarted()` startup so an opened session does not depend solely on incidental hook timing to begin polling.
- Verification:
  - `npm test` in `packages/frontend-sdk`: passed.
  - Follow-up rerun `npm test` in `packages/frontend-sdk`: passed.
  - `RUN_BACKEND_INTEGRATION=1 npx vitest run src/integration/__tests__/backend.integration.test.ts -t "H: recoverAfterResume reloads the active window and reconciles a stale request id"`: passed.
  - `npm test -- --runInBand` in `mobile/crystal-lattice-control-rn`: passed.
  - Follow-up rerun `npm test -- --runInBand` in `mobile/crystal-lattice-control-rn`: passed.
  - `npx tsc --noEmit --project tsconfig.json` in `mobile/crystal-lattice-control-rn` still reports pre-existing `SessionChatScreen.tsx` attachment-side type errors unrelated to this recovery work.
- Follow-up investigation:
  - Added a real FastAPI + frontend SDK integration reproducer for reopened persisted sessions after backend restart in `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`.
  - Extended `packages/frontend-sdk/src/integration/harness.ts` so restart-style tests can reuse an existing config file and sessions directory across backend processes.
  - Verification for this follow-up is tracked separately from the earlier green runs, because the new restart regression test is intended to confirm whether older-session send visibility currently fails.
  - Root cause and fix:
    - Reopened sessions after backend restart could begin polling with a null cursor, allowing `/events` to keep reusing the server's moving default session cursor and skip the first post-reopen send events.
    - Added an explicit polling bootstrap cursor path in the frontend SDK (`getLatestEventId()` plus `PollingEventSource` startup stabilization) so null-cursor sessions pin a stable lower bound before normal session polling begins.
    - Updated `/events` responses to always include `latest_event_id`, which keeps the contract explicit and helps filtered polling callers stabilize empty responses.
    - Shared request-state handling was temporarily tightened so `final` events also cleared `activeRequestId`, but that change was later reverted because it changed UI semantics incorrectly; request state now remains tied to `request_completed` / `request_cancelled`, while the restart/reopen bugs are handled by the lower-level event cursor fixes.
    - Updated the backend integration harness/config to use the new repo-root system-message feature plugin package under `plugins/feature-system-message`.
    - Changed `AgentApplication` startup to default the plugin cache directory relative to the config directory and to raise immediately for plugin resolution/import errors instead of degrading silently.
  - Follow-up verification:
    - `RUN_BACKEND_INTEGRATION=1 npx vitest run src/integration/__tests__/backend.integration.test.ts`: passed.
    - `RUN_BACKEND_INTEGRATION=1 npx vitest run src/integration/__tests__/backend.integration.test.ts -t "I: reopened persisted sessions after backend restart keep the next user send visible before assistant final"`: passed.
    - `npm test` in `packages/frontend-sdk`: passed (integration tests remain skipped unless `RUN_BACKEND_INTEGRATION=1` is set).
    - `pytest core/python/tests/test_application_config_errors.py -q`: passed.
    - `pytest application/python/tests/test_agent_terminal_app_server.py -q -k "events_endpoint_bootstrap_returns_latest_event_id or events_endpoint_uses_session_cursor_as_default_since_id or filtered_empty_response_still_includes_latest_event_id"`: passed.
  - Additional follow-up coverage:
    - Added restart/polling regression `J` in `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts` for the case where the backend restarts while the same controller keeps polling.
    - Added cache-rehydration regressions `K1`-`K4` in `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts` covering:
      - cached reopen without restart
      - cached reopen after backend restart
      - empty cached session without restart
      - empty cached session after backend restart
    - Extended `packages/frontend-sdk/src/integration/harness.ts` to support restarting the backend on a fixed port so a single live transport/controller can survive a backend restart.
    - Root cause for the live-poll restart bug:
      - event ids were process-local and restart from low values after backend restart
      - comparing bare numeric `since_id` values across server processes is unsafe, even when the old cursor is not greater than the new latest id
      - final fix moved this one level lower into the shared event layer:
        - `InMemoryEventStore` now emits composite opaque ids of the form `<store-instance>:<counter>`
        - store-side `since_id` handling replays safely when the cursor belongs to another store instance
        - the frontend poller now treats `event_id` as an opaque cursor token instead of parsing numeric ids
      - this removed the temporary need for an HTTP-only `server_instance_id` response field
    - Verification:
      - `RUN_BACKEND_INTEGRATION=1 npx vitest run src/integration/__tests__/backend.integration.test.ts`: passed with 15 tests.
      - `npm test` in `packages/frontend-sdk`: passed.
      - `pytest application/python/tests/test_agent_terminal_app_server.py -q -k "events_endpoint_bootstrap_returns_latest_event_id or events_endpoint_uses_session_cursor_as_default_since_id or filtered_empty_response_still_includes_latest_event_id"`: passed with explicit `server_instance_id` assertions.
  - Follow-up correction:
    - Reverted the temporary reducer behavior that cleared `activeRequestId` on `final`; request lifecycle state again remains owned by `request_completed` / `request_cancelled`.
    - Adjusted cursor-expiry handling in `packages/frontend-sdk/src/chat/chatController.ts` so an expired cursor that exactly matches the last `/messages` snapshot cursor is treated as non-resumable rather than as a reason to reload the same snapshot again.
    - In that case, the controller now clears both stored cursors and restarts polling from a null bootstrap, which prevents cached old sessions from entering a repeating reload loop when `/messages` returns an already-expired cursor.
    - Added regression coverage for both the reducer correction and the expired-snapshot-cursor no-reload path in the frontend SDK tests.