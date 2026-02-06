# Subtask: Chat header + session actions (desktop dropdowns)

Add a desktop-first chat header to each open chat tab (main column), including:

- Agent selector dropdown (switch the agent for the current session)
- Render options dropdown (desktop-local toggles; no persistence yet)
- A small set of essential session actions (reload, cancel)

This task builds on the minimal working chat pane from `080`.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/080-desktop-chat-tabs-and-chat-pane.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Chat pane baseline + tab mounting model (read 363–399): `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:363`
- Dropdown surface implementation (JS overlay; read 72–202): `packages/frontend-rn-components/src/actions/MenuSurfaces.tsx:72`
- Agents controller hook (load + cache key; read 16–38): `packages/frontend-sdk-react/src/useAgentsController.ts:16`
- Backend agent APIs (read 38–42): `packages/frontend-sdk/src/backend/backend.ts:38`
- ChatController reload/cancel APIs (read 199–234): `packages/frontend-sdk/src/chat/chatController.ts:199` and `packages/frontend-sdk/src/chat/chatController.ts:228`
- Mobile reference for agent switching behavior (logic only; read 649–725): `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:649`

## Requirements

- Chat header is visible in the active tab pane.
- Header controls must be dropdown/anchored (desktop-friendly); do not use full-screen modals.
- Switching the agent should call `backend.switchSessionAgent(sessionId, agentId)`.
- Render options are local UI toggles that affect rendering in the chat pane.

## Deliverables

### 1) Header layout

- Add a header row to `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` (created in `080`).
- Show:
  - session title + connection label
  - online/offline state

### 2) Agent dropdown (Option B)

- Add an anchored dropdown that:
  - loads agents via `useAgentsController({ backend, cacheKey: connectionId, enabled: visible })`
  - loads current session agent via `backend.getSessionAgent(sessionId)` (only when needed)
  - switches via `backend.switchSessionAgent(sessionId, agentId)`

Notes:

- Keep the UI responsive: show a small loading state while switching.
- If the connection is offline, disable agent switching.

### 3) Render options dropdown (Option B)

- Add an anchored dropdown with desktop-local toggles. Initial suggested toggles:
  - `renderMarkdown` (used by `083`)
  - `showReasoning` and `showToolCalls` (used by `084`)

Storage:

- Keep render options in component state for now.
- Persistence is handled later in `087`.

### 4) Essential session actions

- Add simple actions (can be buttons or a small dropdown):
  - Reload: `chatController.clearRequestState(); chatController.loadMessages({ start: -50 })`
  - Cancel: `chatController.cancelActiveRequest()` (only enabled when `activeRequestId != null`)

## Verification

- Switch agent while a session tab is active; confirm backend call succeeds and UI reflects the selection.
- Toggle render options; confirm state updates (rendering changes are implemented in `083`/`084`).
- Start a request and cancel it; confirm request stops and no crashes.
