# Desktop UX spec (Phase 5 baseline)

This is the baseline UX model for the desktop app.

## Layout

Two columns:

Left column (stacked panels):

1) Connections panel (top)
2) Sessions panel (bottom)

Main column:

- Session tab strip
- Active session chat pane

## Connection panel

- Shows which connections are open.
- Allows adding/editing manual connections (host/port).
- Allows switching between saved connections.

Manual only (no discovery/bridge).

## Sessions panel

- Lists sessions for the focused connection.
- Clicking a session row selects it.
- Use an explicit “Open” affordance to open it as a tab in the main column.
- If already open, focuses the existing tab.

## Session tabs

Baseline behavior:

- Tabs are closable.
- Tabs may belong to different connections.
- Closing active tab focuses nearest neighbor.
- Tabs show a short title (session title or session id prefix initially).

Future extensions:

- Dirty indicator (if reducer marks session dirty)
- Unread indicator
- Drag reorder

## Settings and actions

- Desktop prefers dropdowns/anchored menus.
- Avoid modal popups for:
  - session actions
  - message actions
  - settings

Implementation hint:

- “Dropdown” can initially be a JS overlay anchored to a button.
- Keep the shared components flexible so a future macOS-native menu/popover can be introduced.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

## Keyboard (optional, not required for Phase 5)

- `Cmd+W` close active tab
- `Cmd+Shift+]` / `Cmd+Shift+[` switch tabs
- `Cmd+Enter` send

Implementation hint:

- RN macOS exposes extra key event handling primitives; integrate once the base UI is stable.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`
