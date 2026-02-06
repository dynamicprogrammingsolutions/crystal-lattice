# Subtask: Chat header + session actions (desktop)

Add a desktop-first chat header to each open chat tab (main column), focused on:

- A more informative header (title + IDs + connection label)
- A pinnable session actions bar (same UI as the sessions list) with:
  - Reload
  - Cancel
  - Agent switch

Intentionally skip render options toggles for now.

This task builds on the minimal working chat pane from `080`.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/080-desktop-chat-tabs-and-chat-pane.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Chat pane baseline + tab mounting model (read 363–399): `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:363`
- Existing desktop chat pane baseline (header + status row; read 331–414): `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:331`
- Connection name source (read 384–418): `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:384`
- ChatController reload/cancel APIs (read 129–212): `packages/frontend-sdk/src/chat/chatController.ts:129`
- Desktop sessions list actions UI (pinnable actions bar; read 648–711): `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:648`
- Actions menu bar implementation (macOS popover support; read 1–220): `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx:1`
- Desktop agent picker window (read 1–120): `desktop/crystal-lattice-control-desktop-rn/src/windows/AgentPickerWindow.tsx:1`
- Desktop agent picker event handling (read 206–260): `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:206`

## Requirements

- Chat header is visible in the active tab pane.
- Header shows: title, session id, connection name, and subtitle (if present).
- Add a pinnable actions affordance in the header using the same UI element as the sessions list.
- Built-in actions to support now:
  - Reload
  - Cancel
  - Agent switch
- Agent switching must call `backend.switchSessionAgent(sessionId, agentId)`.
- Actions must be desktop-friendly (compact header buttons + dropdown/popover; no full-screen modals).

## Deliverables

### 1) Header layout (desktop)

- Add a header row to `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` (created in `080`).
- Show (at minimum):
  - title
  - session id
  - connection name
  - subtitle (if provided)
  - online/offline state

Temporary (for visual testing; will be superseded by the session-metadata unification task):

- When opening a tab from the sessions list, pass the same subtitle that is rendered in the sessions list.
- When the sessions list is refreshed/updated, update title + subtitle for any open tabs that match by `sessionId`.

### 2) Session actions bar (pinnable): reload + cancel + agent switch

- Use the same UI primitive as the sessions list:
  - `ActionsMenuBar` from `@crystal-lattice/frontend-rn-components`.

- Add built-in action definitions:
  - `reload` (refresh icon)
  - `cancel` (stop icon)
  - `agentSwitch` (user icon)

- Persist pinned actions per connection using `usePersistentPinnedActions` + `asyncStorageKeyValueStore` (same approach as sessions list).

- Wire action handlers:
  - Reload: `chatController.clearRequestState(); chatController.loadMessages({ start: -50 })`
  - Cancel: `chatController.cancelActiveRequest()` (only enabled when `activeRequestId != null`)
  - Agent switch: open an agent picker and, upon selection, call `backend.switchSessionAgent(sessionId, agentId)`.

Notes:

- Track a small `inFlight` state per button (optional) to prevent double-clicks.
- If the connection is offline (`backend == null`), disable all actions.

### 3) Agent picker support for "switch agent" (desktop window)

- Reuse the existing desktop `AgentPickerWindow` UI, but extend it so it can support both:
  - creating a new session (existing behavior)
  - switching the agent for an existing session (new behavior)

Suggested approach:

- Extend `desktop/crystal-lattice-control-desktop-rn/src/windows/AgentPickerWindow.tsx` props to accept:
  - `mode: 'createSession' | 'switchSessionAgent'`
  - `sessionId?: string`
  - `title?: string` and/or `primaryButtonLabel?: string`
  - `initialAgentId?: string` (so we can preselect the current session agent)

- When `mode === 'switchSessionAgent'`, submit payload via `DesktopWindowManager.submitAgentPicker` including `{ connectionId, sessionId, agentId, mode }`.

- Update the `agentPickerSelected` handler in `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx` so it branches:
  - `mode === 'switchSessionAgent'` + `sessionId` present:
    - call `getBackend(connectionId)?.switchSessionAgent(sessionId, agentId)`
  - otherwise keep the existing "new session" behavior (create session + open tab).

## Verification

- Ensure header shows title/session id/connection name/subtitle correctly for several tabs.
- Click Reload; confirm messages re-fetch and no crashes.
- Start a request and click Cancel; confirm request stops and no crashes.
- Pin/unpin actions; confirm pins persist per connection across restarts.
- Run Agent switch; confirm the backend call succeeds and subsequent sends use the new agent.
- Refresh the sessions list; confirm any open tab titles/subtitles update.

## Detailed implementation plan

### A) Pass `connectionName` into `ChatPane`

Files:

- `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`

Steps:

1) Add a new `connectionName: string | null` prop to `ChatPaneProps`.

2) In `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:384`, pass the resolved connection name to each pane:

- `connectionName={connectionNameById[tab.connectionId] ?? tab.connectionId}`

Rationale: `ChatPane` already receives `connectionId` for cache keys; `connectionName` is purely presentation.

### B) Build a desktop header row with stacked metadata + action buttons

File:

- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`

Steps:

1) Replace the existing header block (`styles.header`, currently title + optional subtitle) with a two-column header:

- Left: a text stack with:
  - Title (existing `title`)
  - A compact meta row: `connectionName` + `sessionId`
  - Subtitle (existing `subtitle`, only if present)
- Right: session actions bar using `ActionsMenuBar` (pinnable), with built-in actions (Reload, Cancel, Agent switch).

2) Add an online/offline indicator in the header (e.g., a small dot + label). Use:

- `backend != null` to determine online.
- `theme.success` for online and `theme.textMuted` (or `theme.border`) for offline.

3) Keep the existing transcript/composer layout unchanged.

Optional tidy-up:

- Remove or simplify the existing `statusRow` that repeats online/offline (`ChatPane.tsx:345`). If kept, ensure it doesn’t duplicate the header info.

### C) Implement session action handlers (reload/cancel/agent switch)

File:

- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`

Steps:

1) Add `handleReload()`:

- Guard: if `!chatController || !backend` return.
- Execute:
  - `chatController.clearRequestState()`
  - `await chatController.loadMessages({ start: -DEFAULT_HISTORY_WINDOW })`
- On error: reuse existing load error behavior (`setLoadError(...)` + `Alert.alert(...)`).

2) Add `handleCancel()`:

- Guard: if `!chatController || !backend` return.
- Guard: if `chatState?.activeRequestId == null` return.
- Execute: `await chatController.cancelActiveRequest()`.
- On error: `Alert.alert('Failed to cancel', message)`.

3) Button enablement:

- Reload enabled when `backend != null && chatController != null`.
- Cancel enabled when `backend != null && chatController != null && chatState?.activeRequestId != null`.

4) Agent switch enablement:

- Disable when `backend == null`.
- Optional: disable while `chatState?.activeRequestId != null` to avoid switching mid-request.

5) Map action keys from `ActionsMenuBar`:

- `reload` → `handleReload()`
- `cancel` → `handleCancel()`
- `agentSwitch` → open agent picker in `switchSessionAgent` mode (load agents via `useAgentsController.ensureLoaded()`, optionally fetch `backend.getSessionAgent(sessionId)` for preselect).

### D) Styling + ergonomics

1) Use `Pressable` hover styles (like `desktop/crystal-lattice-control-desktop-rn/src/ui/PanelHeader.tsx`) so the header actions feel desktop-native.

2) Optional: use `react-native-vector-icons/Feather` icons for actions (consistent with `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:12`).

## Notes / explicit non-goals

- Do not add render options toggles in this subtask (markdown/reasoning/tool-call toggles can be introduced later when we decide where they live).
- Ignore any temporary composer debugging in the working tree; it’s out of scope for this subtask.
