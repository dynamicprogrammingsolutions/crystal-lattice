# Home, Watchlist, and recent sessions

Home is the initial mobile workspace, alongside Sessions and Messages.
Connections appears first, followed by Watchlist and Recent Sessions.

## Connections

Saved connection cards keep their details, Open/Closed status, and pinnable
actions. The list uses most-recently-used ordering and initially shows up to
three cards. When there are more, **Show all N connections** below the cards
reveals the whole list; **Show fewer** returns to three. Expanding does not
leave Home.

Tap a card to enter Sessions and open its connection when necessary. The
card's **Open** action connects while staying on Home. The active connection
offers Disconnect, Health Check, and server settings. Each card's **+** opens
the connection when needed, then shows the agent picker for a new session.
The Connections heading has just **New connection**, without an ellipsis.
The Home menu on the left provides New connection, Global Settings, and
Local provider settings on iOS. The right-hand header area remains empty until
login is implemented.

New connection opens setup in a modal. The current connection stays open
while you configure and validate another. Closing, cancelling, or failed
setup retains it; successful setup switches to the new connection. Bridge
re-pairing also uses the setup modal.

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

Each Watchlist tile shows the session title, an optional subtitle or distinct
message preview, session ID, request status when available, local note,
connection name, and relative modification time. Session IDs and connection
names truncate independently. The relative time and note/remove actions remain
visible when a connection name is long.

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
the Home menu.

Timeline rows use the same information order as Watchlist tiles and add a
neutral gray activity rail. Connection name and relative time are separate, so
the time is not lost when the connection name is long. If a session has no
presentation title or subtitle, its message preview appears once rather than
being repeated as both fields.

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