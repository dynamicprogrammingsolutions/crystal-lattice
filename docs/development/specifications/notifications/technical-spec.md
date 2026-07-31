# Notification technical specification

## Record

The implemented record contains:

- `id`: backend-assigned lifecycle identity;
- `key`: producer-provided deduplication identity;
- `kind`: `notification`;
- `status`: `pending` or `resolved`;
- `severity`: `info`, `success`, `warning`, or `error`;
- `title` and `body`;
- `created_at` and `updated_at`;
- optional `request_id`;
- producer `source` including `plugin`;
- `display`: an action-display payload;
- optional `resolution`;
- `model_visibility: hidden`.

## Authoritative state

Session notifications are stored under:

```text
Session.metadata.notifications.items
```

Application notifications are stored by the stable application owner in
memory. The event store and application notification collection outlive an
individual `AgentApplication`.

## Operations

Session notifications support create, update by ID, update by key, resolve,
and list. Application notifications support equivalent owner-scoped
operations.

Creating a notification with the key of an existing pending notification
updates that item while retaining its ID. The current implementation preserves
all pending session notifications and prunes older resolved records according
to the configured item limit.

## Events

Application events:

- `application_notification_created`
- `application_notification_updated`

Session events:

- `session_notification_created`
- `session_notification_updated`
- `session_notification_resolved`

Application events omit `session_id`. Session events include it. Event
delivery is best effort; persisted session metadata is the reconnect authority
for session notifications.

## Concurrency and persistence

Session notification read-modify-write operations use the application
session lock and save a new immutable `Session`. Notification metadata is
preserved by request checkpoint reconciliation.

The tool-facing notification sink catches failures and returns no notification
result rather than failing the tool or request. Application plugins calling
the application API directly receive validation errors.

## Current dismissal

Dismissal is a frontend-only presentation operation. Frontends identify a
display revision using notification ID and `updated_at`. Dismissing one
revision does not resolve the backend record and does not suppress a later
update.

## Compatibility

Consumers must ignore malformed records and unknown event types. Explicit
supported presentations take precedence over producer defaults. Unknown
presentation values are rejected or reported rather than silently presented
with unrelated semantics.