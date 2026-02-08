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

- Render a single compact row (e.g. monospace, muted color) near the top of the chat pane.
- Suggested placement:
  - Under the chat header, above the transcript scroll area (so it stays visible while scrolling).
- The row should join parts with spacing similar to mobile (`parts.join('   ')`).

## Verification

- With a backend that provides session UI schema `status_bar` elements, open a session and confirm the status bar shows derived fields.
- Trigger a response that updates assistant message metadata and confirm the status bar updates.
- Switch the session agent and confirm the agent label updates (when the agent id is recognized by the agents list).
