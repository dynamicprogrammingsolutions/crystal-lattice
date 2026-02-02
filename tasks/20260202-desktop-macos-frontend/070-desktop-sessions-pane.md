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
  - connection changes
  - user requests refresh
  - a session is created/deleted (controller or plugin events)

## Work plan

### 1) Create a `SessionsController` instance

- Use `@crystal-lattice/frontend-sdk-react` hook (`useSessionsController`) or instantiate controller directly.
- Desktop app owns controller lifecycle per connection.

### 2) Session list UI

- Keep UI desktop-friendly:
  - search input at top of sessions panel
  - list below
  - “New session” button

### 3) Open session in main tabs

When a row is clicked:

- call `openSession(sessionId)` which:
  - adds to `openSessionIds` if not present
  - sets `activeSessionId`

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
