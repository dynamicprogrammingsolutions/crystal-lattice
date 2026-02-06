# Subtask: Session tabs + chat pane (main column)

Replace the main-column chat placeholder with a **minimal, working, multi-tab chat pane**.

This subtask intentionally targets a baseline that is:

- Correct w.r.t. controller lifecycle + cleanup.
- Correct w.r.t. event streaming (only the active tab streams).
- Usable offline (read-only transcript from cache).

Non-essential UX features and “mobile parity” are handled in follow-up subtasks (`081+`).

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/050-desktop-shell-layout.md`
- `tasks/20260202-desktop-macos-frontend/070-desktop-sessions-pane.md`

## Status

- [ ] Not started

## Requirements

- Multiple sessions can be open simultaneously as tabs.
- Tabs may belong to different connections.
- Switching tabs should be fast and should not lose controller state.
- Closing a tab cleans up resources (event polling, timers).
- Chat pane uses the SDK `ChatController` and reducer-driven event state.

Baseline behavior (minimal UI is OK):

- Active tab loads the most recent messages (default window such as last 50).
- Active tab can append+send messages.
- Only the active tab streams events (polling must stop when hidden).
- If a tab’s connection is closed, show cached transcript read-only.

UX hint:

- Use macOS hover/focus affordances for tab close buttons and action menus when possible.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

## Work plan

### Context to read first (files + line numbers)

- Desktop tabs state + placeholder panes (read 99–170 and 363–399): `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:99` and `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:363`
- Desktop messages cache contract + fields (read 14–143 and 12–21): `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:14` and `desktop/crystal-lattice-control-desktop-rn/src/cache/types.ts:12`
- Controller hook lifecycle + streaming gating (read 38–100): `packages/frontend-sdk-react/src/useChatController.ts:38`
- SDK controller cache snapshot + history window expectations (read 110–115 and 184–197): `packages/frontend-sdk/src/chat/chatController.ts:110` and `packages/frontend-sdk/src/chat/chatController.ts:184`
- Mobile reference for send flow (behavior only, no UI copy; read 214–260 and 552–606): `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:214` and `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:552`

### Implementation plan (detailed, minimal baseline)

#### 0) Keep the existing tab model in `DesktopRoot`

- `DesktopRoot` already has the correct tab identity (`${connectionId}:${sessionId}`) and neighbor selection behavior.
- Do not change tab semantics here; just replace the placeholder pane.

#### A) Replace the placeholder panes with real panes

1) Create a new desktop chat pane component.

- Add `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`.
- Props should be sufficient to support:
  - stable controller while tab exists
  - offline cached transcript
  - cache persistence callbacks

2) Update `DesktopRoot` to render the real chat pane instead of `ChatPanePlaceholder`.

- Replace the `tabs.map(...)` block in `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:389`.

#### B) Wire message cache into the chat pane

1) Start consuming message cache values in `DesktopRoot`.

- Update the `useMessagesCache(...)` destructuring in `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:95` to include:
  - `messagesCache`
  - `updateMessagesCache`

2) For each tab, derive:

- `backend = getBackend(tab.connectionId)`
- `cachedEntry = messagesCache[tab.connectionId]?.[tab.sessionId] ?? null`

3) Pass `cachedEntry` into `ChatPane` and pass an `onUpdateCache` callback that delegates to `updateMessagesCache`.

#### C) Controller lifecycle + active-only streaming

Inside `ChatPane`:

1) Create one controller per mounted pane.

- Use `useChatController({ backend, sessionId, initialMessages, initialEventsCursorId, initialActiveRequestId, eventsEnabled })`.
- `eventsEnabled` must be `visible && backend != null`.
- Controller is disposed automatically on unmount (`packages/frontend-sdk-react/src/useChatController.ts:51`).

2) Ensure the controller is windowed so it doesn’t grow unbounded.

- On controller creation, call `chatController.setHistoryRange({ start: -50 })` (or make the window size a constant).
- This matches the SDK expectation that the UI sets a window when hydrating from cache (`packages/frontend-sdk/src/chat/chatController.ts:110`).

3) On first activation, ensure we load messages.

- If `visible` becomes true and the controller snapshot has no cursor and no messages, call `loadMessages({ start: -50 })`.

#### D) Persist cache snapshots (minimal)

Inside `ChatPane`:

1) On snapshot changes, persist to cache.

- Read `chatController.getCacheSnapshot()` (`packages/frontend-sdk/src/chat/chatController.ts:184`).
- Call `onUpdateCache({ connectionId, sessionId, messages, cursorEventId, activeRequestId })`.
- Use a ref to avoid re-persisting the same snapshot every render.

2) Offline mode

- If `backend == null`, render `cachedEntry.messages` read-only.
- Disable composer send; show a subtle offline hint.

#### E) Minimal UI + error handling

- Transcript: Flat list of `IndexedMessage` with a basic row renderer.
- Composer:
  - `appendMessage({ role: 'user', content })` then `send()`.
  - Show error via `Alert` on failures.
- Request lifecycle:
  - Display `activeRequestId` state; allow cancel is deferred to `081`.

## Checklist (done criteria)

- [ ] `DesktopRoot` uses real `ChatPane` instead of `ChatPanePlaceholder`.
- [ ] Each open tab owns one stable `ChatController` (no recreation on tab switch).
- [ ] Only the active tab streams events (`eventsEnabled` gating).
- [ ] Closing a tab unmounts the pane and stops polling (`dispose()` path).
- [ ] Message cache is hydrated into controllers and persisted back via `updateMessagesCache`.
- [ ] Offline: closing the connection still shows cached transcript read-only.
- [ ] Manual verification: open 3 sessions, switch rapidly, send messages, close tabs; no hangs and no obvious background polling.

## Verification (manual)

- Open 3 sessions in tabs; switch rapidly; ensure no reload flash.
- Send a message in each tab; ensure only the active tab streams.
- Close a tab; ensure it no longer updates (polling stopped).
- Close a connection; ensure cached transcript remains visible read-only.
