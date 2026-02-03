# Subtask: Desktop sessions pane (left column bottom)

Implement the left-column sessions list (below connections) using `SessionsController`.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/060-desktop-connections-panel.md`

## Status

- [ ] Not started

## Requirements

- When connected, list sessions.
- Selecting a session opens it as a tab in the main column (do not navigate away).
- If the session is already open in a tab, focus the existing tab.
- Sessions list should refresh when:
  - focused connection changes
  - user requests refresh
  - a session is created/deleted (controller or plugin events)

Notes:

- Multiple connections can be open at the same time.
- The sessions pane lists sessions for a single `focusedConnectionId` at a time.
- Opening a session creates/activates a tab keyed by `{ connectionId, sessionId }`.

## Work plan

### 1) Create a `SessionsController` instance

- Use `@crystal-lattice/frontend-sdk-react` hook (`useSessionsController`) or instantiate controller directly.
- Desktop app owns controller lifecycle per connection.

Recommendation:

- Keep one `SessionsController` per open connection.
- Switching `focusedConnectionId` swaps which controller’s state is rendered.

### 2) Session list UI

- Keep UI desktop-friendly:
  - search input at top of sessions panel
  - list below
  - “New session” button

### 3) Open session in main tabs

When a row is clicked:

- call `openTab({ connectionId: focusedConnectionId, sessionId })` which:
  - adds a new tab if not present
  - sets `activeTabId`

### 4) Minimal session metadata

- Use SDK session list presentation helpers if desired.
- Avoid coupling to mobile’s markdown renderer.

## Open questions

1) Session creation behavior
   - Option A (recommended): create session and open a new tab immediately.
   - Option B: create session but do not open until user clicks.

2) Sessions ordering
   - Option A: sort by `last_modified_at` if available.
   - Option B: server order.
