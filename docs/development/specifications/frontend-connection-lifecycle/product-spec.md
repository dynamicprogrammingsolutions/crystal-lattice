# Frontend connection lifecycle product specification

## Purpose

A network connection is temporary; the user's workspace is not. Crystal
Lattice frontends should preserve access to known sessions, messages, and
composed work while a server is closed, unreachable, reconnecting, or being
repaired. Network completion must never override newer user intent.

The target user experience supports one focused workspace and zero or more
open connection runtimes. A frontend may initially expose only one open
runtime, but its behavior must not make focus, cache ownership, or navigation
depend on that limitation.

## Terms

**Saved connection** is durable configuration and authorization needed to
identify and reach one server through a supported connection kind.

**Connection identity** is the stable frontend ID used to scope cached data,
navigation, drafts, and runtime state. Repairing or editing a saved connection
does not create a new identity unless the user explicitly creates a separate
connection.

**Focused connection** is the connection whose workspace the user is viewing.
It may be open, connecting, closed, or unavailable.

**Open runtime** is a currently usable transport and backend for one saved
connection.

**Connection attempt** is one bounded open, validation, reconnect, repair, or
pairing operation with its own identity and terminal result.

**Candidate runtime** is a transport/backend being validated before it is
allowed to replace or join the usable runtime set.

**Workspace state** is the selected connection, selected session, open
session views, transcript state, and other navigation owned by that
connection.

**Offline content** is cached data shown without claiming that it is current
server state.

**Draft** is unsent composed content, including text, attachment order and
metadata, and any recoverable send state.

## Product principles

### User intent owns navigation

Only an explicit current user action may change focus or navigate because a
connection attempt completed. Reconnection, background validation, timeout,
repair discovery, and superseded operations may update their owning
connection's status but do not take navigation control.

### Connection failure is non-destructive

Trying another server does not close a usable runtime until the candidate is
ready and the selected runtime policy requires the old one to close. Failure
or cancellation disposes the candidate and preserves the previous runtime,
workspace, caches, and drafts.

### Content visibility is independent from connectivity

A saved connection can be focused while offline. Cached sessions and messages
remain navigable with freshness information. Operations that require current
server authority are disabled or request reconnection without hiding cached
content.

### Destructive actions are explicit

Closing a runtime, removing a saved connection, deleting local cached content,
and discarding drafts are different operations. A destructive confirmation
states exactly which local and remote data is affected.

### Drafts are more valuable than expendable cache

A non-empty draft is never silently evicted as ordinary cached history.
Composed work remains recoverable until an acknowledged append/send or an
explicit discard.

## Target user experience

### Launch and restoration

After local state is hydrated, the frontend restores the most recent focused
workspace and its cached content without waiting for a network request. It may
start reconnecting in the background and presents the result without replacing
the restored navigation.

A loading or splash surface reflects actual required initialization rather
than imposing a fixed network-independent delay.

### Connections surface

Each saved connection presents:

- display identity and connection kind;
- focused state independently from runtime status;
- a portable status such as Closed, Connecting, Open, Reconnecting,
  Unavailable, Repair required, or Error;
- available recovery action;
- last successful connection or cache freshness where useful.

Selecting a connection focuses its workspace. Open, Close, Retry, Edit, and
Re-pair are explicit actions even if a platform combines focus and open into
one convenient gesture.

### Creating or switching connections

Creating, editing, or pairing a connection does not tear down the current
workspace. The candidate is promoted only after successful validation.

If a frontend policy allows only one live runtime, it closes the old runtime
after promotion while retaining that connection's offline workspace. A
multi-runtime frontend may keep both open.

### Reconnect and repair

Transient failure offers retry without deleting authorization. A bridge
credential or server-identity problem enters repair for the same saved
connection. Cancelling repair returns to the prior workspace and leaves no
temporary transport or late callback able to change the screen.

Foreground revalidation is status work, not a navigation command. A result for
an older connection remains scoped to that connection even after the user
focuses another one.

### Connection loss and offline navigation

When the focused runtime becomes unavailable:

- the current connection and session remain focused;
- cached sessions and messages remain readable and navigable;
- cache age and offline status are visible without obscuring content;
- local filtering, copy, transcript navigation, and draft editing remain
  available;
- server mutations and authoritative refreshes are disabled with a useful
  reconnect action;
- connection failure does not force navigation to the Connections surface.

### Composer continuity

Users may continue composing while offline. The frontend persists text and
attachment state during editing and communicates any persistence failure.

Send is disabled or changed to a reconnect action while no runtime is usable.
The frontend does not silently queue and later send a message without an
explicit product policy and user-visible control.

An uncertain send remains recoverable through its idempotency/status mechanism.
The draft is cleared only when the applicable append/send is acknowledged or
the user explicitly discards it.

### Multiple open connections

Several connection runtimes may be open while one connection or session is
focused. Switching focus does not close another runtime. Closing one runtime
does not delete its saved record, tabs, cached content, or drafts.

Background events and notifications remain connection-scoped. They may update
status or present through their owning portable behavior, but they do not
silently focus their connection.

## Error and recovery outcomes

Portable error categories distinguish at least:

- cancelled or superseded;
- transient network unavailability;
- timeout;
- authentication or authorization failure;
- bridge pairing or repair required;
- expected server identity mismatch;
- invalid saved configuration or connection link;
- unsupported protocol or capability;
- server/application response failure;
- local persistence failure.

Presentation uses concise user language and an appropriate action such as
Retry, Edit, Re-pair, Browse offline, or Discard. Raw transport messages may be
available for diagnostics but are not the only user explanation.

## Acceptance examples

### Older attempt cannot replace newer success

Connection A begins opening. Before it completes, the user opens connection B,
which succeeds. A later timeout, failure, or success from A may update A's
status but does not replace B's focus/runtime or navigate away from B.

### Cancelled bridge repair is terminal

A saved bridge connection enters repair and starts loading available servers.
The user cancels. A later server list, pairing response, or timeout has no
visible effect, and opening repair again starts from a usable initial state.

### Candidate failure preserves a working connection

Connection A is open. The user tries connection B and B fails validation.
Connection A remains usable and focused unless the user had separately focused
B for offline browsing.

### Unreachable saved connection remains browsable

A saved connection cannot be reached. The user focuses it and sees cached
sessions. Opening a cached session shows cached messages and its draft with an
offline/freshness indication.

### Draft survives restart and cache pressure

The user composes text and attachments, then the application process ends.
After restart the draft is restored. Loading enough other sessions to exceed
ordinary message-history cache limits does not discard the draft.

### Close is not delete

The user closes an open runtime. Its saved connection, focused or open session
views, cached content, and drafts remain. Removing those items requires a
separate explicit action.

## Non-goals

- Guaranteeing persistence after unrecoverable device-storage failure.
- Automatically sending offline drafts after reconnection.
- Keeping unlimited message history on the device.
- Treating one successful request as proof of indefinite connectivity.
- Defining the visual design system used by each platform.
- Replacing transport-specific bridge, cloud, or direct HTTP contracts.