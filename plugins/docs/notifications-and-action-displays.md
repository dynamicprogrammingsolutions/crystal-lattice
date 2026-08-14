# Notifications and action displays

Plugins can communicate user-facing information in three ways:

| Intent | Use |
|---|---|
| State that belongs to the running server/application | Application notification |
| State that belongs to one session and must survive reopening it | Session notification |
| The immediate result of the action being executed | Direct action display |

Tools can also create session notifications through the failure-contained
`notification_sink`.

This page describes the currently implemented plugin APIs, record lifecycle,
presentation behavior, actions, and failure boundaries.

Runtime references:

- `core/python/agent_app/notifications.py`
- `core/python/agent_app/application_owner.py`
- `core/python/agent_app/application_future.py`
- `core/python/agent_app/app_context.py`

Reference plugins:

- `plugins/dummy-application-notification-app`
- `plugins/dummy-session-notification-app`
- `plugins/dummy-action-display-app`

Python method examples below are intended for plugin classes and assume
`from typing import Any`.

## Notification or direct display?

Use a notification when the information has a lifecycle independent from the
action that created it. Examples include:

- configuration reload is waiting or failed;
- a session dependency is unavailable;
- a login or other recoverable condition needs attention;
- a tool discovers a warning that should remain associated with the session.

Use a direct display when the content is only the result of the current action:

```python
return {
    "status": "ok",
    "display": {
        "format": "markdown",
        "title": "Export complete",
        "body": "The file was created successfully.",
        "variant": "success",
        "presentation": "modal",
    },
}
```

A direct display is not stored as a notification and has no notification
create/update/resolve lifecycle.

## Notification record

Application and session notifications use the same basic record:

```python
notification = {
    "key": "example:dependency:unavailable",
    "severity": "warning",
    "title": "Dependency unavailable",
    "body": "The request continued without the optional dependency.",
    "source": {
        "plugin": "example_app",
        "subsystem": "dependency",
    },
    "display": {
        "format": "markdown",
        "title": "Dependency unavailable",
        "body": "The request continued without the optional dependency.",
        "variant": "warning",
        "presentation": "inline",
        "dismissible": True,
    },
    "model_visibility": "hidden",
}
```

The backend adds and maintains:

- `id`;
- `revision`;
- `kind: "notification"`;
- `status: "pending" | "dismissed" | "resolved" | "expired"`;
- `created_at` and `updated_at`;
- optional `request_id`;
- optional resolution details.

Required producer fields are:

- a non-empty stable `key`;
- `title`;
- `source.plugin`;
- a valid `display`.

`body` defaults to an empty string, `severity` defaults to `info`, and
`model_visibility` must currently be `hidden`.

## Application notifications

Application notifications belong to the stable application owner. They:

- survive replacement of `AgentApplication`;
- do not survive restart of the owner process;
- are not associated with a `session_id`;
- support `banner` and `modal`;
- reject `inline`.

Create an application notification from an application action:

```python
def execute_action(
    self,
    app: Any,
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any] | None,
    state: dict[str, Any],
) -> dict[str, Any]:
    stored = app.create_application_notification(
        {
            "key": "example:reload:status",
            "severity": "info",
            "title": "Reload requested",
            "body": "New work is paused while active work finishes.",
            "source": {"plugin": self.name},
            "display": {
                "format": "text",
                "title": "Reload requested",
                "body": "New work is paused while active work finishes.",
                "variant": "info",
                "presentation": "banner",
                "dismissible": True,
            },
            "model_visibility": "hidden",
        }
    )
    return {
        "status": "ok",
        "notification_id": stored["id"],
    }
```

Available application methods:

```python
app.create_application_notification(notification)
app.update_application_notification(
    notification_id,
    patch,
    expected_revision=revision,
)
app.dismiss_application_notification(
    notification_id,
    reason="user",
    expected_revision=revision,
)
app.resolve_application_notification(
    notification_id,
    resolution,
    expected_revision=revision,
)
app.expire_application_notification(
    notification_id,
    reason="expired",
    expected_revision=revision,
)
app.list_application_notifications(include_terminal=True)
```

## Session notifications

Session notifications are stored in:

```text
Session.metadata.notifications.items
```

They survive session reload, frontend reconnect, and server restart as part of
the session record. They remain hidden from model/provider history.

Create one from an application plugin:

```python
def execute_action(
    self,
    app: Any,
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any] | None,
    state: dict[str, Any],
) -> dict[str, Any]:
    session_id = str((context or {})["session_id"])
    stored = app.create_session_notification(
        session_id,
        {
            "key": "example:session:warning",
            "severity": "warning",
            "title": "Session warning",
            "body": "An optional session capability is unavailable.",
            "source": {"plugin": self.name},
            "display": {
                "format": "text",
                "title": "Session warning",
                "body": "An optional session capability is unavailable.",
                "variant": "warning",
                "presentation": "inline",
                "dismissible": True,
            },
            "model_visibility": "hidden",
        },
    )
    return {
        "status": "ok",
        "notification_id": stored["id"],
    }
```

Available session methods:

```python
app.create_session_notification(session_id, notification)
app.update_session_notification(
    session_id,
    notification_id,
    patch,
    expected_revision=revision,
)
app.update_session_notification_by_key(
    session_id,
    key,
    patch,
    expected_revision=revision,
)
app.dismiss_session_notification(
    session_id,
    notification_id,
    reason="user",
    expected_revision=revision,
)
app.resolve_session_notification(
    session_id,
    notification_id,
    resolution,
    expected_revision=revision,
)
app.expire_session_notification(
    session_id,
    notification_id,
    reason="expired",
    expected_revision=revision,
)
app.list_session_notifications(session_id)
app.list_session_notifications(session_id, include_terminal=True)
```

## Stable keys and updates

Creating a pending notification with the same `key` updates the existing
notification in place:

```python
app.create_session_notification(
    session_id,
    {
        "key": "example:session:warning",
        "severity": "error",
        "title": "Session dependency failed",
        "body": "The dependency is still unavailable.",
        "source": {"plugin": self.name},
        "display": {
            "format": "text",
            "title": "Session dependency failed",
            "body": "The dependency is still unavailable.",
            "variant": "error",
            "presentation": "banner",
            "dismissible": True,
        },
        "model_visibility": "hidden",
    },
)
```

The stored notification keeps its existing `id`, increments `revision`, and
receives a later `updated_at`. Creating with the key of a dismissed, resolved,
or expired record creates a new notification occurrence with a new ID. Use
separate keys when two active conditions must be represented independently.

## Revisions and conflicts

New notification records begin at revision `1`. Pass the revision shown to the
user back as `expected_revision` for update, dismiss, resolve, or expire
operations.

A stale revision raises `NotificationRevisionConflictError`. The exception
contains the current notification. HTTP dismissal routes return the same
condition as status 409.

Existing records created before integer revisions use their `updated_at` value
as the compatibility expected-revision token. Their first mutation assigns
integer revision `1`.

### Background-operation heartbeats

Background work can keep one pending notification and update it by revision:

```python
notification = app.create_session_notification(
    session_id,
    {
        "key": f"example:operation:{operation_id}",
        "severity": "info",
        "title": "Operation running",
        "body": "Waiting for the provider. Elapsed: 0 seconds.",
        "source": {"plugin": self.name},
        "display": {
            "format": "text",
            "title": "Operation running",
            "body": "Waiting for the provider. Elapsed: 0 seconds.",
            "variant": "info",
            "presentation": "inline",
            "dismissible": False,
        },
        "operation": {
            "version": 1,
            "type": "example_operation",
            "id": operation_id,
            "state": "running",
            "phase": "waiting_for_provider",
            "elapsed_seconds": 0,
            "cancellable": True,
        },
        "model_visibility": "hidden",
    },
)
```

Each heartbeat updates the visible body and structured `operation` field with
`expected_revision=notification["revision"]`. The structured `operation`
mapping is plugin-owned presentation data; its optional fields do not define
the application operation registration contract. The minimal active
registration used for admission and lookup remains separate. Notification
failure must not grant commit authority or cancel the underlying operation.

Use `display.dismissible: false` while Cancel is the intended user action.
After failure or interruption, update the display to `dismissible: true` and
provide Retry or Continue follow-ups as appropriate.

### Notification UI effects

Notifications may carry an optional `ui_effects` mapping using the
same refresh field names as application-action results:

```json
{
  "ui_effects": {
    "reload_session_ids": ["session-1"],
    "reload_sessions_list": true,
    "reload_application_actions": true
  }
}
```

The shared notification-safe effects are:

| Field | Meaning |
| --- | --- |
| `reload_session_ids` | Invalidate the listed sessions on the notification's connection and refresh any listed session that is currently mounted or open. This does not open or navigate to a session. |
| `reload_sessions_list` | Invalidate and refresh the session collection for the notification's connection. |
| `reload_application_actions` | Invalidate and refresh application-action definitions and related application UI schema for the notification's connection. |

These refresh effects are applicable to both notification scopes:

- a session notification applies them within the connection that owns its
  session;
- an application notification applies them within the connection on which it
  was received.

Effects never cross connection boundaries. A connection-level notification
may request `reload_session_ids`, but the frontend does not open those
sessions. It refreshes mounted consumers and invalidates cached data so a later
open observes current state.

Known fields are validated. Additional JSON-compatible `ui_effects` fields are
preserved and remain producer-owned. Frontends may implement recognized
optional fields and must ignore unknown fields.

`navigate_to_session_id` is deliberately not part of notification UI effects.
Navigation is focus-changing and is appropriate after a direct user action,
such as Fork, but not when an asynchronous notification revision arrives.
A notification follow-up may still run an action whose successful action
response navigates after the user explicitly selects it.

Notifications also do not carry action `mutations` and do not infer effects
from created, updated, or deleted session IDs. A notification producer must
request every desired refresh explicitly through `ui_effects`.

Delivery is revision-based:

- an effect is considered once per connection, notification ID, and revision;
- observing the same revision through a snapshot and event does not repeat it;
- `ui_effects` belongs to the revision that explicitly supplies it and is not
  inherited by later notification updates;
- dismissal, resolution, expiration, and other terminal revisions do not
  execute effects, including when reading legacy records that retained them;
- a newer pending revision may request another effect by explicitly supplying
  `ui_effects`;
- reconnecting or remounting may apply the latest persisted revision once so
  a stale client catches up;
- effect execution is best effort and does not change notification lifecycle,
  retry the producer, or affect operation commit authority.

Refresh delivery is durable for the lifetime of the frontend connection.
Session, session-list, and application-action invalidations remain pending
until a matching consumer successfully reloads authoritative data. Therefore:

- a mounted active consumer reloads immediately;
- an inactive consumer may defer the reload without losing it;
- a later-mounted consumer receives the pending invalidation;
- a failed reload leaves the invalidation pending for retry;
- successful reload acknowledgment prevents later remounts from replaying the
  same invalidation.

Action responses remain one-shot and are not revisioned. Their shared refresh
fields should use the same parsing and routing implementation as notification
refresh effects.

## Resolving a notification

Resolve a notification when the underlying condition is no longer active:

```python
app.resolve_session_notification(
    session_id,
    notification_id,
    {
        "action_id": "dependency_recovered",
        "values": {"dependency": "example"},
    },
)
```

Resolution sets `status: "resolved"`, records `resolved_at`, and publishes a
session notification resolved event.

Application notification resolution is equivalent:

```python
app.resolve_application_notification(
    notification_id,
    {"action_id": "reload_completed"},
)
```

## Dismissing and expiring

Dismissal is a terminal server-side lifecycle transition:

```python
dismissed = app.dismiss_session_notification(
    session_id,
    notification_id,
    reason="user",
    expected_revision=revision,
)
```

Expiration is also terminal:

```python
expired = app.expire_application_notification(
    notification_id,
    reason="manual_expiration",
    expected_revision=revision,
)
```

Dismiss, resolve, and expire are idempotent when the record is already in the
requested state. Transitioning from one terminal state to another raises
`NotificationTransitionError`.

## Tool notification sink

Tools receive a session- and request-bound notification sink:

```python
def execute_tool(
    self,
    tool_name: str,
    params: dict[str, Any],
    context: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    sink = context.get("notification_sink")
    if sink is not None:
        sink.create(
            {
                "key": "example:tool:warning",
                "severity": "warning",
                "title": "Tool warning",
                "body": "The tool used its fallback mode.",
                "source": {"plugin": self.name},
                "display": {
                    "format": "text",
                    "title": "Tool warning",
                    "body": "The tool used its fallback mode.",
                    "variant": "warning",
                    "presentation": "inline",
                    "dismissible": True,
                },
                "model_visibility": "hidden",
            }
        )

    return {"status": "ok"}
```

The sink catches notification errors and returns `None`, so notification
failure does not abort the tool or request. Application plugins call the
application methods directly and receive validation errors for malformed
records.

## Presentation

Supported presentations are:

| Producer | `banner` | `inline` | `modal` |
|---|---|---|---|
| Application notification | Mobile Sessions; desktop connection rail | Rejected | Mobile Sessions modal; desktop inline fallback |
| Session notification | Matching mobile Chat; active desktop ChatPane | Matching session region | Matching mobile Chat modal; desktop inline fallback |
| Direct action display | Owning action surface | Owning action surface | Mobile modal; desktop inline fallback |

Supported semantic variants are:

- `info`;
- `success`;
- `warning`;
- `error`.

Application notifications default to banner, session notifications default to
inline, and direct action displays default to modal when presentation is
omitted.

## Follow-up actions

Notification and direct displays can use:

- `run_action`;
- `open_url`;
- `copy_text`;
- `download_attachment_asset`;
- `dismiss`.

Example:

```python
"actions": [
    {
        "kind": "run_action",
        "id": "retry",
        "label": "Retry",
        "plugin": self.name,
        "action_id": "retry_dependency",
        "action_owner": "application",
        "fixed_params": {"source": "notification"},
    },
    {
        "kind": "copy_text",
        "id": "copy-details",
        "label": "Copy details",
        "text": "Dependency unavailable",
    },
]
```

Displays may also contain the common embedded form schema. A `run_action`
follow-up can map submitted fields through `$form.<field_name>`. See
[Plugin actions](actions.md#embedded-display-forms) for a complete form
example.

## Current frontend dismissal behavior

The backend and HTTP API support persistent dismissal. Mobile and desktop
notification Dismiss controls use those server operations for application and
session notifications. Direct action-display close remains frontend-local.

Plugins can already call the server-side dismiss methods. API clients can use:

```text
GET  /application/notifications
POST /application/notifications/{notification_id}/dismiss
GET  /sessions/{session_id}/notifications
POST /sessions/{session_id}/notifications/{notification_id}/dismiss
```

List routes return active notifications by default and accept
`include_terminal=true`.

The initiating mobile frontend stores an exact-revision dismissal cache entry
and hides the notification immediately. If the server request fails, that
revision stays hidden without a blocking error and the same expected-revision
request is retried when the record is observed after reconnect or
rehydration.

The cache never transfers dismissal to a newer revision. If the server returns
the same notification ID at a newer pending revision, mobile removes the
obsolete cache entry and presents the newer content. Direct action displays do
not enter this cache.

Another already-open frontend is not forced to remove a notification
immediately; a newly opened, reconnected, or authoritatively refreshed mobile
or desktop frontend does not present a server-dismissed record.

Desktop uses conservative success-only dismissal. It keeps the notification
visible if the server rejects or cannot complete the mutation, and therefore
does not currently use the mobile failed-dismissal cache.

Dismissal records a user presentation decision. Resolve the notification when
the underlying condition itself is complete.

## Events and reconnect

Application notification events:

- `application_notification_created`;
- `application_notification_updated`;
- `application_notification_dismissed`;
- `application_notification_expired`.

Session notification events:

- `session_notification_created`;
- `session_notification_updated`;
- `session_notification_resolved`;
- `session_notification_dismissed`;
- `session_notification_expired`.

Session metadata is authoritative when a session is reopened. Application
notifications are stored in the runtime's durable application notification
store and survive `AgentApplication` replacement and server-process restart.
Events remain best effort; the application snapshot/list endpoint is the
reconnect authority.

## Failure and security boundaries

- Notification event delivery is best effort.
- Tool sink failures never fail the surrounding request.
- Application-plugin calls report validation and missing-record errors.
- Do not put credentials, provider keys, auth headers, private callback
  payloads, or sensitive configuration in notification fields, displays,
  events, or action results.

## Testing

Use the non-production demonstration packages as examples:

- `plugins/dummy-application-notification-app`
- `plugins/dummy-session-notification-app`
- `plugins/dummy-action-display-app`

Run their focused tests:

```bash
pytest plugins/dummy-application-notification-app/tests -q
pytest plugins/dummy-session-notification-app/tests -q
pytest plugins/dummy-action-display-app/tests -q
```

These plugins are intentionally absent from the production default
configuration.

The application and session notification demos expose presentation, variant,
retention, TTL duration, and follow-up-button controls. Follow-up buttons may
be disabled, shown once, or shown as a group of three for stacked-notification
testing. Follow-up action responses preserve the originating presentation and
variant. Application notifications support follow-up actions normally; their
earlier absence was only a limitation of the demonstration plugin.

## Retention

Notifications accept a versioned retention object with `until_resolved`,
`ttl`, `until_request_complete`, or `until_server_restart` policy.

TTL uses an absolute `expires_at` timestamp. It is intentionally a frontend
presentation deadline: a notification already visible remains visible after
the deadline, while a newly opened or reconstructed frontend host does not
present it. TTL alone does not mutate status, increment revision, or publish
an expiration event.

Request-completion and server-lifetime policies have explicit server
boundaries and transition matching pending records to `expired`. Terminal
history is bounded by `application.notifications.history_limit`; active
records are never silently pruned.

Server lifetime refers to the hosting runtime or server process, not one
replaceable `AgentApplication` generation. An inner application reload may
reuse the same lifetime and therefore does not provide a portable expiration
signal.

Explicit dismissal and resolution always win. A resolved notification stays
resolved after its TTL deadline, request completion, or a later server
restart; automatic retention expiration only targets records still pending.

Notification history UI, historical replay, and interaction-compatible
records remain planned.