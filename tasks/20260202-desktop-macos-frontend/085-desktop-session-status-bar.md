# Subtask: Session status bar (desktop; UI-schema driven)

Add the session-level “status bar” row to the desktop chat pane.

This is the small line of session data derived from **session UI schema** elements (`ui_type: "status_bar"`) and the last assistant message. It mirrors the mobile session chat status bar behavior, but is rendered in a desktop-friendly location.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/084-desktop-rich-assistant-rendering.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Mobile reference: status bar composition + rendering (read 880–1105):
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:880`
- SDK helpers used by mobile:
  - `deriveChatStatusBarParts`: `packages/frontend-sdk/src/chat/presentation.ts:1`
  - `filterStatusBarElements`: `packages/frontend-sdk/src/utils/uiSchema.ts:33`
  - `selectLastAssistantMessage`: `packages/frontend-sdk/src/chat/presentation.ts:1`
- Desktop chat pane (target):
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:1`

## Requirements

- When online, desktop loads the session UI schema and derives a list of status parts from:
  - `sessionId`
  - the current session agent id (if available)
  - last assistant message (including streaming row when present)
  - UI schema `status_bar` elements
- Status bar updates as new assistant messages stream in / complete.
- Offline mode does not crash; it may show only static parts (e.g. session id) when UI schema is unavailable.

## Deliverables

### 1) Load UI schema + extract status-bar elements

- In `desktop/.../ChatPane.tsx`, use `useSessionUiSchemaController(...)` (same as mobile) and derive:
  - `statusBarElements = filterStatusBarElements(uiSchemaElements)`

### 2) Compute status parts

- Use the shared helper `deriveChatStatusBarParts(...)` from `@crystal-lattice/frontend-sdk`.
- Use `selectLastAssistantMessage({ messages, streamingRow })` so the status bar can react to streaming output.

### 3) Wire in session agent id (match mobile semantics)

- Use the same logic mobile uses:
  - Fetch/store `sessionAgentId` (via `backend.getSessionAgent(sessionId)` when online).
  - Load agents list when online (via `useAgentsController.ensureLoaded()`) so `deriveChatStatusBarParts` can decide whether to show the agent label.
- Keep this lightweight: load once per tab mount / when connection changes; re-load after a successful agent switch.

### 4) Render the status bar row (desktop)

- Render a single compact row (e.g. monospace, muted color) at the bottom of the chat pane.
- Placement: below the composer (so it stays visible and does not scroll with the transcript).
- The row should join parts with spacing similar to mobile (`parts.join('   ')`).

## Verification

- With a backend that provides session UI schema `status_bar` elements, open a session and confirm the status bar shows derived fields.
- Trigger a response that updates assistant message metadata and confirm the status bar updates.
- Switch the session agent and confirm the agent label updates (when the agent id is recognized by the agents list).

## Plan (added during completion)

### Decisions

- Keep the existing debug `statusRow` (“Messages/Streaming”) as-is.
- Render the new session status bar at the very bottom of the chat pane (below the composer).
- Avoid growing `ChatPane.tsx` further by extracting status-bar logic into a custom hook that returns `statusBarParts`.

### Implementation steps

1) Add a desktop hook to compute status bar parts

- Create `desktop/crystal-lattice-control-desktop-rn/src/chat/useSessionStatusBarParts.ts` exporting:
  - `useSessionStatusBarParts({ backend, connectionId, sessionId, isActive, uiSchemaElements, messages, streamingRow, sessionSummary })`
  - Return shape: `{ statusBarParts: string[] }` (optionally also return `statusBarText` as a joined string).

Hook responsibilities:

- `ChatPane.tsx` remains the single place that loads UI schema (it already uses `useSessionUiSchemaController` for message footer elements); it passes `uiSchemaElements` into this hook.
- Load agents list (online + active only) via `useAgentsController({ backend, cacheKey: connectionId, enabled: !!(backend && isActive) })`.
- Track `sessionAgentId` with the same semantics as mobile:
  - Prefer `(sessionSummary?.metadata as any)?.agent_id` when present.
  - Otherwise, best-effort fetch via `backend.getSessionAgent(sessionId)` when online.
  - Re-load/update when the session agent is successfully switched.
- Compute:
  - `statusBarElements = filterStatusBarElements(uiSchemaElements)`
  - `lastAssistantMessage = selectLastAssistantMessage({ messages, streamingRow })`
  - `statusBarParts = deriveChatStatusBarParts({ sessionId, sessionAgentId, availableAgents, lastAssistantMessage, statusBarElements })`

2) Make agent switching observable so the status bar updates

- Extend `desktop/crystal-lattice-control-desktop-rn/src/events/desktopEventBus.ts` with:
  - `sessionAgentSwitched: { connectionId: string; sessionId: string; agentId: string }`
- In `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx` `agentPickerSelected` handler:
  - When `mode === 'switchSessionAgent'`, call `backend.switchSessionAgent(...)` and on success publish `sessionAgentSwitched`.
- In `useSessionStatusBarParts`, subscribe to `desktopEventBus` and update `sessionAgentId` when the event matches the current `(connectionId, sessionId)`.

3) Render the status bar below the composer (desktop)

- In `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`:
  - Call `useSessionStatusBarParts(...)` and render a compact status row after the composer area.
  - Keep the existing debug `statusRow` at the top of the body.

Visual spec (desktop; concrete defaults):

- Placement: below composer, inside the pane’s padded body.
- Container:
  - `borderTopWidth: 1`, `borderTopColor: theme.border`
  - `paddingTop: 8` (to visually separate from composer)
  - `paddingHorizontal: 0` (reuse body padding)
- Text row:
  - `fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier'`
  - `fontSize: 11`
  - `color: theme.textSecondary`
  - `numberOfLines={1}` with tail ellipsis to keep it “status bar” sized
  - Content joins with spacing: `statusBarParts.join('   ')`

4) Verification (manual)

- Open a session with `ui_type: "status_bar"` UI schema elements and confirm the bar renders at the bottom.
- Start streaming: confirm the bar updates while streaming (driven by `streamingRow`).
- Switch agent: confirm the `Agent: ...` label updates after the switch completes.
- Go offline (`backend == null`): confirm no crash and at least `Session: XXXXXXXX` is shown.

### Optional tests

- Add a focused unit test for `deriveChatStatusBarParts` and/or `selectLastAssistantMessage` in `packages/frontend-sdk/src/chat/__tests__/...` to lock semantics.
