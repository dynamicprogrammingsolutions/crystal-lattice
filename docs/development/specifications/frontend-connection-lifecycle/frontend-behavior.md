# Portable frontend connection behavior

This page defines framework-independent interaction behavior. Mobile and
desktop may use different navigation and presentation components while
conforming to the same lifecycle outcomes.

## Independent state dimensions

A frontend represents these dimensions independently:

| Dimension | Example values |
| --- | --- |
| Saved | absent, saved, editing, pending deletion |
| Focus | unfocused, focused |
| Runtime | closed, opening, open, reconnecting, unavailable, repair required, error |
| Attempt | absent, active, cancelling, succeeded, failed, cancelled, superseded |
| Cache | absent, available with freshness, invalidated, persistence error |
| Draft | empty, saving, saved, save failed, uncertain send |

A row may therefore be focused and unavailable, or unfocused and open. The UI
does not infer one dimension solely from another.

## Connection selection and actions

Selecting a saved connection changes focus immediately and makes its cached
workspace eligible for presentation. A platform may also begin opening the
runtime from the same gesture, but opening failure does not undo focus unless
the user explicitly returns to the previous connection.

The Connections surface exposes actions appropriate to state:

| Runtime state | Primary actions |
| --- | --- |
| Closed | Open |
| Opening | Cancel |
| Open | Close |
| Reconnecting | Cancel or continue offline |
| Unavailable or Error | Retry, Edit when configuration may be wrong |
| Repair required | Re-pair or Repair |

Deleting a saved connection is not the fallback action for an ordinary
connection error.

## Attempt presentation and cancellation

Progress and error presentation is scoped to the connection or unsaved wizard
attempt that owns it. One global loading flag does not prevent unrelated open
connections from remaining usable.

Cancel:

- becomes effective without waiting for the network timeout;
- moves the attempt to a terminal cancelled state;
- aborts supported requests and disconnects temporary transports;
- suppresses later success, failure, timeout, alert, repair, and navigation
  effects from that attempt;
- leaves the previous usable runtime and focused workspace unchanged;
- leaves a saved connection record and its caches intact.

Starting a later attempt supersedes any older attempt whose completion would
conflict with the later intent. Supersession has the same no-late-effect rule
as cancellation.

## Navigation authority

Connection lifecycle operations return typed outcomes. They do not navigate by
mutating unrelated screen state after an await.

A frontend applies a navigation result only when:

- it belongs to the current authoritative attempt;
- it was requested by the current user intent;
- the destination still belongs to the same connection;
- a later focus or navigation action has not superseded it.

Background reconnect, app foregrounding, health checks, notification refresh,
and transport timeout never navigate by themselves.

Session identity and screen keys include both connection ID and session ID.
Each connection retains its own selected session or open-session collection.

## Offline surfaces

When cached content exists without an open runtime:

- Home, Connections, Sessions, and Messages navigation remains available;
- the owning connection and cache freshness are visible;
- cached rows and transcript content remain interactive for local operations;
- actions requiring server authority are disabled or request reconnection;
- empty cache and unavailable server are presented as separate conditions;
- failed refresh leaves prior cached content visible.

Offline mode does not claim that cached server state is authoritative. A
successful refresh updates freshness; merely opening cached content does not.

## New-connection and repair flows

A wizard is an attempt surface, not a replacement for the current workspace.
Opening it does not close a usable runtime.

An unsaved successful connection creates one saved record after validation and
then may focus it. A repair flow carries the existing connection ID and updates
that record after successful reauthorization.

Bridge server discovery and pairing state is reset when a repair flow is
started again. Cancelling disconnects the temporary bridge transport and
prevents the previous server list from reappearing.

## Connection-kind refinements

### Direct and discovery

Manual and discovery records use direct HTTP. Discovery determines a candidate
address; successful discovery alone is not runtime validation.

Because direct HTTP does not maintain a socket, Open means the frontend has a
usable configured transport with a successful current validation. Later
request failure may transition the runtime to unavailable without deleting the
transport configuration.

### Bridge

Bridge behavior follows the bridge-connectivity specification for transport
selection, pairing, resume, and repair errors.

Repair preserves connection ID, cache ownership, and workspace state. WebSocket
and HTTP/hybrid temporary resources follow the same attempt authority and
cancellation rules.

### Cloud

Cloud connection links are validated before promotion. Authentication,
authorization, unavailable instance, and non-success HTTP responses are
reported as failures under the normalized lifecycle contract rather than
being treated as an open runtime.

### Bonjour discovery

Discovery scanning has explicit start, stop, and cancellation behavior.
Results from an old scan do not populate a later scan or a dismissed wizard.

## Error presentation

User-visible errors contain:

- a portable category and concise explanation;
- the affected connection;
- whether cached content remains available;
- an appropriate recovery action;
- diagnostic detail only where the product exposes a diagnostics surface.

Cancellation and supersession are ordinary terminal outcomes and do not
produce failure alerts.

Recoverable connection problems should normally use status rows or banners
rather than a sequence of blocking alerts. Pairing codes and other explicit
user decisions may retain modal presentation where platform conventions
require it.

## Draft presentation

The composer remains available offline. Text and attachment changes enter a
saving state and become saved after durable persistence. A failed write remains
visible and retryable; the frontend does not display Saved solely because
in-memory state changed.

A non-empty draft is associated with exactly one connection/session pair.
Switching connection or session restores the corresponding draft and does not
move content between scopes.

Offline Send is disabled or offers Reconnect to send. Automatic delayed send
is not implied.

## Mobile refinement

Mobile presents one focused workspace through bottom navigation. It may use
one open runtime during an intermediate migration, while the final target
allows several independently open runtimes without changing cache identity,
focus, or operation authority.

The connection wizard may occupy the Connections tab, but Sessions and
Messages remain available for the focused cached workspace.

The screen-level mobile contract, including illustrative layouts, state/action
tables, connection switching, repair, offline screens, and composer behavior,
is defined in [Mobile connection and offline UX](mobile-ux.md).

## Desktop refinement

Desktop may retain several open runtimes and several session tabs. Focusing a
connection controls the Sessions panel; focusing a session tab controls the
message workspace. Closing a runtime leaves its tabs available from cache.

Closing while an open attempt is pending supersedes that attempt so a late
success cannot reopen the connection.

The screen-level desktop contract, including the multi-column shell,
connection/runtime controls, focused-connection and active-tab policy, cached
tabs, offline composition, and native macOS behavior, is defined in
[Desktop connection and offline UX](desktop-ux.md).

## Accessibility and testability

Connection rows, statuses, primary actions, wizard cancellation, repair
controls, offline indicators, and persistence errors expose accessible roles,
labels, and stable production selectors where native verification requires
them.

Status is not communicated by color alone. Loading and disabled controls
explain their state through accessible text.