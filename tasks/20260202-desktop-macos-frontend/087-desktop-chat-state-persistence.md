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

- [ ] Not started

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
