# Subtask: Desktop shell layout (two columns + session tabs)

Implement the top-level desktop UI layout:

- Left column: connections (top) + sessions (bottom).
- Main column: multiple sessions open as tabs.
- Settings are dropdowns (not modals).

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/020-rn-macos-scaffold-and-version.md`
- `tasks/20260202-desktop-macos-frontend/030-desktop-metro-and-ts-wiring.md`
- `tasks/20260202-desktop-macos-frontend/010-shared-components-package.md`

## Status

- [ ] Not started

## UX spec (reference)

See: `tasks/20260202-desktop-macos-frontend/910-desktop-ux-spec.md`.

## Work plan

### 1) Desktop navigation model

No mobile-style screen tabs. The desktop shell is always visible with a split view.

The main navigation state is:

- `activeConnectionId`
- `openSessionIds: string[]` (tabs)
- `activeSessionId: string | null`

### 2) Implement layout container

- `DesktopRoot` component that renders:
  - left column container
  - main column container

The left column has two stacked panels:

- `ConnectionsPanel` (top)
- `SessionsPanel` (bottom)

The main column has:

- `SessionTabs` tab strip (shared component)
- `ChatPane` for the selected tab

### 3) Settings dropdowns

Implement a reusable dropdown menu pattern (shared component or desktop-local), used for:

- connection actions (rename/delete)
- session actions
- message actions

Avoid `Modal`.

## Deliverables

- Desktop app shows the layout with placeholder panels.
- Session tabs UI is visible and can switch between placeholder tabs.
