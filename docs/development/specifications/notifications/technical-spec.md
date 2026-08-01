# Notification technical specification

Status: Accepted; implementation pending

## Record family

The record family contains:

- `id`: backend-assigned lifecycle identity;
- `revision`: monotonically increasing mutation revision;
- `key`: producer-provided deduplication identity;
- `kind`: `notification` or `interaction`;
- lifecycle `status`;
- `severity`: `info`, `success`, `warning`, or `error`;
- `title` and `body`;
- `created_at` and `updated_at`;
- optional `request_id`;
- producer `source` including `plugin`;
- `display`: an action-display payload;
- optional `resolution`;
- optional `dismissal`, `expiration`, `response`, and `timeout` according to
  kind and status;
- versioned `retention`;
- `model_visibility: hidden`.

## Authoritative state

Session notifications are stored under:

```text
Session.metadata.notifications.items
```

Application notifications are stored by the stable application owner. The
initial store may remain memory-backed for server-lifetime records, but it is
authoritative for notification lifecycle and dismissal while the record
exists.

The notification record and dismissal state have the same authoritative owner.

## Ordinary notification lifecycle

```text
pending
├── dismissed
├── resolved
└── expired
```

Dismissal, resolution, and expiration increment `revision` and retain the
terminal record for history.

## Interaction-compatible lifecycle

The record model accepts interaction states without normalizing them back to
ordinary notification values:

```text
pending_response
├── responded → resolved
├── suspended → responded → resolved
├── cancelled
└── expired
```

Active interactions are nondismissible.

## Operations and stale mutations

Session notifications support create, update by ID, update by key, resolve,
server-side dismiss, expire, and list/history. Application notifications
support equivalent owner-scoped operations plus an authoritative current-state
snapshot/list path.

Mutations may include `expected_revision`. A stale mutation returns the current
record rather than overwriting a later revision.

Creating with the key of an active notification updates that item while
retaining its ID. A matching terminal record does not suppress a new
occurrence.

## Retention and pruning

The extensible retention object initially supports:

- `until_resolved`;
- `ttl` with `expires_at`;
- `until_request_complete`;
- `until_server_restart`.

Active and terminal limits are separate. Terminal records are pruned by
history policy. Active interactions are never silently pruned. Unsupported
retention policies fail validation rather than receiving guessed semantics.

## Events

Application events:

- `application_notification_created`
- `application_notification_updated`

Session events:

- `session_notification_created`
- `session_notification_updated`
- `session_notification_resolved`
- proposed dismissal and expiration transitions, either as explicit lifecycle
  events or revisioned updates with equivalent observable meaning.

Application events omit `session_id`. Session events include it. Event
delivery is best effort. Events accelerate updates but are not authoritative.
Session metadata is the session reconnect authority; the application
notification snapshot is the application reconnect authority.

## Concurrency and persistence

Session notification read-modify-write operations use the application
session lock and save a new immutable `Session`. Notification metadata is
preserved by request checkpoint reconciliation.

The tool-facing notification sink catches failures and returns no notification
result rather than failing the tool or request. Application plugins calling
the application API directly receive validation errors.

## Dismissal consistency

The dismissing frontend updates immediately from the successful mutation
response. The server is not required to force immediate presentation removal
on other already-open frontends. Their state converges on reconnect, explicit
refresh, or normal authoritative reload.

A newly hydrated frontend filters terminal dismissed records from active
presentation.

## History and replay

History queries include active and terminal records subject to retention.
Historical replay is a local display operation and does not mutate lifecycle,
increment revision, or publish a notification lifecycle event.

Mutating historical actions are disabled unless explicitly declared valid and
validated against current lifecycle and revision.

## Compatibility

Consumers must ignore malformed records and unknown event types. Explicit
supported presentations take precedence over producer defaults. Unknown
presentation values are rejected or reported rather than silently presented
with unrelated semantics.

Existing records without `revision` may use `updated_at` as a compatibility
revision token during migration.