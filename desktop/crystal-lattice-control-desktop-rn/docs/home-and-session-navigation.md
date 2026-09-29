# Home and session navigation

The desktop tab strip begins with a fixed Home icon. Home contains a local
Watchlist and Recent Sessions from all saved connections.

## Watchlist and History

Watchlist membership and order are stored only on this Mac. They do not change
server-side session pins. Drag Watchlist tiles to reorder them, or use their
Move Earlier and Move Later accessibility actions.
Sessions and Chat also provide Add to Watchlist or Remove from Watchlist in
their pinnable Session actions.

Recent Sessions includes cached sessions modified in the selected timeframe:

- Last 24 hours
- Last 3 days
- Last week

The same collection is available in the Home workspace and the History side
panel. A watched session can also appear in Recent Sessions.

Watchlist cards and Recent timeline rows show title, an optional subtitle or
distinct message preview, session ID, request status when available, local
note, connection name, and relative modification time. Connection name and
session ID truncate independently while time and actions remain available.
Preview-only sessions show their message preview once. Recent entries use a
neutral gray timeline rail; request-status colors keep their semantic meaning.

Local notes are keyed by session ID. Home, History, Sessions, and Chat can edit
the same note. In Sessions and Chat, Local note is in the ellipsis Session
actions menu and may be pinned. Removing a Watchlist entry or deleting a
connection does not delete the note.

## Side panels

The narrow activity rail has three controls:

- Connections at the top independently shows or hides the Connections section.
- Sessions at the bottom shows the focused connection's Sessions panel.
- History at the bottom shows recent sessions across connections.

Drag the divider between the side panel and main workspace to resize the
panel. The selected width is stored locally. The divider can also be focused
and adjusted with the Left and Right Arrow keys, or through its accessibility
Make Sidebar Narrower and Make Sidebar Wider actions. Resizing is bounded so
the sidebar remains useful without consuming the main workspace.

## Preview and permanent tabs

Single-clicking a session item only selects it. Double-click behavior is
configured in Settings:

- Preview uses one italic tab at the right of permanent tabs.
- Open creates or activates a permanent tab.

The item button always provides the other action. With the default setting,
double-click previews and the button says Open.
If the session already has a preview or permanent tab, the item button says
Open. It activates the permanent tab or promotes the existing preview instead
of creating a duplicate.

Double-click an italic preview tab to make it permanent. Starting a request or
another session mutation also makes the preview permanent before the operation
begins. Permanent tabs can be dragged to reorder them.

Middle-click any session tab to close it without selecting it. A three-finger
click has the same behavior when macOS or a pointing-device utility maps that
gesture to middle-click.

Session-action pin choices are connection-scoped. Pinning or unpinning an
action updates the other currently mounted tabs for that connection
immediately; an older tab restored into the warm set reads the same persisted
choice. Program actions are listed before plugin-contributed actions in the
complete menu.

Permanent order, the current preview, and the active Home or session workspace
are restored after relaunch. Selecting or restoring a session tab attempts to
reopen its saved connection while cached messages remain visible.

Opening Home does not close session tabs or discard the three most recently
active Chat panes kept ready by the desktop workspace.

Reopening a tab does not change the connection selected in the sidebar by
default. Two independent View and Settings choices control sidebar behavior:

- Follow Active Tab in Sessions List defaults On. It selects and reveals the
  active tab's session when that session belongs to the connection already
  shown in the sidebar.
- Switch Connection with Active Tab defaults Off. It changes the sidebar to
  the active tab's connection.

Enable both choices to follow a tab across connections. Disable Follow while
leaving Switch Connection enabled to change connections without selecting the
tab's session. A manual Sessions selection remains selected when a tab cannot
be followed; a selection made automatically for the previous tab is cleared.

## Request status

Home, History, Sessions, session tabs, and the Chat header can show:

- Idle
- Not started
- In progress
- Completed
- Interrupted

These values are lightweight current-runtime estimates, not durable request
history. Status can be unavailable while a server is offline or does not
support stateless status reads.

## Settings

Choose `Settings…` from the application menu or press Command-comma. Settings
opens in a separate window and controls font size, Markdown Headers, Recent
Sessions timeframe, the session double-click action, whether Sessions follows
the active tab, and whether tab changes switch the sidebar connection. Both
navigation choices are also available in the View menu.
