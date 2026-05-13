# Session-Scoped Message Cache Persistence

Standardize message-cache persistence across the desktop and mobile apps so each session is stored independently instead of serializing the entire message cache into one AsyncStorage value.

## Requirements checklist

- [ ] Replace the monolithic `clc_messages_cache_v1` persistence model with per-session persisted entries plus a lightweight index.
- [ ] Standardize the message-cache format and storage-key conventions so the same logical model applies to both the desktop app and the mobile app.
- [ ] Keep the in-memory `messagesCache` shape compatible with current desktop and mobile consumers.
- [ ] Save only the touched session when cache data changes.
- [ ] Support hydration, targeted delete-by-connection, and clear-all behavior with the new storage layout.
- [ ] Decide whether to migrate old `clc_messages_cache_v1` data, and if migration is kept, test it.
- [ ] Add or update tests for hydrate, update, delete-by-connection, clear-all, and any retained migration path in the shared logic and in affected app integrations.

Parent Task: `tasks/20260513-desktop-warm-tabs-and-session-cache/000-main.md`

## Current state

- `useMessagesCache` persists the whole cache via `JSON.stringify(messagesCache)` in `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:69-78`.
- Cache updates are currently merged into one nested in-memory object in `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:80-140`.
- Current storage keys are defined in `desktop/crystal-lattice-control-desktop-rn/src/cache/storageKeys.ts:1-2`.
- Consumers expect `messagesCache[connectionId]?.[sessionId]`:
  - `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:154`
  - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:350-366`
- Mobile currently uses the same monolithic pattern for transcript cache persistence:
  - key definitions in `mobile/crystal-lattice-control-rn/App.tsx:64-65`
  - whole-cache hydrate in `mobile/crystal-lattice-control-rn/App.tsx:287-308`
  - whole-cache save in `mobile/crystal-lattice-control-rn/App.tsx:337-350`
  - in-memory per-session updates in `mobile/crystal-lattice-control-rn/App.tsx:363-407`
- Mobile consumers also expect `messagesCache[connectionId]?.[sessionId]`, for example in `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx:231-272`.

## Implementation notes

- A likely v2 shape is:
  - one index key that lists persisted session records
  - one storage key per `connectionId/sessionId` entry
- Prefer extracting shared cache persistence logic or conventions so desktop and mobile do not drift again.
- Keep the public hook/API shape the same so `DesktopRoot`, `ChatPaneTabStack`, and mobile consumers such as `ConnectedRoot` do not need a broad refactor.
- Deletes should use the index to remove only the affected connection or session entries.
- If migration from v1 is implemented, do it once at hydration time and then write back the v2 layout.

## Suggested test coverage

- Hydrating a v2 index plus multiple per-session entries reconstructs the in-memory cache correctly.
- Updating one session writes only that session entry and leaves other persisted sessions untouched.
- `deleteConnectionMessagesCache(connectionId)` removes only sessions for that connection.
- `clearMessagesCache()` removes the index and all tracked session entries.
- If v1 migration is kept, a regression test verifies the old blob can be imported once and normalized to the new layout.
- Mobile integration coverage verifies the mobile app can hydrate and persist the same standardized layout.