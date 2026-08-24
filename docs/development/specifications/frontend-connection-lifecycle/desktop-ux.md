# Desktop connection and offline UX

This page refines the portable frontend lifecycle for the Crystal Lattice
macOS desktop application. It defines the target behavior of the Connections
panel, focused Sessions panel, persistent cross-connection session tabs,
active Chat pane, connection-level display rail, native windows, offline
content, and composer continuity.

The product outcomes remain authoritative in
[Product behavior and target user experience](product-spec.md). Portable
semantics shared with mobile remain authoritative in
[Portable frontend behavior](frontend-behavior.md). This page defines how
those outcomes appear in the desktop application's multi-column and
multi-runtime workspace.

## Normative and illustrative content

The following are normative:

- connection, runtime, focus, tab, cache, and draft ownership;
- which states and consequences are visible;
- which actions are available;
- when focus or navigation changes;
- cancellation, candidate promotion, offline, failure, and recovery behavior;
- native-window and popover interaction boundaries;
- accessibility meaning and stable selector identity.

The text wireframes illustrate information hierarchy. Exact dimensions,
spacing, typography, colors, icons, and non-semantic copy may follow the
desktop design system. Equivalent clear status names and accessible labels are
allowed where exact wording is not required.

## Desktop workspace model

Desktop has five coordinated surfaces:

```text
Connections panel
        |
        v
focused Sessions panel       persistent session tab strip
                                      |
                                      v
                               active Chat pane
                                      |
                                      v
                        connection/session display rail
```

An illustrative full workspace:

```text
┌────────────────────┬─────────────────────┬──────────────────────────────┐
│ Connections        │ Sessions            │ Session A | Session B        │
│ 3 saved · 2 open   │                     ├──────────────────────────────┤
│                    │ Focused: Ireland    │ Office Mac · Session B       │
│ Ireland      Open  │ Online · cached     │ Offline · cached at 14:32    │
│ Office      Closed │                     │                              │
│ Home         Error │ Session A           │ Cached transcript            │
│                    │ Session C           │                              │
│ [New connection…] │                     │ Draft saved locally          │
└────────────────────┴─────────────────────┴──────────────────────────────┘
```

The model distinguishes:

- **focused connection**: controls the Connections selection and Sessions
  panel;
- **open runtimes**: zero or more connection-scoped transports/backends;
- **session tabs**: durable workspace entries keyed by connection and session;
- **active tab**: controls the visible Chat pane;
- **warm pane**: an implementation-mounted tab; not a separate user-visible
  identity;
- **cache and draft state**: restores a tab independently from runtime or
  component mounting.

The focused Sessions connection and active Chat connection may differ when the
user has selected independent-panel behavior.

## Launch and restoration

Desktop hydrates saved connections, open tabs, the active tab, caches, and
drafts before treating empty initial state as durable state.

When persisted tabs exist:

- every valid tab label is restored;
- the previous active tab is restored when possible;
- the initially focused connection is the active tab's connection unless a
  separately persisted valid focus policy selects another;
- cached Messages content and draft state are eligible immediately;
- a connection does not have to open successfully before its tab can appear;
- network opening follows the explicit desktop reopen policy and does not
  replace restored focus or tabs.

When no persisted tab exists:

- the most recently selected valid connection may become focused;
- an automatic open may occur only under a documented policy;
- opening failure leaves the saved connection focused with available cached
  Sessions content.

Restoration never silently deletes a tab merely because its connection is
temporarily unavailable. A later authoritative server response may identify a
deleted session and offer or perform the documented stale-tab resolution.

## Connections panel

### Panel responsibilities

The Connections panel:

- lists saved connections;
- shows saved and open counts;
- distinguishes focused state from runtime state;
- exposes Open, Cancel, Close, Retry, Edit, and Delete;
- opens the new/edit connection window;
- reports connection-scoped errors without blocking unrelated runtimes;
- permits several connections to remain open.

### Saved connection row

Each row presents:

- display name;
- supported connection-kind detail without credentials;
- focused indication;
- runtime or attempt status as text;
- a primary lifecycle action;
- a concise scoped error/recovery indication when applicable.

Illustrative rows:

```text
┌──────────────────────────────────────────┐
│ ✓ Ireland Server                   Open  │
│   127.0.0.1:8080                  [Close]│
├──────────────────────────────────────────┤
│   Office Mac                 Connecting  │
│   192.168.1.42:8080            [Cancel] │
├──────────────────────────────────────────┤
│   Home Server                Unavailable │
│   Last validated yesterday      [Retry] │
└──────────────────────────────────────────┘
```

Focus is not communicated by background color alone. Runtime state is not
communicated by color alone.

### Status and actions

| State | Primary behavior | Additional behavior |
| --- | --- | --- |
| Closed | Open | Focus and browse cache/tabs |
| Opening | Cancel | Keep other runtimes usable |
| Open | Close | Health/detail actions may remain |
| Reconnecting | Cancel or continue offline | Show last usable time |
| Unavailable | Retry | Edit when address/configuration may be wrong |
| Repair required | Repair or Re-pair when that kind is supported | Keep cache/tabs |
| Configuration error | Edit | Retry after correction |
| Persistence error | Retry local save | Identify affected local state |

Cancellation and supersession are terminal attempt outcomes rather than
persistent Error states.

### Row activation

The desktop default may retain convenient focus-and-open behavior:

1. row activation focuses the connection immediately;
2. its cached Sessions content appears immediately;
3. if no usable runtime exists, an Open attempt begins;
4. failure does not undo focus or remove cached content;
5. explicit Open/Retry/Close/Cancel remains available independently.

A setting may select focus-only behavior. Focus-only activation never opens or
closes a runtime.

Opening one connection does not close another. Connection-scoped progress does
not disable unrelated rows, tabs, or runtimes.

## Multiple open connections

Desktop permits several established runtimes simultaneously. Each runtime:

- has independent status, attempts, errors, and resource ownership;
- can back one or more open session tabs;
- can contribute connection-level notifications;
- can be closed without closing another runtime;
- can recover without taking focus or active-tab ownership.

One connection's failure does not convert other open rows to a loading/error
state. A global connection loading flag is not used.

Closing a runtime:

- changes only that runtime to Closed;
- retains the saved record;
- retains the focused connection unless the user selects another;
- retains session tabs;
- retains caches, transcript state, and drafts;
- makes applicable Chat panes offline.

## Open, cancellation, and candidate promotion

Every Open, Retry, reconnect, and edited-configuration validation is one
authoritative attempt.

Opening is transactional:

```text
create candidate
    ↓
validate while existing runtime remains usable
    ↓
confirm current operation authority
    ↓
promote candidate
    ↓
dispose replaced runtime only after promotion
```

Close or Cancel during Opening:

- invalidates operation authority immediately;
- removes Opening presentation;
- aborts supported work and disposes candidate resources;
- prevents late success from reopening the row;
- prevents late failure from replacing a newer status or presenting an alert.

Starting another attempt for the same connection supersedes the older attempt.
Independent connection attempts may progress concurrently.

Editing or reopening one connection ID does not remove a currently usable
runtime before the edited candidate validates.

## Runtime status convergence

For stateless direct HTTP, Open means the frontend has a configured runtime
whose current validation or use succeeded. It is not a claim that a persistent
socket exists.

A relevant later transport/backend failure can transition the runtime to
Unavailable. The row, Sessions subtitle, and active Chat status converge on
the same connection state.

A failed Sessions refresh:

- retains prior cached sessions;
- marks refresh failure or runtime unavailability as applicable;
- does not replace server-derived freshness with local draft activity;
- does not close unrelated runtimes.

Retry revalidates without deleting tabs, caches, or drafts.

## New and edit connection window

Connection configuration remains in a separate desktop window. The window:

- identifies New versus Edit;
- validates local fields before submission;
- preserves stable connection ID on Edit;
- provides accessible labels and stable selectors;
- closes through explicit Cancel or successful submission;
- does not mutate another connection.

The action copy makes network behavior explicit. Supported patterns include:

```text
[Cancel] [Save] [Save & Open]
```

or:

```text
[Cancel] [Save & Open]
```

If plain Save is available, it may persist a currently unreachable
configuration without claiming the runtime is Open. If Save also opens, its
label or surrounding copy communicates that behavior.

For an edited open connection:

- candidate validation is non-destructive;
- failure leaves the previous runtime usable until the user explicitly closes
  it or approves an offline saved replacement policy;
- successful promotion updates the runtime under the same connection ID;
- caches, tabs, and drafts retain ownership.

The initial desktop lifecycle target supports manual direct HTTP connection
editing. Additional bridge, cloud, or discovery editor flows require an
explicitly specified extension.

## Focused connection and active tab

The focused connection controls the Connections and Sessions panels. The
active tab controls the visible Chat pane. The two identities are explicit and
do not silently overwrite each other.

### Follow-active-tab enabled

When the setting is enabled, selecting a session tab:

1. activates that tab;
2. focuses the tab's owning connection;
3. presents that connection in Sessions;
4. selects and, when practical, scrolls its session row into view;
5. does not open or close a runtime merely because focus changed.

If the session is filtered or outside the current Sessions window, the panel
retains its filters/window unless the documented follow policy intentionally
reveals the row. It never selects a same-named session from another
connection.

### Follow-active-tab disabled

When disabled:

- selecting a tab changes only the active Chat pane;
- the Sessions panel remains on its independently focused connection;
- the UI continues to label both connection identities;
- selecting a connection row changes Sessions but not the active tab;
- opening a session from Sessions creates/activates that session's tab.

This supports comparing one connection's session list while reading another
connection's Chat.

### Changing the setting

Enabling follow applies to the current or next active-tab intent according to
the control's documented behavior. It does not close tabs or runtimes.
Disabling follow preserves the current focused connection until the user
changes it.

## Sessions panel

The Sessions panel always identifies its focused connection and combines
runtime state with cache freshness:

```text
Sessions
Focused: Office Mac · offline · cached yesterday
```

Required distinctions:

| Condition | Presentation |
| --- | --- |
| Open with current data | Normal content; refresh available |
| Opening/reconnecting with cache | Retain content; show scoped progress |
| Closed/unavailable with cache | Retain content; show offline and Open/Retry |
| Refresh failed with cache | Retain prior content and earlier freshness |
| Offline without cache | Explain that no sessions have been loaded locally |
| Cache invalidated | Retain content without presenting it as authoritative |
| No focused connection | Prompt to select a saved connection |

Local behavior remains available offline:

- search and filter cached summaries;
- adjust local visible windows;
- select a cached session;
- open a cached session tab;
- inspect locally available presentation fields.

Server-authoritative behavior is disabled or starts explicit opening:

- refresh;
- create session;
- switch agent;
- modify settings/plugins;
- run remote application/session actions;
- perform remote destructive actions.

Disabled controls expose why they are unavailable.

## Session tabs

A tab is keyed by connection ID and session ID. Its label makes connection
identity visible even when several connections have similarly named sessions.

Tabs:

- persist independently from runtime status;
- restore from cache after application relaunch;
- remain visible when their pane is not mounted;
- retain title/subtitle updates scoped to their connection;
- can be activated or closed without closing a runtime;
- retain cached transcript, range, viewport, and draft state through pane
  unmount/remount.

Closing a tab:

- removes that workspace tab;
- does not close its connection runtime;
- does not delete the server session;
- does not implicitly delete a non-empty draft without the documented
  confirmation/recovery policy.

The tab action menu exposes real actions or is absent. It does not present
placeholder commands. Useful actions may include Close, Close Others, Close
Tabs for Connection, and Focus Owning Connection.

Runtime status may be shown on each tab or in the active pane, but every tab
always retains unambiguous connection identity. Offline state of the active tab
is visible without consulting the Connections panel.

## Chat pane and offline transcript

The Chat header identifies:

- session title and ID;
- owning connection;
- runtime/offline state;
- cache freshness or failed-refresh state where applicable.

Cached transcript content remains readable after:

- explicit runtime Close;
- later runtime failure;
- failed Open/Retry;
- application relaunch;
- pane unmount/remount;
- focus moving to another connection.

Local behavior remains available:

- read and scroll cached messages;
- use loaded-range and viewport controls within available data;
- copy content;
- inspect cached details;
- edit or discard the local draft;
- switch tabs.

Server-authoritative actions are disabled or open/retry-gated:

- append, send, resend, and cancel-server-request;
- modify/delete messages;
- switch agent;
- snapshot operations;
- remote plugin/session actions.

The offline state does not alter transcript range/viewport semantics owned by
the chat transcript specification.

## Composer and draft behavior

### Offline composition

The composer remains editable without a backend. Offline presentation does not
label the entire composer read-only merely because Send is unavailable.

The primary action is disabled with an accessible reason or becomes an
explicit Open/Reconnect to send action. Opening a runtime never submits the
draft automatically.

Attachment addition remains available offline only where the selected
attachment path can create a durable local draft without immediate server
authority. An attachment action that requires server storage explains that
requirement without disabling text composition.

### Persistence status

The composer distinguishes:

```text
Saving…
Saved locally
Draft could not be saved locally [Retry]
```

Exact copy is illustrative. Saved means the current draft revision reached
durable storage, not merely component state.

Text edits persist with bounded debounce and flush at tab, pane,
application-lifecycle, and disposal boundaries. A write failure remains
visible and retryable.

### Attachment draft continuity

The complete attachment draft persists:

- order and placement;
- metadata;
- preview/display identity;
- upload/readiness state;
- app-managed or durable server-owned content reference;
- recoverable error state.

A pane may be unmounted to bound desktop resource usage. Remounting it from a
still-visible tab restores the complete draft. Component-local arrays are not
the sole draft authority.

An attachment that cannot be reopened remains visible with Replace/Remove or
another recovery action rather than disappearing.

### Acknowledgement and uncertain send

Submission captures one draft revision. An acknowledged append/send clears
only that revision. Newer edits made while the request is pending remain.

When acknowledgement is uncertain, the Chat pane retains durable submitted
content and idempotent recovery:

```text
Send not yet confirmed
The server may have accepted this message.
[Check status] [Retry safely]
```

The state survives tab unmount and application restart. Reopening a runtime
does not automatically retry.

## Connection-level displays and notifications

Connection-level notifications from every open runtime may share the desktop
display rail. Each presentation retains connection identity.

The active Chat contributes session-owned displays for its exact
connection/session. A background connection display may present through the
portable notification/action contract but does not focus a connection or
activate a tab unless an explicit current user action requests navigation.

Desktop modal requests continue to follow the documented platform fallback.
This connection UX specification does not replace notification or action
display contracts.

## Native windows and popovers

Desktop follows current macOS interaction boundaries:

- anchored transient menus and filters use native popovers;
- connection, server, session, and attachment editors may use separate native
  windows;
- connection/error banners remain in normal application layout;
- React Native modal behavior is not assumed where the desktop host does not
  support it reliably.

Closing or cancelling a native connection window prevents its later event from
creating, editing, opening, or focusing a connection.

Window and popover state is connection/session-scoped and cannot commit to a
newer editor or active tab after cancellation.

## Closing and destructive actions

Desktop distinguishes:

### Close tab

Removes one local workspace tab. It does not close a runtime or delete a server
session.

### Close runtime

Stops one live runtime and retains saved connection, focus, tabs, caches, and
drafts.

### Clear cached server content

Removes selected server-derived cache according to explicit scope. Non-empty
drafts remain unless the action explicitly includes them.

### Discard draft

Removes one connection/session draft after confirmation when non-empty. It
does not delete server messages.

### Delete saved connection

The confirmation names every local consequence:

- saved configuration and credentials;
- runtime closure;
- cached Sessions/Messages data;
- tabs for that connection;
- local drafts and owned attachment content.

It states that remote server data is not deleted.

### Clear all connections

Bulk removal separately identifies saved connections, runtimes, caches, tabs,
and drafts. The confirmation does not hide drafts under a generic cache label.

## Connection-kind boundary

The initial desktop implementation target supports manual direct HTTP
connections while consuming a shared lifecycle model capable of other kinds.

Adding desktop bridge, cloud, or discovery behavior requires:

- supported editor/pairing/input surfaces;
- kind-specific status and recovery;
- credential handling;
- platform tests;
- an explicit update to this page and live requirements.

The absence of a desktop UI for one connection kind does not weaken the shared
adapter contract or mobile behavior.

## Accessibility and production selectors

Required accessible meaning includes:

- connection row identity and focused state;
- runtime status;
- Open, Cancel, Close, Retry, Edit, and Delete;
- editor fields and submission behavior;
- focused Sessions connection and online/offline/freshness state;
- session row connection/session identity;
- tab connection/session identity, active state, and Close;
- active Chat connection/runtime state;
- disabled server-action reason;
- draft Saving, Saved, and Save failed;
- recoverable attachment and uncertain-send state;
- destructive-action consequences.

Status and focus are not color-only. Hover-only controls remain keyboard and
accessibility reachable.

Production selectors use stable connection/session IDs rather than row
positions or visible copy. Native tests can select:

- connection row, focus, status, and lifecycle action by connection ID;
- new/edit connection controls;
- Sessions state and rows by focused connection/session;
- tabs and tab Close by connection/session;
- active Chat online/offline state;
- draft persistence and recovery state.

## Acceptance sequences

### Close while opening

1. Start opening connection A.
2. Activate Cancel or Close before readiness validation returns.
3. Resolve the old validation successfully.
4. Verify A remains Closed, no backend becomes available, and no stale error or
   focus change occurs.

### Independent concurrent opens

1. Start opening connections A and B.
2. Complete B before A.
3. Verify B becomes Open without blocking A.
4. Complete A.
5. Verify both are Open and retain independent runtimes/status.

### Follow-active-tab enabled

1. Focus connection A in Sessions.
2. Activate a tab owned by connection B.
3. Verify B becomes focused in Connections/Sessions.
4. Verify B's session row is selected/revealed when applicable.
5. Verify no runtime opens or closes solely because focus followed.

### Follow-active-tab disabled

1. Focus connection A in Sessions.
2. Activate a tab owned by connection B.
3. Verify Chat shows B while Sessions remains on A.
4. Verify both surfaces clearly label their connection.

### Candidate edit failure

1. Keep connection A open.
2. edit A to an unreachable address and choose the open/validate action.
3. Fail candidate validation.
4. Verify the previous runtime remains usable and tabs/caches/drafts remain
   under A's stable identity.

### Runtime failure after open

1. Open A successfully.
2. Make A unavailable and issue a relevant request.
3. Verify A converges to Unavailable and offers Retry.
4. Verify cached Sessions/Chat remain visible and connection B is unaffected.

### Offline relaunch with tabs

1. Open tabs from connections A and B and load messages.
2. Terminate network access and the application.
3. Relaunch.
4. Verify tab labels, active tab, focused policy, cached transcript, range,
   viewport, and drafts restore before network success.

### Draft survives pane eviction

1. Compose text and attachments in tab A.
2. Activate enough other tabs for A's pane to be unmounted.
3. Return to tab A.
4. Verify complete text, attachments, metadata, order, and status restore.

### Close is not delete

1. Close A's runtime while an A tab is active.
2. Verify the tab and cached transcript remain offline.
3. Reopen A and verify server actions return without replacing the tab.
4. Delete A and verify the confirmation names tabs, caches, and drafts before
   removal.

## Deferred and unchanged behavior

This desktop target does not itself:

- add bridge, cloud, or Bonjour connection UI;
- automatically open every connection with a restored tab;
- automatically send or replay offline work;
- define broad reconnect/backoff timing;
- change bridge transport routing/defaults;
- replace native window or popover conventions;
- redesign transcript content or viewport controls;
- require all session panes to remain mounted;
- require exact styling from the illustrative wireframes.

## Requirement coverage

- State, operation authority, cancellation, and promotion:
  `FCL-001`–`FCL-005`
- Status, adapters, application lifecycle, and navigation:
  `FCL-006`–`FCL-013`, `FCL-022`
- Hydration, cache freshness, and offline workspace:
  `FCL-014`–`FCL-015`
- Draft durability and destructive actions:
  `FCL-016`–`FCL-020`
- Accessibility and stable production selectors: `FCL-021`