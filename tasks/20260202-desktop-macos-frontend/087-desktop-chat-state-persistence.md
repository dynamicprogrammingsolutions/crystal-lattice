# Subtask: Persist per-tab chat UI state (draft + scroll + options)

Persist and restore chat UI state per tab, so switching tabs or going offline/online does not lose:

- Composer draft text
- Scroll anchor / pinned-to-bottom state
- (Optional) render option toggles from `081`

This should use the existing desktop messages cache entry fields (`composeText`, `scrollAnchor`) rather than introducing a new store.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/086-desktop-plugin-actions-in-chat.md`

## Status

- [x] Completed

## Context to read first (files + line numbers)

- Desktop messages cache entry fields (read 12–21): `desktop/crystal-lattice-control-desktop-rn/src/cache/types.ts:12`
- Desktop messages cache updater signature (needs extension; read 14–88): `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:17`
- Mobile scroll + draft persistence reference (read 172–213 and 900–925): `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:172` and `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:900`

## Requirements

- Draft text is restored when returning to a tab.
- Scroll position is restored when returning to a tab.
- Persisted state is scoped by `connectionId + sessionId`.

## Deliverables

### 1) Extend `useMessagesCache.updateMessagesCache` to support UI fields

- Update `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts` to accept optional:
  - `composeText?: string`
  - `scrollAnchor?: any`

### 2) Save and restore composer draft

- In `ChatPane`, persist `composeText` into the cache entry.
- Restore initial compose text from cache when mounting the pane.

### 3) Save and restore scroll anchor

- Define a lightweight scroll anchor shape (can mirror mobile’s “bottom gap + pinned-to-bottom” model).
- Persist it into `MessagesCacheEntry.scrollAnchor`.
- On first render of a re-activated tab, restore scroll offset.

### 4) Optional: persist render options

- If render options from `081` should persist, store them in the cache entry as well.
- Keep the shape stable and versioned (e.g. `renderOptionsV1`).

## Verification

- Type a draft in Tab A, switch to Tab B, then back: draft is restored.
- Scroll up in Tab A, switch away/back: scroll offset is restored.
- Restart the app: both draft + scroll restoration still work for cached tabs.

---

## Implementation plan (added during completion)

### 1) Extend messages cache updater to accept UI fields

File:

- `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts`

Changes:

- Extend `updateMessagesCache(params)` to accept optional:
  - `composeText?: string`
  - `scrollAnchor?: unknown`
- Merge into the existing entry (preserving prior values when omitted).

### 2) Introduce a typed scroll-anchor model (desktop-local, mirrors mobile)

File:

- `desktop/crystal-lattice-control-desktop-rn/src/chat/chatScroll.ts`

Exports:

- `ChatScrollAnchor` (`{ bottomGapPx: number; pinnedToBottom: boolean; updatedAtMs: number }`)
- `PINNED_TO_BOTTOM_THRESHOLD_PX`
- `isChatScrollAnchor(...)`
- `createChatScrollAnchor(...)`

Rationale: keep cache payload validated/stable while `MessagesCacheEntry.scrollAnchor` remains `unknown`.

### 3) Add hook: persisted composer draft (restore + debounce-save)

File:

- `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatDraft.ts`

Hook behavior:

- Initialize composer text from `cachedEntry?.composeText ?? ''`.
- If cache hydrates after mount, hydrate once (only if the user hasn’t typed yet) and update the native `MacTextView` via `ref.setText(...)`.
- Debounce persistence into `MessagesCacheEntry.composeText`; flush on unmount.

Integration goal:

- Keep `ChatPane` focused on rendering + existing send flow; draft persistence stays in the hook.

### 4) Add hook: persisted scroll anchor (capture + restore once)

File:

- `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatScrollAnchor.ts`

Hook behavior:

- Track `contentHeight`, `layoutHeight`, and `offsetY` from list events.
- Persist `{ bottomGapPx, pinnedToBottom, updatedAtMs }` into `MessagesCacheEntry.scrollAnchor` (debounced; flush on unmount).
- Restore scroll once per mount after both layout and content dimensions are known.

### 5) Small plumbing: allow transcript list components to accept an imperative ref

Files:

- `desktop/crystal-lattice-control-desktop-rn/src/ui/PlaceholderFlatList.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/ui/DependencyFlatList.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/ui/DependencyVirtualizedScroll.tsx`

Changes:

- Add `listRef?: React.Ref<any>` to `PlaceholderFlatListProps<TItem>` and pass it through to the underlying `ScrollView` / `FlatList` / `VirtualizedList`.

### 6) Wire hooks into `ChatPane`

File:

- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`

Changes:

- Use `usePersistedChatDraft` to control `composeText` + persistence.
- Use `usePersistedChatScrollAnchor` to capture/restore scroll state.
- Pass `listRef` and scroll handlers to the transcript component.

### Verification (manual)

- Draft: type in Tab A → switch to Tab B → back → draft restored.
- Scroll: scroll up in Tab A → switch away/back (or cold-start) → scroll restored.
- Restart app: reopen tab/session → draft + scroll restored from cache.

---

## Completion notes (added during completion)

- Draft persistence implemented via `usePersistedChatDraft` and cached `composeText`.
- Scroll persistence on macOS implemented via a native pull-based metrics module (`MacScrollViewMetrics`) since transcript `ScrollView` does not emit scroll events.
- Cached sessions no longer appear "in flight" on restart; `activeRequestId` is scrubbed during hydration.

Implementation details:

- Draft storage key: `MessagesCacheEntry.composeText`.
- Draft debug: set `globalThis.CLC_DEBUG_DRAFT_PERSIST = true` to log init/flush/restore.
- Scroll storage key: `MessagesCacheEntry.scrollAnchor` (stored as `ChatScrollAnchor` from `desktop/.../src/chat/chatScroll.ts`).
- Scroll persistence triggers:
  - `isActive` transitions `true -> false` (tab deactivated)
  - unmount cleanup (covers tab close / app quit)
- Scroll restore trigger: `isActive` transitions `false -> true` (reset + restore).
