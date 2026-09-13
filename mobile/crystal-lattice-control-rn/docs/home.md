# Home, Watchlist, and recent sessions

Home is the initial mobile workspace. It sits alongside Connections, Sessions,
and Messages and provides shortcuts to sessions cached from all saved
connections.

## Watchlist

Add a session to the Watchlist with its bookmark control. The Watchlist is
stored on the current device and is independent from server-side session
pinning.
You can also add or remove the current session through Session actions on the
Sessions and Messages tabs.

Watched sessions appear as reorderable two-column tiles. Drag a tile by its
move handle to change the order. The tile follows the drag while an empty
outlined space previews its prospective position. Vertical and horizontal
movement are both supported; scrolling Home normally still works when the
gesture starts outside a move handle. Accessible Move Earlier and Move Later
actions provide the same operation without dragging. When the drag ends, the
floating tile is placed directly into the outlined destination and stays there
until the ordinary tiles report the saved final order.

Watchlist membership and order are local to the device. A watched session can
remain on Home after it is no longer recent. Use the close control on a
Watchlist tile to remove that local membership without deleting the session.

## Permanent local notes

Home and Sessions offer a Local Note action. Each session ID has one note
stored on the device. If the same session ID appears through another
connection, both places show and edit the same note.

Removing a session from the Watchlist or deleting a saved connection does not
remove its note. Use Remove Note in the note editor when the note should be
deleted.

## Recent Sessions

Recent Sessions is a chronological timeline built from locally cached session
summaries. It includes sessions modified inside the selected window whether
or not they are also on the Watchlist:

- Last 24 hours
- Last 3 days
- Last week

Change the window in Global Settings. Global Settings is available from
Connections, the Home menu, and Home actions.

## Request status

Home and Sessions can show:

- Idle
- Not started
- In progress
- Completed
- Interrupted

The initial status is a lightweight current-runtime estimate. An active
request is In progress. Otherwise the server inspects the stored conversation
tail: a final assistant answer is Completed, a user tail is Not started, and
an unfinished assistant/tool tail is Interrupted.

Status may be unavailable when a server is offline, does not implement status
queries, or is reachable only through an older WebSocket-only bridge. Status
checks do not open a saved connection.

Selecting a Home session opens its saved connection when necessary and enters
Messages after the connection succeeds.