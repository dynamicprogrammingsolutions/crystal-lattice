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

The backend and HTTP API support persistent dismissal. Mobile notification
Dismiss controls use those server operations for application and session
notifications. Desktop notification Dismiss controls remain local until the
desktop integration stage.

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
frontend does not present a server-dismissed record.

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

## Planned lifecycle extension

Automated retention policies, notification history, historical replay,
desktop adoption of server dismissal, and interaction-compatible records
remain planned. The manual expire methods and terminal status already exist;
TTL, request-completion, and server-lifetime policy evaluation do not.