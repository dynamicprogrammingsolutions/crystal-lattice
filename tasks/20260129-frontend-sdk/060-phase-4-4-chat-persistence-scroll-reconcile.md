# Phase 4.4 — Chat persistence, scroll anchoring, and reconcile-on-completion

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/050-phase-4-headless-controllers.md`

Fix a cluster of UX and correctness issues in chat by making persistence and reconciliation controller-driven.

This phase is not implemented yet; it’s the next intended cleanup step.

## Status

- [ ] Not started

## Problems to solve (current behavior)

### 1) Scroll restore defaults to top too often

- The app persists a raw `scrollOffset` and uses `0` as the default.
- `0` is ambiguous (top vs unknown) so the UI tends to restore to top.

### 2) Cached restore returns stale state (missing event-applied messages)

- The cache is primarily updated on explicit reloads (`listMessages`).
- Event-applied updates in `ChatController` are not persisted, so restoring a session often loads an earlier snapshot then “catches up” by replaying old events.

### 3) Send triggers reload and can cause duplicates

- Current send flow still performs a post-send `loadMessages()`.
- While events are active, this can race with event-delivered message appends and lead to duplicates.

## Target design (what should exist after this phase)

### A) Persisted controller snapshot

- Introduce a persisted snapshot shape (SDK-owned), including:
  - `messages`
  - `eventsCursorId` (max processed `event_id` from polling)
  - `activeRequestId`
- Persist the snapshot whenever controller state changes (throttled), not only after manual reload.
- On restore, start polling from `eventsCursorId` to avoid replaying old events.

### B) Scroll persistence uses a bottom-anchor model

- Persist `bottomGapPx` (distance from bottom) and whether user is “pinned to bottom”.
- When state is missing/unreliable, default to bottom.

### C) Event-driven send + single reconcile-on-completion

- Remove unconditional `loadMessages()` after send/resend.
- Add a debounced reconciliation step triggered by completion events (`request_completed` / `request_cancelled`):
  - call `listMessages()` once
  - replace/merge controller messages with server snapshot
  - persist the reconciled snapshot

## Work breakdown checklist

### Stage 4.4.1 — Persisted snapshot plumbing

- [ ] Add `eventsCursorId` tracking to `ChatController` when applying events
- [ ] Add `getPersistedSnapshot()` (or a persisted-snapshot subscription) to `ChatController`
- [ ] Update RN cache storage schema to persist/restore the controller snapshot
- [ ] Ensure polling resumes from `eventsCursorId` (not just `cursor_event_id`)

### Stage 4.4.2 — Scroll anchor persistence

- [ ] Replace `scrollOffset` persistence with `bottomGapPx` + `pinnedToBottom`
- [ ] Default to bottom when anchor is missing/unreliable
- [ ] Ensure scroll restoration doesn’t fight with “new message auto-scroll” behavior

### Stage 4.4.3 — Event-driven send + reconcile-on-completion

- [ ] Remove eager reload from send/resend flows
- [ ] Add reconcile-on-completion (debounced `listMessages()` after completion)
- [ ] Confirm duplicate message issue is resolved (no reload+event races)

## Files to touch (expected)

- `packages/frontend-sdk/src/chat/chatController.ts`
- `packages/frontend-sdk/src/events/pollingEventSource.ts`
- `packages/frontend-sdk-react/src/useChatController.ts`
- `mobile/crystal-lattice-control-rn/App.tsx` (cache persistence schema)
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` (scroll hook + remove reload)

## References

- Detailed plan: `plans/frontend-sdk/09-chat-persistence-scroll-and-reconcile.md`
