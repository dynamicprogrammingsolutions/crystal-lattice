# Stage 1 Backend Notification Substrate

Implement backend support for creating, updating, resolving, persisting, and publishing generic session notifications.

## Requirements checklist

- [ ] Add application-layer helper(s) to create/update/resolve session notifications.
- [ ] Persist notifications in `Session.metadata`.
- [ ] Publish notification lifecycle events.
- [ ] Expose a safe notification sink through application/tool context.
- [ ] Add focused Python unit/application tests.
- [ ] Ensure notification failures do not abort requests or tool execution.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On: `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`

## Proposed Backend API

Add internal application helpers similar to:

```python
create_session_notification(
    session_id: str,
    notification: dict,
    *,
    request_id: str | None = None,
) -> dict

update_session_notification(
    session_id: str,
    notification_id: str,
    patch: dict,
    *,
    request_id: str | None = None,
) -> dict

resolve_session_notification(
    session_id: str,
    notification_id: str,
    resolution: dict,
    *,
    request_id: str | None = None,
) -> dict
```

These helpers should:

- load and save the session safely
- update `session.metadata["notifications"]["items"]`
- preserve unrelated metadata
- publish a lifecycle event through `EventStore`
- return the normalized notification

## Context Integration

Tools already receive application context through `ApplicationContext.build_tool_context`, including:

- `app`
- `application`
- `session_id`
- `request_id`
- `base_config`
- `runtime_store`
- `tool_runtime`

Prefer exposing a small `notification_sink` or callable in the context instead of requiring tools to know the full application object API. For example:

```python
context["notification_sink"].create(notification)
context["notification_sink"].resolve(notification_id, resolution)
```

If the first implementation uses `application.create_session_notification(...)` directly, document it as an interim step and keep the call narrow.

## Event Publishing

When a notification is created/updated/resolved, publish:

```json
{
  "type": "session_notification_created",
  "session_id": "...",
  "request_id": "...",
  "notification": { "...": "..." }
}
```

The event should be compatible with the existing `/events` endpoint and event compaction rules.

## Tests

Add backend tests that assert:

- creating a notification persists metadata
- creating with an existing key updates instead of duplicating
- resolving a notification changes status and stores resolution
- events are published with the expected type and payload
- a notification helper failure path is contained and does not fail a request in a dummy tool scenario

Potential test locations:

- `core/python/tests/test_session_notifications.py`
- `application/python/tests/test_session_notifications_endpoints.py` if HTTP endpoints are added

Avoid MCP-specific names in platform tests.