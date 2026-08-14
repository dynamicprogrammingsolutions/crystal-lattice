# Notification product specification

## Purpose

Notifications let backend components and plugins communicate persistent or
application-level information without inserting it into model-visible message
history.

## Notification scopes

Application notifications describe state belonging to one server application
owner or connection. The application notification store is authoritative for
the record, dismissal, resolution, expiration, and history during the record's
configured retention lifetime. The target store is durable across
`AgentApplicationOwner` and server-process restart.

Session notifications describe state belonging to one session. They are
persisted with the session. Their dismissal and terminal lifecycle state are
stored in the same session record.

Direct action results are not notifications. They may use the same display
payload, but they have no notification lifecycle or persistence guarantee.

## Proposed lifecycle

An ordinary notification is active while `pending` and becomes terminal when
it is:

- dismissed by the user;
- resolved because its underlying condition ended;
- expired according to retention.

Producers publish notifications using stable keys. Repeated publication updates
the active occurrence for that key. If the key currently maps to a terminal
record, publication creates a new lifecycle occurrence. If no occurrence exists,
publication creates one.

Plugin and background-work producers publish these recurring updates via a
stable key without passing `expected_revision`; the notification service owns
revision allocation and performs an atomic upsert against the current active
occurrence. A stale terminal or older occurrence does not suppress a later
key-scoped producer publication.

Dismissal applies only to the notification ID and revision the user saw. A
stale dismissal cannot hide a newer revision or a later stable-key occurrence.
The frontend that dismisses a notification may hide and cache that exact
revision immediately while sending the server mutation. If the request fails,
the cached revision remains hidden and the same `expected_revision` request may
be resent when that revision is observed again.

A cached dismissal never transfers to a newer revision. A newer pending
revision makes the old cache entry obsolete and is presented normally.

Other already-open devices do not have to reconcile the dismissal immediately.
A newly opened, reconnected, or explicitly refreshed frontend loads
authoritative state and does not present a server-dismissed record as active.

## Dismissability

Regular operation-progress notifications are user-dismissible. The user can
dismiss a progress banner at any time; dismissing the presentation does not
cancel the underlying operation. An explicit Cancel action remains the
operation control.

Nondismissible presentation remains available only for deliberately
exceptional cases, such as:

- permanent or environment status indicators;
- active interactions that must remain discoverable;
- presentations where hiding would remove the only path to a required response.

Long-running operation progress should not use nondismissible presentation
merely to preserve a Cancel action. A persistent notification must never
become a dead end: if it cannot be dismissed, it must have a viable recovery
action or reliably transition into a dismissible state.

## Refresh effects

A pending notification revision may explicitly request connection-scoped
refresh effects. The initial portable effects reload named sessions, reload
the session collection, or reload application-action definitions.

The effect belongs to the revision that explicitly requests it. A later
presentation or lifecycle update does not inherit the earlier command.
Dismissed, resolved, and expired revisions do not repeat it.

An active frontend consumer reloads authoritative state promptly. If the
affected consumer is inactive, unavailable, or not mounted, the connection
retains the invalidation until an appropriate consumer can reload
successfully. A frontend that started from cached data therefore converges on
authoritative state without requiring the producer to repeat the notification.

Notification effects do not navigate or change user focus. Action responses
may use the same explicit refresh field meanings, but action-only navigation
and mutation-derived behavior do not become notification behavior.

## Retention

Every notification has a defined lifetime. Initial retention policies support:

- explicit resolution;
- a TTL deadline for fresh frontend presentation;
- request-completion expiration;
- server-lifetime expiration.

TTL does not remove a notification that is already displayed and does not
change server lifecycle state by itself. A frontend that reconstructs its
notification host after the deadline does not present the elapsed record.

Server lifetime means the lifetime of the hosting runtime or server process,
not the lifetime of one replaceable `AgentApplication` generation. Reloading
or replacing an inner application may preserve the same lifetime. Whether a
particular host reconstructs that lifetime during an inner reload is an
implementation detail and is not a portable plugin contract.

Explicit dismissal or resolution takes precedence over every retention
boundary. A notification resolved before its TTL deadline or before a server
restart remains `resolved`; retention never replaces that terminal state with
`expired`.

Terminal records remain in durable history until history retention removes
them.

## Placement

On mobile:

- application notifications appear only on Sessions;
- session notifications appear only in their exact matching Chat;
- banners participate in normal layout and push content down;
- modal notifications use the owning screen's modal host.

On desktop:

- connection-level notifications from open connections share the
  message/detail-area rail and retain connection labels;
- the active session contributes session notifications at the same visual
  location without a redundant session label;
- modal notification requests use inline fallback.

## Notification history

Relevant screens expose a Notifications entry through the reusable top
pinnable action surface.

History presents compact active and terminal records with scope, status,
severity, and time filtering. Rich inline or modal content can be shown again
locally without reactivating the notification.

Historical content is read-only by default. Mutating actions require explicit
historical validity and server-side lifecycle/revision validation.

## Interaction readiness

Interactions extend the same stored item family but cannot be dismissed while
active. They require response, cancellation, timeout, or resolution.

The complete interaction remains in its owning Chat. Session lists and tabs
may show a compact waiting-for-input indicator.

## Safety

Notifications are hidden from provider/model history. Notification delivery
must not abort a request or tool call. Notification content must not contain
credentials or sensitive configuration values.

Frontend dismissal caches store only notification identity, scope, revision,
and retry metadata. They do not duplicate notification content.

Dismissal being revision-scoped for the mutation does not prevent producers from
issuing a later key-scoped update.

## Non-goals of this proposed follow-up

- Immediate dismissal reconciliation across every already-open device.
- A permanent audit log beyond configured history retention.
- Stage 2a request waiting.
- Stage 2b request suspension and restart.