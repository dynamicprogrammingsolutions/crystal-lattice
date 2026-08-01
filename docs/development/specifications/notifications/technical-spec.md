# Notification technical specification

Status: Implementing — Stage B-2 complete; Stage C pending

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

Application notifications are stored through an
`ApplicationNotificationStore` created and closed by the owning runtime. The
same long-lived store is injected into every `AgentApplication` generation.
The production implementation is durable at an application-configured path,
while tests may use an in-memory implementation.

The durable store preserves active and terminal records across
`AgentApplication` replacement, owner reconstruction, and server-process
restart. Event delivery remains separate and best-effort.

The notification record and dismissal state have the same authoritative owner.
`AgentApplication` owns the public notification API and lifecycle event
publication. `ApplicationControl` coordinates reload only. The owner creates
reload notifications through the current `AgentApplication`.

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

Stage A exposes the frontend-facing subset through:

```text
GET  /application/notifications
POST /application/notifications/{notification_id}/dismiss
GET  /sessions/{session_id}/notifications
POST /sessions/{session_id}/notifications/{notification_id}/dismiss
```

List endpoints return active records by default and accept
`include_terminal=true`.

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
- `application_notification_dismissed`
- `application_notification_expired`

Session events:

- `session_notification_created`
- `session_notification_updated`
- `session_notification_resolved`
- `session_notification_dismissed`
- `session_notification_expired`

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

Application notification create/update/transition operations perform
stable-key selection, expected-revision comparison, revision increment, and
durable replacement in one store transaction. Lifecycle events are published
only after the durable mutation commits.

## Dismissal consistency

The dismissing frontend may persist a local cache entry and hide the selected
revision immediately before the server mutation completes. A retryable failure
does not restore that revision or require a blocking error.

A cache entry contains at least:

- owning connection;
- application/session scope and optional session ID;
- notification ID;
- exact dismissed revision;
- dismissal time.

When the same active notification ID and revision is observed again, the
frontend keeps it hidden and may resend the unchanged expected-revision
request. The frontend never replaces the cached expected revision with a newer
revision.

When a newer pending revision is authoritative, the older cached dismissal is
obsolete, is removed, and the newer revision is eligible for presentation.
Terminal or missing authoritative state also removes the cache entry.

The server is not required to force immediate presentation removal on other
already-open frontends. Their state converges on reconnect, explicit refresh,
or normal authoritative reload.

A newly hydrated frontend filters terminal dismissed records from active
presentation.

## History and replay

History queries include active and terminal records from durable application
storage or session metadata, subject to retention.
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

Stage A migrates such a record to integer revision `1` on its first mutation.
Mobile calls the server mutation routes and hydrates application notifications
from the owner snapshot. Desktop retains frontend-local dismissal until Stage
C. Mobile uses the Stage B-2 revision-scoped failed-dismissal cache, which does
not change the meaning of `expected_revision`.