# Chat persistence, scrolling, and reconcile-on-completion (Phase 4.4)

This document proposes a focused cleanup/refactor to address a cluster of chat UX issues:

- Scroll restoration often snaps to top instead of bottom when unknown.
- Restoring messages from cache often restores a stale snapshot (missing event-applied messages), then "replays" old events.
- Sending a message triggers a full reload, which is unnecessary when events are active and can cause duplicates/races.

The unifying goal is to make chat behavior **event-driven and stateful**:

- `ChatController` becomes the source of truth for the chat state machine.
- The app persists a **controller-produced snapshot** instead of persisting only the last REST `listMessages()` snapshot.
- Reloads become a deliberate reconciliation step, not part of the normal send path.

## Background (what exists today)

- Cached messages are updated only from explicit reloads (e.g. `loadMessages()` calling `onUpdateCache(...)`).
- Events update controller state, but those updates are not persisted to cache.
- Scroll persistence stores a raw `scrollOffset` and treats `0` as "top" (but `0` also means "unknown"), making default behavior wrong.
- Send performs `appendMessage` + `send` + `loadMessages`, which races with event-delivered updates.

## Phase 4.4 goals

1) **Persist correct chat state** (including event-applied changes) so session switching is fast and consistent.
2) **Scroll defaults to bottom** when offset is missing/unreliable.
3) **Send is event-driven**: no immediate reload; avoid duplicates.
4) Add a single **reconcile-on-completion** step to ensure correctness without constant reloads.

## Proposed changes

### A) Persisted controller snapshot

Introduce an SDK-owned persisted snapshot shape derived from controller state.

**New SDK types (example)**

```ts
export interface ChatPersistedSnapshot {
  sessionId: string;
  messages: IndexedMessage[];
  // Cursor for polling: the highest processed event_id.
  eventsCursorId: string | null;
  // Cursor from listMessages response (optional, useful for diagnostics).
  listCursorEventId: string | null;
  activeRequestId: string | null;
  updatedAtMs: number;
}
```

**SDK responsibilities**

- `ChatController` maintains and exposes `eventsCursorId` (highest processed `event_id`).
- `ChatController` offers `getPersistedSnapshot()` and/or a `subscribePersistedSnapshot(...)` convenience.
- When events are applied, controller updates `eventsCursorId` and the persisted snapshot.

**App responsibilities**

- The RN app persists `ChatPersistedSnapshot` per `(connectionId, sessionId)`.
- Cache writes are throttled/debounced (e.g. 250–1000ms) to avoid excessive `AsyncStorage` writes.

**Why this fixes the cache regression**

- Restores include event-applied messages.
- Polling resumes from `eventsCursorId`, preventing replay of old events.

### B) Scroll persistence as "bottom anchor" not raw offset

Replace `scrollOffset` persistence with an anchor model.

**New persisted fields (example)**

```ts
export interface ChatScrollAnchor {
  // Distance from bottom at the time of persistence.
  bottomGapPx: number;
  // Whether user was effectively pinned to bottom.
  pinnedToBottom: boolean;
  updatedAtMs: number;
}
```

**UI behavior**

- If no saved anchor exists (or it is stale/unreliable), default to `scrollToEnd()`.
- If `pinnedToBottom` is true, always `scrollToEnd()` on mount and when new messages arrive.
- If not pinned, restore using `bottomGapPx` so that additional messages do not shift the user upward.

**Implementation note**

- This stays in the UI layer (platform-specific), but the persisted format can live in the SDK.
- Create a UI helper/hook like `useChatScrollAnchor(...)` that:
  - tracks whether user is near bottom
  - computes `bottomGapPx` on scroll
  - restores on content size changes

### C) Send becomes event-driven (no immediate reload)

Update send flow to avoid the `append → send → loadMessages` pattern.

**Target behavior**

- On send:
  - Optimistically append the user message in controller (optional), OR rely on a `message_appended` event.
  - Call `backend.send(sessionId)`.
  - Do *not* call `loadMessages()`.

**Why this improves UX**

- Avoids expensive full reload on every send.
- Avoids duplicates when events deliver the same message content.

### D) Reconcile-on-completion (single controlled reload)

We still want correctness even if the event stream drops messages or ordering.

**Policy**

- When the controller observes `request_completed`/`request_cancelled`, schedule a reconciliation:
  - Debounce (e.g. 250–500ms)
  - Call `listMessages()` once
  - Replace controller messages with server snapshot
  - Update persisted snapshot + cursors

This makes reload a deliberate correctness mechanism, not part of the normal UX.

### E) Deduplication and correctness strategy

Avoid complex client-side dedupe heuristics.

- Primary correctness comes from reconcile-on-completion.
- During streaming, treat event-applied appends as provisional.
- If events arrive out of order or are duplicated, reconciliation resolves it.

## Implementation stages (Phase 4.4)

### Stage 4.4.1 — Persisted snapshot plumbing

- Add `eventsCursorId` tracking in `ChatController`.
- Add `getPersistedSnapshot()`.
- Update RN cache model to store and restore the controller snapshot.
- Start event polling from `eventsCursorId` if present.

**Success criteria**

- Switching sessions does not revert to older message states.
- Poller does not replay old events after restore.

### Stage 4.4.2 — Scroll anchor persistence

- Replace `scrollOffset` persistence with `ChatScrollAnchor`.
- Default to bottom when anchor is missing/unreliable.
- Respect "not at bottom" when user is reading older messages.

**Success criteria**

- Unknown scroll state starts at bottom.
- Returning to a session preserves reading position reliably.

### Stage 4.4.3 — Event-driven send + reconcile-on-completion

- Remove unconditional `loadMessages()` from send/resend.
- Introduce controller-driven reconcile (debounced) triggered by completion events.
- Persist reconciled snapshots.

**Success criteria**

- Send does not perform an immediate reload.
- Duplicate messages caused by reload+events disappear.
- Final state always matches server after completion.

## Files likely to change (when implementing)

- `packages/frontend-sdk/src/chat/chatController.ts`
- `packages/frontend-sdk/src/events/pollingEventSource.ts` (cursor semantics)
- `packages/frontend-sdk-react/src/useChatController.ts`
- `mobile/crystal-lattice-control-rn/App.tsx` (cache schema update)
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` (remove reload-on-send; scroll hook)

## Risks / notes

- Persisting messages frequently: requires throttling to avoid AsyncStorage write churn.
- Cursor semantics: `cursor_event_id` from `listMessages` is not necessarily the same as `event_id` max from polling; prefer persisting polling cursor.
- Reconcile timing: must debounce to avoid redundant reloads when multiple completion-like events arrive.
