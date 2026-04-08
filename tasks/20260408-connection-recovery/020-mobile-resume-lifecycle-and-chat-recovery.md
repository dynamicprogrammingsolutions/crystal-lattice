# Mobile Resume Lifecycle And Chat Recovery

Make the React Native app recover cleanly after lock/unlock or background/foreground transitions, including chat send/cancel/reload behavior when transport requests fail before a request id is known.

## Requirements checklist

- [ ] Improve mobile foreground/background recovery for direct HTTP and bridge usage.
- [ ] Make chat send state recoverable when a request fails or times out before `request_id` is returned.
- [ ] Ensure cancel/reload/retry behavior remains usable after wake-from-lock scenarios.
- [ ] Add mobile-focused observability for resume/reconnect/send-state transitions.
- [ ] Add related integration tests in the same subtask for resume and stuck-chat-state scenarios.

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