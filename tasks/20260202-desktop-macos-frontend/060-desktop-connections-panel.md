# Subtask: Desktop connections panel (manual only)

Implement the left-column top panel showing connections and enabling manual connect (host/port).

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/040-shared-connection-model.md`
- `tasks/20260202-desktop-macos-frontend/050-desktop-shell-layout.md`

## Status

- [ ] Not started

## Requirements

- Manual connections only for Phase 5.
- The panel shows saved connections and which ones are open.
- Selecting a connection constructs:
  - `FetchTransport`
  - `RestAgentBackend`

Notes:

- Phase 5 supports multiple open connections simultaneously.
- The sessions pane (`070`) uses a `focusedConnectionId` to decide which connection’s sessions list is visible.

## Work plan

### 1) Desktop storage adapter

- Implement a `KeyValueStore` adapter backed by `AsyncStorage` in desktop app code.
- Use SDK connection persistence helpers from `packages/frontend-sdk/src/connections/store.ts`.

### 2) Create/edit/delete connections

- Minimal UI:
  - host input
  - port input
  - save button
- Saved connections list:
  - click row to activate
  - dropdown menu for rename/delete (no modal)

### 3) Connection status indicator

- Show open connection label(s) + base URL(s).
- Show “disconnected” state for connections that are not open.

## Open question

Do we need auto-reconnect on app start?

- Option A (recommended): yes, reconnect to the most recent (`lastUsedAt`) and set it as `focusedConnectionId`.
- Option B: no; user must explicitly open a connection.
