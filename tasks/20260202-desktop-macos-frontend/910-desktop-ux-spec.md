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

- Shows current active connection.
- Allows adding/editing manual connections (host/port).
- Allows switching between saved connections.

Manual only (no discovery/bridge).

## Sessions panel

- Lists sessions for the active connection.
- Clicking a session opens it as a tab in the main column.
- If already open, focuses the existing tab.

## Session tabs

Baseline behavior:

- Tabs are closable.
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

## Keyboard (optional, not required for Phase 5)

- `Cmd+W` close active tab
- `Cmd+Shift+]` / `Cmd+Shift+[` switch tabs
- `Cmd+Enter` send
