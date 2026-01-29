# Chat persistence and scrolling (Phase 4.4)

This document proposes a focused cleanup/refactor to address a cluster of chat UX issues:

- Scroll restoration often snaps to top instead of bottom when unknown.
- Restoring messages from cache often restores a stale snapshot (missing event-applied messages), then "replays" old events.
- Sending a message triggering a full reload is undesirable.

The unifying goal is to make chat behavior **event-driven and stateful**:

- `ChatController` becomes the source of truth for the chat state machine.
- The app persists a **controller-produced snapshot** instead of persisting only the last REST `listMessages()` snapshot.
- Reloads should not be part of the normal send path; reload is a fallback for out-of-sync clients.

## Background (what exists today)

- Cached messages are updated only from explicit reloads (e.g. `loadMessages()` calling `onUpdateCache(...)`).
- Events update controller state, but those updates are not persisted to cache.
- Scroll persistence stores a raw `scrollOffset` and treats `0` as "top" (but `0` also means "unknown"), making default behavior wrong.
- Send performs `appendMessage` + `send` + `loadMessages`, which races with event-delivered updates.

## Phase 4.4 goals

1) **Scroll defaults to bottom** when offset is missing/unreliable.
2) **Preserve reading position** when the user scrolls away from bottom.
3) **Persist scroll state** in a way that stays stable as messages are appended.

Note: message-state correctness (reducers, dirty fallback, removing reloads) is tracked separately in:

- `tasks/20260129-events-no-full-session/000-main.md`

## Proposed changes

### A) Scroll persistence as "bottom anchor" not raw offset

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

### D) Dirty fallback (reload only when out of sync)

Correctness should be achieved by applying incremental events to local state.

When an event cannot be applied safely (index mismatch, missing prerequisites, unknown schema version), mark the session as `dirty` and surface a manual reload option.

## Implementation stages (Phase 4.4)

### Stage 4.4.1 — Scroll anchor persistence

- Replace `scrollOffset` persistence with `ChatScrollAnchor`.
- Default to bottom when anchor is missing/unreliable.
- Respect "not at bottom" when user is reading older messages.

**Success criteria**

- Unknown scroll state starts at bottom.
- Returning to a session preserves reading position reliably.

### Stage 4.4.3 — Event-driven send + reconcile-on-completion

This stage is superseded by the standalone event-contract task:

- `tasks/20260129-events-no-full-session/000-main.md`

## Files likely to change (when implementing)

- `mobile/crystal-lattice-control-rn/App.tsx` (scroll persistence schema update)
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` (scroll hook)

## Risks / notes

- Scroll persistence requires care to avoid fighting between restore and auto-scroll.
