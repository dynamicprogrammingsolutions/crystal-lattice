# Mobile connection and offline UX

This page refines the portable frontend lifecycle for the Crystal Lattice
mobile application. It defines the target screen behavior and user-visible
state across launch, connection selection, opening, cancellation, repair,
offline navigation, and draft recovery.

The product outcomes remain authoritative in
[Product behavior and target user experience](product-spec.md). Portable
semantics shared with desktop remain authoritative in
[Portable frontend behavior](frontend-behavior.md). This page defines how
those outcomes appear in the mobile application's Home, Connections, Sessions,
and Messages navigation.

## Normative and illustrative content

The following are normative:

- which state is visible;
- which actions are available;
- what an action changes or preserves;
- when navigation may occur;
- connection/session ownership;
- error, cancellation, offline, and draft recovery behavior;
- accessibility meaning and stable selector identity.

The text wireframes illustrate information hierarchy and action placement.
Exact spacing, typography, colors, icons, and non-semantic copy may follow the
mobile design system. Status names and accessible labels may use equivalent
clear wording where this page does not require exact text.

## Navigation model

Mobile retains Connections, Sessions, and Messages and adds Home as a fourth
primary destination:

```text
Home        Connections        Sessions        Messages
```

The destinations are workspace navigation, not connection-state gates.
Sessions and Messages remain selectable while the focused connection is open,
connecting, closed, unavailable, or under repair.

The application distinguishes:

- **focused connection**: owns the currently presented Sessions workspace;
- **selected session**: belongs to one connection and owns the Messages
  workspace;
- **open runtime**: permits server-authoritative actions;
- **connection attempt**: presents progress/cancellation for one connection or
  unsaved wizard;
- **cache and draft state**: permits offline continuity.

The migration may initially keep at most one established runtime open, but the
final mobile target permits several user-opened runtimes. Focus remains one
independent workspace choice. During candidate validation every existing
runtime remains usable until the candidate is promoted or cancelled.

## Launch and restoration

Local hydration determines when the restored workspace can be shown. A fixed
visual delay is not a substitute for connection, workspace, cache, or draft
hydration.

When a previous focused connection exists, launch restores:

- the focused connection;
- that connection's selected session when it remains locally known;
- cached session summaries and messages;
- transcript range and viewport state;
- the session draft.

Network validation may begin after restoration. It updates connection status
without replacing the restored destination.

Illustrative offline launch:

```text
┌─────────────────────────────────────────┐
│ Office Mac                              │
│ Offline · Last synced yesterday  [Retry]│
├─────────────────────────────────────────┤
│ Cached sessions or selected chat        │
│ appear immediately after hydration.     │
└─────────────────────────────────────────┘
  Home       Connections       Sessions       Messages
```

The following result sequence is valid:

```text
restore cached workspace
        ↓
show Reconnecting for the owning connection
        ↓
Open: enable current server actions
or
Unavailable: keep cached workspace and offer Retry
```

Neither result navigates on its own.

Home is the initial destination after local hydration, including when no
focused connection exists. If the focused connection has no applicable cache,
Sessions and Messages show an honest empty offline state rather than a generic
loading failure.

## Home screen

Home aggregates only locally known session summaries across saved connections.
It does not open a runtime merely to discover or poll a session.

Home contains:

- a device-local ordered Watchlist keyed by connection and session;
- permanent device-local notes keyed by session ID;
- a Recent Sessions timeline limited to the user-selected 24-hour, 3-day, or
  1-week window;
- lightweight request status where the saved connection supports one
  stateless explicit-ID query.

The Watchlist is not server-side session pinning. Equal session IDs across
connections intentionally share one local note, while Watchlist membership and
navigation remain connection-scoped. Watchlist membership does not remove a
session from the time-bounded Recent Sessions timeline; a qualifying session
may appear in both sections because one is manually curated and the other is
chronological.

Selecting a Home session is explicit user navigation intent. A closed
connection is opened first; only the current successful intent may focus the
connection, select the session, and enter Messages. Status polling, recovery,
and stale open completion never navigate.

## Connections screen

### Screen responsibilities

The Connections screen:

- lists saved connections;
- distinguishes focus from runtime status;
- exposes connection-scoped Open, Close, Cancel, Retry, Edit, and Re-pair
  actions;
- starts the new-connection wizard;
- presents last-success/cache context where useful;
- exposes destructive local-data actions separately.

It does not hide saved rows while one connection is opening or while the
wizard is active unless the wizard intentionally occupies the Connections tab.
Even when the wizard occupies that tab, Sessions and Messages remain available
through primary navigation.

### Saved connection row

Each row presents:

- display name;
- connection kind and relevant non-secret detail;
- focused indication independent from status;
- runtime/attempt status in text;
- primary lifecycle action;
- cache or last-connection freshness where useful;
- concise scoped error text when recovery is needed.

Illustrative rows:

```text
┌─────────────────────────────────────────┐
│ ✓ Ireland Server                  Open  │
│   Bridge · Hybrid                       │
│   Last connected 2 minutes ago  [Close] │
├─────────────────────────────────────────┤
│   Office Mac               Unavailable  │
│   Direct HTTP                           │
│   Cached yesterday              [Retry] │
├─────────────────────────────────────────┤
│   Home Server           Repair required │
│   Bridge · HTTP                         │
│   Cached sessions available     [Re-pair]│
└─────────────────────────────────────────┘
```

The focused indicator is not communicated by color alone. A row may be:

- focused and open;
- focused and unavailable;
- focused and closed;
- unfocused and open during candidate or future multi-runtime behavior;
- unfocused and unavailable.

### Status and actions

| State | Required primary behavior | Additional useful behavior |
| --- | --- | --- |
| Closed | Open | Focus/browse cache |
| Opening | Cancel | Continue browsing cache |
| Open | Close | Health/detail actions may remain |
| Reconnecting | Cancel or continue offline | Show last usable time |
| Unavailable | Retry | Edit configuration when applicable |
| Repair required | Re-pair | Browse cached workspace |
| Configuration error | Edit | Retry after correction |
| Persistence error | Retry local save | Explain which local state is affected |

Cancellation and supersession are terminal attempt outcomes and do not leave a
permanent Error row by themselves.

### Focus versus opening

Selecting a saved row focuses its workspace immediately. Opening is a
separate lifecycle action even when the interface offers a convenient combined
gesture.

After focus:

- Sessions presents that connection's cached summaries, if any;
- Messages presents that connection's selected cached session, if any;
- an Open/Retry attempt may continue in the background;
- open failure does not undo focus or remove cache.

The row's primary action operates on network state. It does not implicitly
delete cache, discard drafts, or forget credentials.

## New connection wizard

Starting a new connection opens a candidate workflow. It does not close the
current runtime or discard the current workspace.

Each method retains its existing domain inputs:

- manual address;
- Bonjour discovery;
- bridge service and explicit bridge transport mode;
- cloud connection link.

The wizard shows progress and error state within the attempt context:

```text
┌─────────────────────────────────────────┐
│ Manual Connection                       │
│                                         │
│ Host  [192.168.1.42                  ]  │
│ Port  [8080                          ]  │
│                                         │
│ [Connect]  [Cancel]                     │
│                                         │
│ Could not reach this server.            │
│ Your previous connection remains open.  │
│ [Retry]  [Edit address]                 │
└─────────────────────────────────────────┘
  Home       Connections       Sessions       Messages
```

Cancel:

- becomes effective immediately in the UI;
- invalidates the attempt before resource cleanup;
- stops discovery where supported;
- aborts supported requests;
- disconnects temporary bridge resources;
- returns to the saved Connections surface;
- prevents late result, timeout, alert, record creation, focus, or navigation.

A cancelled operation does not require the user to wait for its normal
timeout.

### Candidate promotion

The target sequence is:

```text
create candidate
    ↓
validate candidate while previous runtime remains usable
    ↓
confirm the attempt is still authoritative
    ↓
save/promote the candidate
    ↓
focus/navigate only if the initiating user intent is still current
    ↓
retain other user-opened runtimes
```

Candidate failure disposes only candidate-owned resources. If connection B is
focused while its opening fails, B remains focusable offline and previously
open connection A remains available when the user focuses it again.

An intermediate one-runtime compatibility policy may close the previously
open runtime after promotion. That policy is not the final multi-open mobile
behavior and does not change focus, cache, session, or draft identity.

## Multiple open connections

### Connection list and focus

The Connections screen may show several Open rows while exactly one connection
is focused:

```text
┌─────────────────────────────────────────┐
│ ✓ Ireland Server                  Open  │
│   Bridge · Hybrid                 [Close]│
├─────────────────────────────────────────┤
│   Office Mac                     Open  │
│   Direct HTTP                     [Close]│
├─────────────────────────────────────────┤
│   Home Server                   Closed  │
│   Bridge · HTTP                   [Open]│
└─────────────────────────────────────────┘
```

Opening a connection does not automatically close another. Focusing a row:

- changes the Sessions workspace to that connection;
- restores its selected session and Messages workspace;
- does not open a Closed runtime unless an explicit combined Open action is
  invoked;
- does not close or suspend another runtime;
- does not transfer cache, draft, or navigation state.

Closing the focused runtime leaves that connection focused offline. Closing an
unfocused runtime leaves the current workspace unchanged.

### Runtime isolation

Every open runtime has independent:

- attempt generation and cancellation;
- transport/backend resources;
- foreground recovery;
- availability/error status;
- event stream and application notifications;
- cache invalidation and refresh effects.

Failure or repair of A cannot interrupt B. A connection-level display from an
unfocused runtime retains its connection label and does not take focus.

### Application lifecycle

Backgrounding prepares or disconnects each stateful runtime according to its
adapter. Foregrounding starts independent recovery for the runtimes that were
user-open within the current application process.

After process restart, the frontend restores saved/focused workspaces, caches,
and drafts first. It does not automatically reopen every previously open
runtime unless a later explicit product setting defines and communicates that
policy. Users can reopen saved rows independently.

If a platform resource limit prevents another runtime from opening, the UI
reports the limit and offers an explicit choice of a runtime to close. It does
not silently close one.

### Deep links and background activity

A connection-targeted deep link resolves against any matching open runtime,
not only the focused one. Any focus/session navigation remains an explicit
current deep-link action.

Notifications and refresh invalidations from open unfocused runtimes remain
connection-scoped. They may update caches or present through their owning
portable behavior without changing focus.

### Multi-open acceptance

1. Open A and B.
2. Focus A and select one of its sessions.
3. Receive events or notifications from B.
4. Verify A remains focused and B's update remains labeled/scoped to B.
5. Focus B and verify its selected session and draft restore.
6. Close B and verify B remains focused offline while A stays Open.
7. Focus A and verify its runtime and workspace were not reconstructed or
   disturbed.

## Competing attempts and navigation

Each attempt and user navigation action has authority independent from visual
loading state.

If A starts, B starts later, and B succeeds first:

- B's current user intent may focus or navigate to B;
- A's later success, failure, timeout, or repair result cannot replace B;
- A may update only its own row if that update is still meaningful and
  authoritative;
- A never presents a stale modal over B.

The same rule applies when the user:

- cancels an attempt;
- starts another saved connection;
- returns to cached Sessions or Messages;
- changes selected session;
- opens another repair flow;
- backgrounds and foregrounds the application.

Connection attempt functions return typed outcomes. The screen does not
navigate merely because an asynchronous function returned after handling its
own failure.

## Bridge reconnect and repair

Bridge transport mode, pairing, resume, and error meanings follow the
[Bridge connectivity specification](../bridge-connectivity/index.md). This
page owns the mobile presentation and lifecycle coordination.

When saved authorization cannot resume, the existing connection row becomes
Repair required:

```text
┌─────────────────────────────────────────┐
│ Ireland Server                          │
│ Repair required                         │
│                                         │
│ The saved bridge authorization can no   │
│ longer be used. Cached work is intact.  │
│                                         │
│ [Re-pair]  [Browse cached sessions]     │
└─────────────────────────────────────────┘
```

Repair:

- retains the original saved connection ID;
- retains cache, selected-session, draft, and bridge transport-mode ownership;
- uses a temporary candidate transport;
- discovers current servers and requests pairing under one repair attempt;
- updates the existing record only after authoritative success;
- does not create a duplicate saved connection.

Cancelling repair:

- closes the temporary transport;
- clears only repair presentation state;
- returns to the previous workspace/destination;
- prevents the previous server list, pairing response, or timeout from
  reappearing;
- ensures a later repair opens with newly initialized discovery state.

Foreground reconnect is connection-scoped status work. A stale reconnect for
connection A cannot open repair, clear credentials, present a modal, or
navigate after the user has moved to B.

## Sessions screen

### Online and offline header

Sessions identifies the focused connection and combines runtime state with
cache freshness:

```text
┌─────────────────────────────────────────┐
│ Office Mac                              │
│ Offline · Last synced yesterday  [Retry]│
├─────────────────────────────────────────┤
│ Search sessions…                        │
│                                         │
│ Session A                               │
│ Session B                               │
│ Session C                               │
└─────────────────────────────────────────┘
  Home       Connections       Sessions       Messages
```

Required distinctions:

| Condition | Presentation |
| --- | --- |
| Open with current data | Normal content; refresh available |
| Opening/reconnecting with cache | Retain content; show scoped progress |
| Unavailable with cache | Retain content; show Offline/Unavailable and Retry |
| Refresh failed with cache | Retain prior content and its earlier freshness |
| Offline without cache | Explain that no sessions have been loaded locally |
| Cache invalidated | Retain content but do not present it as authoritative |

A failed request never replaces prior cached sessions with an accidental empty
state.

### Offline action availability

Local behavior remains available:

- search and filter cached summaries;
- select a cached session;
- navigate among primary destinations;
- inspect locally available presentation fields.

Server-authoritative behavior is disabled or starts explicit reconnection:

- refresh sessions;
- create session;
- switch session agent;
- modify server/session settings;
- run plugin/application actions requiring a backend;
- perform remote destructive actions.

Disabled controls expose why they are unavailable. If a user invokes a visible
server action while offline, the recovery path names the focused connection
and does not discard current navigation.

## Messages screen

### Cached transcript continuity

The selected connection/session pair remains the identity of the Messages
screen after runtime loss, explicit Close, failed reconnect, repair
cancellation, or application restart.

Illustrative offline chat:

```text
┌─────────────────────────────────────────┐
│ Session A                               │
│ Offline · Synced at 14:32        [Retry]│
├─────────────────────────────────────────┤
│                                         │
│ Cached transcript remains readable.     │
│ Transcript navigation remains usable.   │
│                                         │
├─────────────────────────────────────────┤
│ Draft saved locally                     │
│ [Type your message…                  ]  │
│ [Attachments]      [Reconnect to send]  │
└─────────────────────────────────────────┘
  Home       Connections       Sessions       Messages
```

Local behavior remains available:

- read and scroll cached messages;
- use loaded-range and viewport controls within available data;
- copy content;
- inspect cached message details;
- edit or discard the local draft;
- return to cached Sessions.

Server-authoritative actions are disabled or reconnect-gated:

- append, send, and resend;
- cancel active server request;
- modify or delete server messages;
- switch agent;
- create, restore, or delete snapshots;
- invoke remote plugin/session actions.

The offline state does not alter transcript-navigation semantics owned by the
chat transcript specification.

### Per-connection selected session

Each connection retains its own selected session:

```text
Ireland Server -> Session A
Office Mac      -> Session B
```

Focusing Office Mac may show Session B. Focusing Ireland Server again restores
Session A. The same session ID appearing under two connections still produces
separate screen identity, cache, events, transcript state, and draft.

Late callbacks from a screen owned by one connection cannot write state under
the currently focused different connection.

## Composer and draft behavior

### Persistence status

The composer reports durable state rather than only in-memory state:

```text
Saving…
```

```text
Saved locally
```

```text
Draft could not be saved locally                 [Retry]
```

Exact wording is illustrative. The required distinction is pending durable
write, accepted current revision, and failed current revision.

Text edits enter persistence with bounded debounce and flush at applicable
navigation/application lifecycle boundaries. The current draft restores
without requiring the input to have blurred before application termination.

### Attachments

Draft restoration includes:

- attachment order;
- placement relative to text;
- metadata;
- preview/display identity;
- upload/readiness state;
- a usable app-managed or server-owned content reference.

An attachment that cannot be reopened remains visible as a recoverable item:

```text
photo.jpg
Source is no longer available              [Replace] [Remove]
```

The frontend does not silently drop it or claim that the complete draft was
saved.

### Offline composition

The composer remains editable offline. The primary send action is disabled
with an accessible reason or becomes an explicit Reconnect to send action.

Reconnection does not automatically submit the draft. Sending requires a
current explicit user action after a usable runtime exists.

### Acknowledgement and uncertain send

Submission captures one draft revision. An acknowledgement clears only that
revision. Text or attachments added while the request is pending form a newer
draft and remain.

If acknowledgement is uncertain:

```text
┌─────────────────────────────────────────┐
│ Send not yet confirmed                  │
│                                         │
│ The server may have accepted this       │
│ message.                                │
│                                         │
│ [Check status]  [Retry safely]          │
└─────────────────────────────────────────┘
```

The submitted content and idempotent recovery state survive restart until the
outcome is resolved or the user explicitly discards it.

## Closing and destructive actions

Mobile distinguishes:

### Close runtime

Stops the live runtime and retains:

- saved connection;
- focus;
- selected session;
- cached sessions and messages;
- transcript state;
- drafts.

The focused workspace becomes Closed/offline and remains navigable.

### Forget or repair authorization

Removes or replaces connection authorization while retaining the saved
identity and local workspace where applicable. This action does not silently
delete caches or drafts.

### Clear cached server content

Removes selected server-derived cache according to the chosen scope. By
default, non-empty drafts are not ordinary cached server content and remain
unless explicitly included.

### Discard draft

Removes one connection/session draft after confirmation when it is non-empty.
It does not delete server messages.

### Delete saved connection

The confirmation names all local consequences:

```text
Delete “Ireland Server”?

This removes the saved connection, its authorization,
cached sessions and messages, and local drafts.
It does not delete data from the server.

[Cancel]  [Delete]
```

Equivalent wording is allowed, but saying only that server data is unaffected
is insufficient when local cache or drafts will also be removed.

## Error behavior

Recoverable connection errors normally appear in the owning row, wizard, or
workspace status surface rather than as repeated blocking alerts.

A user-visible error provides:

- connection identity;
- concise category-appropriate explanation;
- cache availability;
- Retry, Edit, Re-pair, or Browse offline as applicable.

Raw transport messages may remain in diagnostics. Credentials, pairing tokens,
cloud tokens, and sensitive request content never appear in status copy,
selectors, or diagnostics metadata.

Cancellation and supersession do not produce failure alerts.

## Accessibility and production selectors

Required accessible meaning includes:

- focused connection;
- connection status;
- primary lifecycle action;
- attempt progress and Cancel;
- repair state and Re-pair;
- offline/freshness state;
- disabled server-action reason;
- draft Saving, Saved, and Save failed;
- recoverable attachment state;
- destructive-action consequences.

Status is not color-only. Controls expose button roles and labels. Loading and
disabled controls retain an accessible explanation.

Production selectors identify stable entities and actions rather than list
positions or visible copy. At minimum, native tests can select:

- a connection row by connection ID;
- the focused indicator and status for that row;
- row Open, Close, Retry, Cancel, and Re-pair actions;
- new-connection and wizard Cancel actions;
- Sessions and Messages offline/freshness surfaces;
- a session row by connection/session identity;
- draft persistence state;
- attachment draft items and recovery controls.

## Acceptance sequences

### Cancelled bridge repair

1. Focus a saved bridge connection with invalid authorization.
2. Start Re-pair and begin server discovery.
3. Cancel before discovery completes.
4. Open another connection or browse cached content.
5. Deliver the old discovery result and timeout.
6. Verify no server list, alert, credential mutation, focus change, or
   navigation occurs.
7. Start Re-pair again and verify newly initialized discovery state.

### Older connection timeout after newer success

1. Start opening connection A.
2. Start opening connection B.
3. Complete B successfully and enter its workspace.
4. Fail A with a timeout.
5. Verify B remains focused/open and the current destination is unchanged.

### Failed candidate preserves working connection

1. Open connection A.
2. Focus connection B and start opening it.
3. Fail B validation.
4. Verify B remains available from cache with Retry.
5. Focus A and verify its previous runtime remains usable.

### Offline relaunch

1. Focus a connection, open a session, and load messages.
2. Terminate network access and the application.
3. Relaunch without restoring network.
4. Verify the connection, selected session, cached transcript, freshness, and
   draft restore before network success.

### Draft restoration and eviction

1. Compose text and attachments while online or offline.
2. End the application without relying on input blur.
3. Relaunch and verify the complete draft.
4. Load enough other sessions to exceed ordinary message-history limits.
5. Verify the non-empty draft remains.

### Close is not delete

1. Close the focused runtime from an open chat.
2. Verify the same cached chat and composer remain visible offline.
3. Reopen the runtime and verify current server actions become available
   without replacing navigation.

### Multiple open failure isolation

1. Open connections A and B.
2. Focus A and open an A session.
3. Make B unavailable.
4. Verify B transitions to Unavailable while A remains Open and focused.
5. Retry B and verify its attempt does not disable A's Chat or navigation.

## Deferred and unchanged behavior

The mobile target described here does not itself:

- automatically queue or send offline messages;
- automatically replay failed mutations;
- define broad reconnect/backoff timing;
- automatically reopen every previously open runtime after process restart;
- change bridge WebSocket, HTTP, or hybrid routing/defaults;
- remove or replace the existing Connections, Sessions, or Messages
  destinations;
- redesign transcript content or viewport controls;
- require exact visual styling from the illustrative wireframes.

The final mobile multi-open presentation uses the same connection, cache,
navigation, and draft identities established by the staged lifecycle
migration.

## Requirement coverage

- State, authority, cancellation, and candidate promotion:
  `FCL-001`–`FCL-005`
- Status, adapters, app lifecycle, and navigation:
  `FCL-006`–`FCL-013`, `FCL-023`
- Hydration, cache, and offline continuity:
  `FCL-014`–`FCL-015`
- Draft durability and destructive actions:
  `FCL-016`–`FCL-020`
- Accessibility and stable production selectors: `FCL-021`