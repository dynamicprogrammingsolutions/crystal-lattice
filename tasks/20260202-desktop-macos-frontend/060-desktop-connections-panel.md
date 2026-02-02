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
- The panel shows saved connections and which is active.
- Selecting a connection constructs:
  - `FetchTransport`
  - `RestAgentBackend`

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

- Show active connection label + base URL.
- Show “disconnected” state if transport/backend is null.

## Open question

Do we need auto-reconnect on app start?

- Option A (recommended): yes, reconnect to `lastUsedAt` most recent.
- Option B: no; user must click connect.
