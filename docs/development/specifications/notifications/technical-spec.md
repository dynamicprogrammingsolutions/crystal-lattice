# Notification technical specification

Status: Implementing — Stage D complete; Stage E pending

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
- optional revision-scoped `ui_effects`;
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

## UI effects and frontend invalidation

The initial portable notification refresh fields are:

- `reload_session_ids`: unique non-empty session IDs;
- `reload_sessions_list`: boolean;
- `reload_application_actions`: boolean.

Known fields are validated. Unknown JSON-compatible fields are preserved for
forward compatibility and ignored by consumers that do not implement them.
`navigate_to_session_id` is rejected because asynchronous notification
delivery must not move user focus.

`ui_effects` is a command on the revision that explicitly supplies it, not
durable state inherited by every later revision. An update that omits the field
stores no effect on its new revision. Only `pending` revisions execute effects.
Consumers ignore effects retained on legacy dismissed, resolved, or expired
records.

Frontend observation is deduplicated by connection, notification scope,
notification ID, and revision. Snapshot and event delivery of the same
revision therefore request an effect once. A newer pending revision may
request the same effect again explicitly. Rehydrating from a latest persisted
pending revision may request it once for the reconstructed frontend host.

Refresh execution creates frontend-runtime invalidation state scoped to the
owning backend connection:

- session invalidation is keyed by session ID;
- session-list invalidation is keyed by connection;
- application-action invalidation is keyed by connection.

The invalidation remains pending until an appropriate consumer successfully
reloads authoritative state. An unavailable or inactive consumer may decline
the reload without clearing it. Failed reload leaves it pending. Successful
reload acknowledges only the matching invalidation revision.

One invalidation revision has at most one claimed reload per target at a time.
Rerender or resubscription while a reload is in flight does not start another
reload. A newer invalidation supersedes the pending target revision, and late
acknowledgment of an older revision cannot clear it.

Pending invalidation and in-flight claims are frontend runtime state, not
additional server notification state. The persisted pending notification
revision remains the reconnect source when a frontend runtime is reconstructed.

Application-action responses use the same refresh field meanings and parsing,
but remain one-shot results in their initiating action context. Their
navigation and mutation-derived policies remain action-only. Notification
effect execution is best effort and never changes notification lifecycle,
producer retry, or operation commit authority.

## Retention and pruning

The extensible retention object initially supports:

- `until_resolved`;
- `ttl` with `expires_at`;
- `until_request_complete`;
- `until_server_restart`.

TTL is a frontend fresh-presentation rule. It does not schedule a server
mutation or lifecycle event. A host that accepted the notification before the
deadline keeps it until an explicit terminal transition or host
reconstruction.

`until_server_restart` is stamped with the hosting runtime's owner epoch. An
`AgentApplication` generation replacement normally reuses that epoch and does
not itself end the retention lifetime. Hosts may choose a different runtime
boundary, so plugins must not use inner application reload as a portable
expiration signal.

Automatic request/server expiration applies only to records still `pending`.
Explicit dismissal or resolution is final and is never overwritten by a later
TTL, request-completion, or server-restart boundary.

Active records are not pruned. Terminal records are bounded independently by
`application.notifications.history_limit`; legacy `max_items` is accepted as
an alias. Active interactions are never silently pruned. Unsupported retention
policies fail validation rather than receiving guessed semantics.

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
Mobile and desktop call the server mutation routes and hydrate application
notifications from the owner snapshot. Mobile uses the Stage B-2
revision-scoped failed-dismissal cache, which does not change the meaning of
`expected_revision`. Desktop uses conservative success-only dismissal and
keeps a notification visible when its server mutation fails.