# Notification product specification

## Purpose

Notifications let backend components and plugins communicate persistent or
application-level information without inserting it into model-visible message
history.

## Notification scopes

Application notifications describe state belonging to one running application
owner or connection. They survive replacement of `AgentApplication`, but not a
restart of the owning process.

Session notifications describe state belonging to one session. They are
persisted with the session and are restored when that session is reopened.

Direct action results are not notifications. They may use the same display
payload, but they have no notification lifecycle or persistence guarantee.

## Current lifecycle

A notification is pending until it is resolved by the backend. Creating a
pending notification with the same stable key updates the existing lifecycle
item.

The current frontend may dismiss one displayed revision locally. Dismissal
does not mutate backend state, and a later revision may appear again. A
resolved notification is no longer presented.

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

## Safety

Notifications are hidden from provider/model history. Notification delivery
must not abort a request or tool call. Notification content must not contain
credentials or sensitive configuration values.

## Non-goals of the implemented baseline

- Persistent dismissal is not implemented.
- Notification history is not exposed as a user-facing surface.
- Retention policies beyond resolved-item pruning are not implemented.
- Blocking or suspended interactions are not implemented.