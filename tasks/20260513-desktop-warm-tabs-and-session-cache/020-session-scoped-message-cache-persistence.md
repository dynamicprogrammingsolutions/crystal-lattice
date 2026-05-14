# Session-Scoped Message Cache Persistence

Standardize message-cache persistence across the desktop and mobile apps so each session is stored independently instead of serializing the entire message cache into one AsyncStorage value.

## Requirements checklist

- [x] Replace the monolithic `clc_messages_cache_v1` persistence model with per-session persisted entries plus a lightweight index.
- [x] Standardize the message-cache format and storage-key conventions so the same logical model applies to both the desktop app and the mobile app.
- [x] Keep the in-memory `messagesCache` shape compatible with current desktop and mobile consumers.
- [x] Save only the touched session when cache data changes.
- [ ] Support hydration, targeted delete-by-connection, and clear-all behavior with the new storage layout.
- [x] Decide whether to migrate old `clc_messages_cache_v1` data, and if migration is kept, test it.
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

## Execution plan

Added during completion planning.

1. Extract shared message-cache persistence helpers into `packages/frontend-sdk/src/storage`.
   - Add a canonical v2 index key for the set of persisted session entries.
   - Add a canonical v2 per-session key format derived from `connectionId` and `sessionId`.
   - Keep the external in-memory cache shape unchanged as `messagesCache[connectionId]?.[sessionId]`.
2. Define one normalized persisted entry format for both desktop and mobile.
   - Persist `connectionId`, `sessionId`, `messages`, `lastLoadedAt`, `cursorEventId`, `activeRequestId`, `composeText`, `scrollAnchor`, `rangeStartText`, and `rangeEndText`.
   - Normalize older in-memory/mobile field usage to canonical `cursorEventId` at the shared persistence boundary.
   - Scrub `activeRequestId` to `null` during hydration so restarted apps do not present stale in-flight requests.
3. Intentionally skip v1 migration.
   - Do not read or convert `clc_messages_cache_v1`.
   - Treat the old monolithic value as discarded transient cache data and hydrate only from the new v2 layout.
4. Refactor desktop cache state to use targeted persistence instead of whole-cache writes.
   - Replace the `useEffect` that serializes the entire cache after every state change.
   - On each `updateMessagesCache` call, compute the next in-memory state, persist only the touched session entry, and delete any entries evicted by per-connection pruning.
   - Apply the same targeted persistence flow to `deleteConnectionMessagesCache` and `clearMessagesCache`.
5. Refactor mobile cache state around the same shared persistence helpers.
   - Extract the message-cache load/save/update/delete logic from `mobile/crystal-lattice-control-rn/App.tsx` into a focused hook or module.
   - Add a hydration gate before any persistence writes so startup cannot overwrite stored data with the initial empty state.
   - Preserve the current consumer-facing data shape and callbacks used by `ConnectedRoot` and `SessionChatScreen`.
6. Keep pruning policy app-owned, not persistence-owned.
   - Desktop can continue capping cached sessions per connection at 50.
   - Mobile can continue capping cached sessions per connection at 10 unless separately changed.
   - The shared persistence layer should write exactly the sessions retained by each app state layer.
7. Add tests at the shared and integration edges.
   - Add `vitest` coverage in `packages/frontend-sdk` for hydrate, targeted update, delete-by-connection, clear-all, malformed data tolerance, and index consistency after eviction.
   - Add desktop coverage for hook-level hydrate and targeted persistence behavior.
   - Add mobile coverage for hydrate gating and per-session persistence behavior after extracting the cache module/hook.

## Completion Notes

Added during completion.

- Implemented shared v2 session-scoped message-cache persistence in `packages/frontend-sdk/src/storage/sessionScopedMessagesCache.ts` with one index key plus one per-session entry key.
- Rewired desktop `useMessagesCache` to hydrate from the shared v2 layout, scrub persisted `activeRequestId`, persist only the touched session, and clean up evicted or deleted entries without serializing the whole cache.
- Extracted a mobile `useMessagesCache` hook that uses the same shared v2 layout, adds a hydration gate before persistence writes, preserves current consumer-facing `messagesCache[connectionId]?.[sessionId]` access, and keeps the mobile compatibility alias `eventsCursorId` in memory while persisting canonical `cursorEventId`.
- Intentionally skipped `clc_messages_cache_v1` migration. Old monolithic cache blobs are now discarded as transient, recoverable data.
- Added focused tests for shared storage behavior plus desktop and mobile hook integrations.
- Verification run:
  - `npm test -- --run src/storage/sessionScopedMessagesCache.test.ts` in `packages/frontend-sdk`
  - `npm test -- --runInBand __tests__/useMessagesCache.test.tsx` in `desktop/crystal-lattice-control-desktop-rn`
  - `npm test -- --runInBand __tests__/useMessagesCache.test.tsx` in `mobile/crystal-lattice-control-rn`
- `npx tsc --noEmit` still reports unrelated pre-existing errors in `packages/frontend-sdk`, `desktop/crystal-lattice-control-desktop-rn`, and `mobile/crystal-lattice-control-rn`; none of the reported failures were in the new cache implementation after the local type import/test fixes.

## Follow-up Plan

Added after review findings identified remaining gaps before this task can be considered fully complete.

1. Rework the hydration gate in desktop and mobile cache hooks so pre-hydration writes queue mutation intents rather than persistence closures.
   - Load hydrated v2 cache first.
   - Replay queued mutations against the hydrated in-memory state.
   - Persist the rebased result after replay so startup writes cannot clobber previously stored transcripts, drafts, or scroll state.
2. Refactor cache mutation paths around a shared per-hook state transition helper.
   - Have each mutation return the next in-memory cache plus the specific session writes and deletes needed for persistence.
   - Use the same transition path for transcript updates, compose text updates, scroll-anchor updates, delete-by-connection, and clear-all.
3. Restore mobile per-connection pruning on every path that can create a cache entry.
   - Apply the 10-session cap not only in `updateMessagesCache`, but also in compose-text and scroll-anchor upserts.
   - Delete any evicted session entries from persisted storage as part of the same operation.
4. Expand app-level tests to cover the missing integration cases.
   - Add desktop and mobile hook tests for pre-hydration queued writes rebasing over hydrated cache state.
   - Add desktop and mobile hook tests for delete-by-connection and clear-all behavior.
   - Add a mobile regression test proving compose-text or scroll-anchor writes still enforce the 10-session cap.