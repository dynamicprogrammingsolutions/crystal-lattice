# Subtask: Session tabs + chat pane (main column)

Implement the main column:

- Session tab strip (multiple open sessions)
- Chat pane for the active tab

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

UX hint:

- Use macOS hover/focus affordances for tab close buttons and action menus when possible.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

## Work plan

### 1) Tab state model

- Keep in desktop app state:
  - `tabs: Array<{ tabId: string; connectionId: string; sessionId: string; title: string }>`
  - `activeTabId: string | null`

Rules:

- Opening a session that’s already open focuses it.
- Closing the active tab focuses the nearest neighbor.

Tab identity:

- Use `{ connectionId, sessionId }` as the logical identity.
- Recommended `tabId`: `${connectionId}:${sessionId}`.

### 2) Controller lifecycle strategy (important)

We need a stable controller per open session.

Additionally, because tabs can belong to different connections:

- The per-tab controller needs to be created with the correct `AgentBackend` for that connection.
- Closing a tab must clean up only that tab’s controller + streaming.

Two viable options:

- Option A (recommended): keep a `Map<sessionId, ChatController>` in a `useRef` and manually create/cleanup.
  - Pros: stable controllers, explicit cleanup.
  - Cons: more manual wiring.

- Option B: render a `ChatTab` component per open session which owns its controller.
  - Pros: idiomatic React, cleanup via unmount.
  - Cons: you must ensure non-active tabs don’t keep expensive work running.

### 3) Event streaming behavior

- Ensure polling starts only when:
  - a session tab becomes active, OR
  - the chat controller already has a cursor snapshot.

We already had issues on mobile with polling start timing; prefer reusing the SDK logic.

### 4) Chat pane UI

Desktop-specific chat UI should be simple initially:

- transcript list
- composer

Shared components should cover “in-between” elements:

- message actions menu / pinned actions bar
- session actions menu

Do not force sharing of the markdown renderer.

### 5) Settings dropdowns (no modal)

Implement settings as dropdowns anchored in the chat header (desktop-friendly), e.g.:

- Agent selector dropdown
- Render options dropdown (markdown on/off, show reasoning, tool result formatting)

Implementation hint:

- A JS overlay-based dropdown is a good Phase 5 baseline.
- Keep the rendering layer swappable if a native `NSMenu`/`NSPopover` approach is introduced later.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

## Verification

- Open 3 sessions, switch rapidly, send messages in each; no hangs.
- Close tabs; verify no background polling remains for closed sessions.
