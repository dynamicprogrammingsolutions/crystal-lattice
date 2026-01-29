# Mobile frontend: remove unconditional reloads; add dirty UI + manual reload

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/060-chatcontroller-integration.md`

Update the mobile RN chat UI so it does not reload messages as part of the normal workflow. All updates should flow from events applied via the SDK reducer.

## Status

- [ ] Not started

## Current behavior to remove

File: `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

- `handleSend()` does: append user message → send → `loadMessages()` (`mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:441`)
- `handleResend()` does: send → `loadMessages()`

These reloads can cause duplicates and are unnecessary once events are applied robustly.

## Required behavior

- Send/resend/cancel should not call `loadMessages()`.
- Message list should update only from controller state (event-driven).
- If the controller reports `dirty`, show a banner/button:
  - "Out of sync — Reload"
- Reload is triggered only:
  - by explicit user action, or
  - by a policy decision when `dirty` is set (optional; prefer manual)

## Work checklist

- [ ] Remove `loadMessages()` from send/resend paths
- [ ] Ensure user message becomes visible via events (append event) or optimistic local append
- [ ] Update cache persistence to store controller snapshot (messages + poll cursor)
- [ ] Add dirty banner + manual reload button
