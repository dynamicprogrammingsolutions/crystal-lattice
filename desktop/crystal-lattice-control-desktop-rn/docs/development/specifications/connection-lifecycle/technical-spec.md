# Desktop connection lifecycle host technical specification

## Architecture

The target desktop host composes the shared lifecycle controller with its
multi-column workspace:

```text
saved records --------------------+
                                  v
Connections panel ---- DesktopRoot lifecycle host ---- shared controller
        |                         |                           |
        v                         v                           v
focused Sessions          persistent session tabs      runtime map
                                  |
                                  v
                         active cached/live Chat
```

`DesktopRoot` owns one controller instance. Package hooks adapt its immutable
snapshot to existing panel APIs during staged migration. No panel implements
its own operation generation.

## Controller and runtime mapping

The desktop host:

- injects manual direct HTTP factory and readiness validation;
- observes all runtime/attempt/error snapshots;
- provides backend lookup by connection ID;
- passes all open runtimes to the global display layer;
- passes the focused backend to Sessions;
- passes each tab's owning backend to its Chat pane;
- disposes candidates/runtimes at host teardown.

The runtime map remains transient. Several records may be Open concurrently.
Closing one does not alter another.

The initial adapter UI boundary remains manual direct HTTP. Shared bridge,
cloud, and discovery adapters may exist without becoming desktop-supported
editor behavior.

## Connection row mapping

Each saved row combines:

- persisted record;
- focused connection ID;
- runtime status/resource;
- current attempt and phase;
- normalized lifecycle error.

Opening one row begins a connection-scoped shared attempt. The row exposes
Cancel during Opening. Close invalidates a pending open and closes an
established runtime through the same controller.

Late completion cannot recreate a closed runtime. Unrelated rows remain
interactive during one attempt.

## Candidate and editor event authority

The separate connection editor emits one completion/cancel event owned by a
window/editor generation.

New or edited configuration:

- validates local fields in the window;
- preserves ID on Edit;
- identifies whether submission means Save or Save & Open;
- begins candidate validation without removing a usable old runtime;
- commits/presents only while editor and attempt authority remain current;
- ignores an event from a closed or superseded window.

If Save without Open is supported, the record may persist offline without
claiming runtime success. If Save & Open fails, the selected persisted-record
policy is explicit and the old runtime remains usable until the user closes
it.

## Focus and active-tab coordinator

Desktop stores:

- one focused connection for Connections/Sessions;
- persistent tabs keyed by connection/session;
- one active tab.

When follow-active-tab is enabled, tab activation atomically:

1. sets active tab;
2. focuses its connection;
3. asks Sessions to select/reveal that connection's session.

When disabled, tab activation does not change focused connection. The active
Chat and Sessions panel label their separate connection identities.

Changing connection focus does not change active tab. Opening a session from
Sessions creates/activates its connection/session tab.

The coordinator uses monotonic intent when asynchronous row measurement or
window events are involved. A stale scroll/select completion cannot override a
later tab/focus action.

## Persistent tabs and warm panes

Open-tab persistence restores tab identity, title/subtitle, active tab, and
range preferences only after hydration.

All tab labels remain visible even when resource policy mounts only a bounded
most-recent set of Chat panes. Pane unmount:

- flushes transcript and complete draft state;
- stops pane-owned subscriptions;
- does not remove the tab;
- does not delete local/server data.

Pane remount loads cache/draft by connection/session before network refresh.
No user-visible state depends solely on component-local arrays.

## Runtime failure convergence

The desktop host reports relevant transport/backend failures to the lifecycle
controller. A direct HTTP runtime may transition from Open to Unavailable even
though it has no persistent socket.

Connection row, Sessions `isOnline`, and every owning Chat status derive from
the same runtime snapshot. Retry revalidates without deleting cache/tabs.

Errors normalize to portable categories. Raw details remain diagnostics and
exclude sensitive request content.

## Sessions cache host

Sessions cache is keyed by connection and hydrated before writes. The focused
panel receives:

- focused record/name;
- runtime status/backend;
- cached summaries and server freshness;
- pending invalidation/refresh failure where applicable.

Local search/filter/window selection remains available offline. Remote actions
are gated by the focused runtime.

Failed refresh retains prior data and freshness. Draft or transcript
preference writes do not update Sessions or Messages server freshness.

## Chat and draft host

Each tab receives backend and cache by its own connection/session. Cached Chat
remains readable offline.

The composer consumes shared versioned draft storage:

- text remains editable offline;
- durable status is visible;
- attachments persist order, placement, metadata, preview identity,
  server-asset/local reference, readiness, and error;
- draft survives pane unmount and application restart;
- ordinary message cache eviction cannot remove it;
- uncertain sends persist submitted revision and idempotent recovery.

Server-dependent attachment creation is gated separately from text editing.
Reopening a runtime never submits automatically.

Acknowledgement clears only the submitted draft revision. Local attachment
cleanup is reference-aware.

## Displays and notifications

The global display layer observes every open runtime and labels
connection-owned presentations. The active Chat contributes exact session
presentations.

Background connection events and action effects do not focus a connection or
activate a tab unless an explicit user action requests navigation.

Closing one runtime disposes only its connection-level observer. Cached
presentations follow their owning notification/action contracts.

## Native windows and popovers

Connection and settings editors remain separate windows. Anchored transient
controls remain native popovers.

Every native event includes enough owner identity/generation to reject:

- an event after window cancellation;
- an event for an older editor instance;
- a connection/session result after its owner changed;
- a callback after host disposal.

Native modal behavior is not introduced where macOS hosting does not support
it reliably.

## Deletion and cleanup

Desktop commands distinguish:

- close tab;
- close runtime;
- clear server-derived cache;
- discard one draft;
- delete one saved connection;
- clear all connections/local state.

The command payload and confirmation share explicit scope. Deleting a record
removes only the approved local classes and leaves remote server data.

## Accessibility and macOS verification

Stable selectors derive from connection/session IDs and cover:

- connection focus/status/Open/Cancel/Close/Retry/Edit/Delete;
- editor fields and submission;
- focused Sessions status and rows;
- tabs, active state, owning connection, and Close;
- active Chat runtime/offline state;
- draft status, attachments, and uncertain send.

Shared tests own operation ordering. Desktop Jest/component tests own host
mapping. XCUITest uses production panels/windows to verify:

- Cancel/Close during Opening with late success;
- two independent open runtimes;
- follow-active-tab enabled and disabled;
- runtime failure to offline cached Chat;
- editor candidate failure preserving old runtime;
- offline tab relaunch;
- complete draft restoration after pane unmount and process relaunch.

The native harness may inject deterministic adapters but does not duplicate
the production connection or tab UI.

## Compatibility

The staged host migration preserves:

- existing manual saved-record IDs and AsyncStorage keys;
- current several-open-connection behavior;
- persisted tab IDs and presentation;
- connection/session cache keys;
- native window/popover conventions;
- notification and transcript contracts;
- manual-only desktop editor scope until separately extended.