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

- [x] Done

Implemented in desktop app:

- `desktop/crystal-lattice-control-desktop-rn/App.tsx:1`
- `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:1`
- `desktop/crystal-lattice-control-desktop-rn/src/layout/DesktopShell.tsx:1`
- `desktop/crystal-lattice-control-desktop-rn/src/panels/ConnectionsPanelPlaceholder.tsx:1`
- `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanelPlaceholder.tsx:1`
- `desktop/crystal-lattice-control-desktop-rn/src/tabs/SessionTabs.tsx:1`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPanePlaceholder.tsx:1`

## UX spec (reference)

See: `tasks/20260202-desktop-macos-frontend/910-desktop-ux-spec.md`.

## Work plan

### 1) Desktop navigation model

No mobile-style screen tabs. The desktop shell is always visible with a split view.

Important correction:

- Multiple connections can be open at the same time.
- Session tabs can belong to different connections.
- Switching tabs must be fast; tabs should remain mounted (rendered but hidden) so controller state is not lost.

The Phase 5 baseline navigation state is:

- `focusedConnectionId: string | null`
  - Controls which connection’s sessions are shown in the left Sessions panel.
  - This is not necessarily the same connection as the active tab.
- `openConnectionIds: string[]`
  - Connections that are currently “open” (connected).
  - Task `060` wires this to real `FetchTransport` + `RestAgentBackend` instances.
- `tabs: Array<{ tabId: string; connectionId: string; sessionId: string; title: string }>`
  - `tabId` should be stable and unique across connections; recommended: `${connectionId}:${sessionId}`.
- `activeTabId: string | null`

Derived behavior:

- `openTab({ connectionId, sessionId })`:
  - if already open, focuses it
  - otherwise adds a new tab and focuses it
- `closeTab(tabId)`:
  - closing the active tab focuses the nearest neighbor
- `focusTab(tabId)`

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

Implementation notes:

- For Phase 5, it’s OK for the main column to render *placeholder chat panes*.
- Tabs should be rendered-but-hidden when inactive (do not unmount inactive tab panes).
  - This sets up task `080`, where each tab pane will own a stable `ChatController`.

### 3) Settings dropdowns

Implement a reusable dropdown menu pattern (shared component or desktop-local), used for:

- connection actions (rename/delete)
- session actions
- message actions

Avoid `Modal`.

Decision: for Phase 5, using a transparent `Modal` as a portal surface is acceptable as long as the UX is an anchored dropdown.

Implementation guidance:

- Prefer using the shared menu surface abstraction from `@crystal-lattice/frontend-rn-components`.
- The shell should establish obvious “menu anchor points” even if the menus are placeholders:
  - Tab strip menu button
  - Connection row menu button
  - Session row menu button

## Deliverables

- Desktop app shows the layout with placeholder panels.
- Session tabs UI is visible and can switch between placeholder tabs.

## UI elements to build in this stage

- Shell layout container (two columns).
- Left column panel containers:
  - Connections panel placeholder (header + placeholder list + menu anchor).
  - Sessions panel placeholder (header + placeholder list + menu anchor).
- Main column:
  - Session tab strip (switch + close).
  - Placeholder tab panes rendered-but-hidden for inactive tabs.

## Comprehensive implementation plan (Phase 5 baseline)

1) Refactor desktop entry to a shell-based structure

- Keep `desktop/crystal-lattice-control-desktop-rn/App.tsx` thin; move shell components under `desktop/crystal-lattice-control-desktop-rn/src/`.
- Introduce `DesktopRoot` which owns the navigation state and renders the shell.

2) Create a pure layout component

- Add a `DesktopShell` component responsible only for:
  - left column layout (stacked panels)
  - main column layout (tabs + content)

3) Add placeholder panels

- Connections panel placeholder:
  - Accepts props like `focusedConnectionId`, `openConnectionIds`, and callbacks.
  - Uses placeholder data for now.

- Sessions panel placeholder:
  - Shows placeholder sessions for the `focusedConnectionId`.
  - Clicking a placeholder session calls `openTab({ connectionId, sessionId })`.

4) Implement `SessionTabs` strip + tab switching

- Controlled tab strip:
  - `tabs`
  - `activeTabId`
  - `onSelectTab(tabId)`
  - `onCloseTab(tabId)`
- Display connection context in the tab label (badge or prefix) to reduce confusion when multiple connections are open.

5) Render per-tab panes (rendered-but-hidden)

- Render one pane per `tabs[]` entry.
- Hide inactive panes without unmounting.
- For now, panes can be placeholders; task `080` replaces placeholder panes with real chat.

6) Add menu anchors

- Add small “…” buttons where menus will live.
- Menu content can be stubbed for now (no-op items).
- Use dropdown/anchored menu UX.

7) Lightweight verification

- App renders the shell.
- Can open multiple placeholder tabs.
- Can switch between tabs instantly.
- Can close tabs; active tab selection updates correctly.

## Checklist

- [x] Update this task doc’s navigation model (multi-connection + per-tab connectionId)
- [x] Add `DesktopRoot` and a `src/` directory structure
- [x] Add `DesktopShell` layout component (two columns)
- [x] Add placeholder `ConnectionsPanel` container
- [x] Add placeholder `SessionsPanel` container
- [x] Implement controlled `SessionTabs` strip (select + close)
- [x] Render per-tab placeholder panes rendered-but-hidden when inactive
- [x] Add menu anchor buttons (no modals; anchored dropdown surface allowed)
- [x] Smoke test: open 3 tabs across 2 connections, switch rapidly, close tabs
