# Notification product specification

## Purpose

Notifications let backend components and plugins communicate persistent or
application-level information without inserting it into model-visible message
history.

## Notification scopes

Application notifications describe state belonging to one server application
owner or connection. The application notification store is authoritative for
the record, dismissal, resolution, expiration, and history during the record's
configured retention lifetime.

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

The frontend that dismisses a notification updates immediately after the
server mutation succeeds. Other already-open devices do not have to reconcile
the dismissal immediately. A newly opened, reconnected, or explicitly
refreshed frontend loads authoritative state and does not present a dismissed
record as active.

## Retention

Every notification has a defined lifetime. Initial retention policies support:

- explicit resolution;
- TTL expiration;
- request-completion expiration;
- server-lifetime expiration.

Terminal records remain in history until history retention removes them.

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

## Non-goals of this proposed follow-up

- Immediate dismissal reconciliation across every already-open device.
- A permanent audit log beyond configured history retention.
- Stage 2a request waiting.
- Stage 2b request suspension and restart.