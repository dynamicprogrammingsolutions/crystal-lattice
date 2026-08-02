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

Creating with the stable key of an active record updates that record. Creating
with the key of a terminal record creates a new lifecycle occurrence.

The frontend that dismisses a notification may hide and cache that exact
revision immediately while sending the server mutation. If the request fails,
the cached revision remains hidden and the same expected-revision request may
be resent when that revision is observed again.

A cached dismissal never transfers to a newer revision. A newer pending
revision makes the old cache entry obsolete and is presented normally.

Other already-open devices do not have to reconcile the dismissal immediately.
A newly opened, reconnected, or explicitly refreshed frontend loads
authoritative state and does not present a server-dismissed record as active.

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

## Non-goals of this proposed follow-up

- Immediate dismissal reconciliation across every already-open device.
- A permanent audit log beyond configured history retention.
- Stage 2a request waiting.
- Stage 2b request suspension and restart.