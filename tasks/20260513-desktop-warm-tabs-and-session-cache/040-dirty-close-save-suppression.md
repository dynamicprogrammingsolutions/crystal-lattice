# Dirty Close Save Suppression

Make close-time and unmount-time session-cache saves cheap by persisting only when the session entry materially changed since the last persisted version.

## Requirements checklist

- [ ] Make unchanged session-cache updates preserve object identity so reference equality can serve as the cheap dirty check.
- [ ] Track the last persisted session entry and skip writes when `currentEntry === lastPersistedEntry`.
- [ ] Apply the dirty-check contract to close/unmount persistence paths so inactive or closing tabs do not rewrite unchanged cache entries.
- [ ] Preserve persistence when session content actually changes, including message list, cursor/request state, range, draft text, or scroll anchor.
- [ ] Add or update tests for unchanged close, changed close, and repeated flushes that should become no-ops.

Parent Task: `tasks/20260513-desktop-warm-tabs-and-session-cache/000-main.md`
Depends On: `tasks/20260513-desktop-warm-tabs-and-session-cache/020-session-scoped-message-cache-persistence.md`

## Current state

- `ChatPane` flushes a snapshot on unmount in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:762-770`.
- Draft persistence flushes on unmount in `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatDraft.ts:162-166`.
- Scroll persistence flushes on unmount in `desktop/crystal-lattice-control-desktop-rn/src/chat/useProactiveChatScrollPersistence.ts:253-260`.
- `useMessagesCache` currently rebuilds session entries during updates in `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:96-137`, so there is no stable persisted-entry identity contract yet.

## Implementation notes

- This task pairs best with the session-scoped persistence refactor because dirty tracking is easier when each session has its own persisted record.
- `updateMessagesCache` should return the existing session entry reference when incoming content is materially unchanged.
- The comparison can stay cheap if it relies primarily on:
  - message-array reference equality
  - scalar equality for cursor/request/range/draft fields
  - a tiny structural equality helper for `scrollAnchor` if needed
- Seed `lastPersisted` tracking from hydrated entries so a freshly loaded session does not rewrite itself on first close unless it changed.

## Suggested test coverage

- A session that hydrates and closes without changes does not trigger a new persist.
- A session that changes messages, draft text, range, or scroll anchor does trigger a persist.
- Multiple unmount-style flushes with no intervening changes stay no-op after the first persisted version.