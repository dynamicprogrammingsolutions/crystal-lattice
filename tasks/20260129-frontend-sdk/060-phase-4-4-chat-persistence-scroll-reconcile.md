# Phase 4.4 — Chat scroll anchoring and restoration

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/050-phase-4-headless-controllers.md`

Fix chat scroll restoration so it defaults to bottom when unknown and preserves reading position as messages update.

Note: message-state correctness (event schema, reducer, dirty fallback, removing reloads) moved to Phase 4.5:

- `tasks/20260129-events-no-full-session/000-main.md`

This phase is not implemented yet; it’s the next intended cleanup step.

## Status

- [ ] Not started

## Problems to solve (current behavior)

### 1) Scroll restore defaults to top too often

- The app persists a raw `scrollOffset` and uses `0` as the default.
- `0` is ambiguous (top vs unknown) so the UI tends to restore to top.

Current restore logic (for reference):

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:805`
  - `onScroll` updates `scrollOffsetRef.current`
  - `onContentSizeChange` restores only when `initialScrollOffset > 0` and otherwise tends to fall back to the top

Current persistence wiring (for reference):

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:411` (unmount effect calls `onSaveScrollOffset(scrollOffsetRef.current)`)
- `mobile/crystal-lattice-control-rn/App.tsx:358` (`saveMessagesScrollOffset` writes `scrollOffset` into `messagesCache`)

### 2) Auto-scroll fights restoration / user reading

- Auto-scroll on new content can fight the user's reading position.
- The UI needs a clear “pinned to bottom vs reading history” state.

## Target design (what should exist after this phase)

### A) Scroll persistence uses a bottom-anchor model

- Persist `bottomGapPx` (distance from bottom) and whether user is “pinned to bottom”.
- When state is missing/unreliable, default to bottom.

### B) Default-to-bottom semantics

- If scroll position is missing/unreliable, the chat view should open at bottom.
- When pinned-to-bottom, new messages keep the view at bottom.
- When not pinned-to-bottom, new messages should not yank the viewport.

## Work breakdown checklist

### Stage 4.4.1 — Scroll anchor persistence

- [ ] Replace `scrollOffset` persistence with `bottomGapPx` + `pinnedToBottom`
- [ ] Default to bottom when anchor is missing/unreliable
- [ ] Ensure scroll restoration doesn’t fight with “new message auto-scroll” behavior

### Stage 4.4.2 — Auto-scroll policy

- [ ] Track “pinned to bottom” with a threshold (e.g. within N px of bottom)
- [ ] Only auto-scroll on new messages when pinned
- [ ] Ensure restore runs once and then stops fighting user scroll

## Files to touch (expected)

- `mobile/crystal-lattice-control-rn/App.tsx` (scroll persistence schema)
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

## References

- Detailed plan: `plans/frontend-sdk/09-chat-persistence-scroll-and-reconcile.md`
- Phase 4.5 (events/reducer/no reloads): `tasks/20260129-events-no-full-session/000-main.md`
