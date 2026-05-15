# File-Backed Cache Storage Evaluation

Evaluate and, if approved, implement a real file-backed storage path for the standardized session message cache instead of relying only on AsyncStorage keys.

## Requirements checklist

- [ ] Confirm whether true file-backed persistence should replace or augment the standardized per-session AsyncStorage design, and document the answer separately for desktop and mobile.
- [ ] If approved, introduce a file-backed storage adapter for standardized session cache entries, with platform-specific implementations where needed.
- [ ] Define storage location, naming, indexing, and cleanup behavior for per-session cache files while preserving the shared logical cache format from task `020`.
- [ ] Keep the implementation scoped to app/platform layers so the generic frontend SDK `KeyValueStore` contract does not need unrelated file-system concerns.
- [ ] Add or update tests for the chosen adapter and any migration or fallback behavior on each affected platform.
- [ ] If platform or dependency constraints block the implementation, document the blocker and the intended fallback explicitly in the completion notes.

Parent Task: `tasks/20260513-desktop-warm-tabs-and-session-cache/000-main.md`
Depends On: `tasks/20260513-desktop-warm-tabs-and-session-cache/020-session-scoped-message-cache-persistence.md`

## Current state

- The desktop app currently depends on `@react-native-async-storage/async-storage` and does not include a file-system package in `desktop/crystal-lattice-control-desktop-rn/package.json`.
- The generic storage abstraction is still only `get/set/delete` in `packages/frontend-sdk/src/storage/keyValueStore.ts:1-5`.
- Existing desktop native modules such as `desktop/crystal-lattice-control-desktop-rn/src/native/MacScrollViewMetrics.ts` show there is already a pattern for adding desktop-specific native functionality if needed.
- Mobile already has `react-native-fs` available in `mobile/crystal-lattice-control-rn/package.json`, but transcript/session cache persistence still uses AsyncStorage in `mobile/crystal-lattice-control-rn/App.tsx:287-350`.

## Design questions to settle

- Should the file-backed cache be a pure app implementation detail, or should it become a reusable storage module with separate desktop/mobile adapters under each app's `src/storage` area?
- Is a directory of JSON files plus one manifest/index enough, or is a manifest-free directory scan acceptable for startup and cleanup?
- Should AsyncStorage remain the fallback for platforms that do not get a file-backed implementation immediately?
- How should migration from standardized per-session AsyncStorage keys to files be handled if the file-backed version ships?

## Suggested test coverage

- Adapter tests for read, write, delete, and clear semantics.
- Migration tests if an AsyncStorage-to-files migration is implemented.
- A failure-path test proving that partial file errors do not corrupt the in-memory cache model or crash hydration.
- If mobile gets a file-backed implementation too, coverage should prove it still reads and writes the same logical cache format as desktop task `020`.