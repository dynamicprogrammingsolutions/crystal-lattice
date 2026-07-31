# Stage 1 Backend Notification Substrate

Implement backend support for creating, updating, resolving, persisting, and publishing generic session notifications.

## Requirements checklist

- [x] Add `SessionNotifications` helper class in `core/python/agent_app/notifications.py`.
- [x] Add thin methods on `AgentApplication` that delegate to `SessionNotifications`.
- [x] Persist notifications in `Session.metadata["notifications"]["items"]`.
- [x] Publish notification lifecycle events via `app.publish_event` + `app.record_checkpoint`.
- [x] Expose a safe `notification_sink` through `ApplicationContext.build_tool_context`.
- [x] Use `app.acquire_session_lock` for the read-modify-write in each helper.
- [x] Add focused Python unit tests.
- [x] Ensure notification failures do not abort requests or tool execution.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On: `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`

Completed Via:
`tasks/20260729-staged-application-config-and-full-reload.md`

## Backend API

New module `core/python/agent_app/notifications.py`:

```python
class SessionNotifications:
    """Application-level helper for persistent session notifications."""

    def __init__(self, app: "AgentApplication") -> None:
        self._app = app

    def create(
        self,
        session_id: str,
        notification: dict,
        *,
        request_id: str | None = None,
    ) -> dict:
        """Create or update (by key) a notification. Returns the stored notification."""

    def update(
        self,
        session_id: str,
        notification_id: str,
        patch: dict,
        *,
        request_id: str | None = None,
    ) -> dict:
        """Update a notification by id. Raises KeyError if not found."""

    def update_by_key(
        self,
        session_id: str,
        key: str,
        patch: dict,
        *,
        request_id: str | None = None,
    ) -> dict:
        """Update a notification by stable key. Raises KeyError if not found."""

    def resolve(
        self,
        session_id: str,
        notification_id: str,
        resolution: dict,
        *,
        request_id: str | None = None,
    ) -> dict:
        """Mark a notification as resolved. Stores resolution, emits event."""

    def list(
        self,
        session_id: str,
        *,
        include_resolved: bool = False,
    ) -> list[dict]:
        """Return notifications for a session."""
```

Thin methods on `AgentApplication` delegate to this class so application plugins can call `app.create_session_notification(...)` directly (matches the `session_pinned_app` convention):

```python
class AgentApplication:
    def create_session_notification(self, session_id, notification, *, request_id=None) -> dict: ...
    def update_session_notification(self, session_id, notification_id, patch, *, request_id=None) -> dict: ...
    def update_session_notification_by_key(self, session_id, key, patch, *, request_id=None) -> dict: ...
    def resolve_session_notification(self, session_id, notification_id, resolution, *, request_id=None) -> dict: ...
    def list_session_notifications(self, session_id, *, include_resolved=False) -> list[dict]: ...
```

## Concurrency Pattern

Each helper follows the pattern from `plugins/session-pinned-app`:

```python
def create(self, session_id, notification, *, request_id=None):
    with self._app.acquire_session_lock(session_id):
        ctx = self._app.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        _core, _base, session = ctx
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        items = self._merge_or_append(metadata, notification)
        new_metadata = {**metadata, "notifications": {"items": items}}
        new_session = Session(
            session_id=session.session_id,
            messages=session.messages,
            metadata=new_metadata,
        )
        saved = self._app.save_session(new_session)
        self._app.publish_event({
            "type": "session_notification_created",
            "session_id": saved.session_id,
            "request_id": request_id,
            "notification": notification,
        })
        self._app.record_checkpoint(saved.session_id, request_id)
        return notification
```

The session lock serializes notification operations within a session. The existing `_merge_non_protected_session_metadata` reconciler preserves notification changes across concurrent request checkpoints because `notifications` is not a protected key.

## Context Integration

`ApplicationContext.build_tool_context` gains a `notification_sink` key. The sink is a small object bound to `(app, session_id, request_id)`:

```python
class NotificationSink:
    def __init__(self, app, session_id, request_id):
        self._app = app
        self._session_id = session_id
        self._request_id = request_id

    def create(self, notification: dict) -> dict | None:
        try:
            return self._app.create_session_notification(
                self._session_id, notification, request_id=self._request_id
            )
        except Exception:
            logger = get_logger("notification_sink")
            logger.exception("notification_create_failed")
            return None

    def update(self, notification_id: str, patch: dict) -> dict | None:
        try:
            return self._app.update_session_notification(
                self._session_id, notification_id, patch, request_id=self._request_id
            )
        except Exception:
            logger = get_logger("notification_sink")
            logger.exception("notification_update_failed")
            return None

    def resolve(self, notification_id: str, resolution: dict) -> dict | None:
        try:
            return self._app.resolve_session_notification(
                self._session_id, notification_id, resolution, request_id=self._request_id
            )
        except Exception:
            logger = get_logger("notification_sink")
            logger.exception("notification_resolve_failed")
            return None
```

Tools call `context["notification_sink"].create({...})` and never see exceptions. The `app` and `application` keys remain available for application plugins that call `AgentApplication` methods directly.

## Event Publishing

Events are published via `app.publish_event(...)` followed by `app.record_checkpoint(...)`. The event payload is compatible with the existing `GET /events` endpoint and event compaction rules. Notification events pass through `compact_events` unchanged.

## Pruning

The list is capped at `app_config.get("notifications", {}).get("max_items", 50)` most recent by `updated_at`. All pending notifications are kept; only resolved ones are pruned. Pruning runs inside `create`/`update`/`resolve` after the item is stored.

## Tests

Add `core/python/tests/test_session_notifications.py`:

- `test_create_notification_persists_metadata` — create → reload session → assert `metadata["notifications"]["items"]` contains the notification.
- `test_create_with_existing_key_updates_in_place` — create with key `k`, create again with key `k` → assert one item, updated fields.
- `test_update_notification_by_id` — create → update → assert fields changed.
- `test_update_notification_by_key` — create → update by key → assert fields changed.
- `test_resolve_notification_changes_status_and_stores_resolution` — create → resolve → assert `status == "resolved"`, `resolution` populated.
- `test_notification_events_published` — create/update/resolve → poll event store → assert `session_notification_created/updated/resolved` events with expected payload.
- `test_notification_sink_failure_contained` — dummy tool calls `notification_sink.create` with a malformed notification → sink returns `None`, tool execution completes, request succeeds.
- `test_notification_events_not_compacted` — publish notification events alongside `partial`/`final` events → assert notification events survive `compact_events`.
- `test_notification_list_pruning` — create 60 resolved notifications → assert only 50 most recent remain.

Avoid MCP-specific names in platform tests. Use generic names like `dummy:tool:warning`.

## Completion Notes

- Completed via
  `tasks/20260729-staged-application-config-and-full-reload.md`.
- Implemented persistent metadata operations, lifecycle events/checkpoints,
  pruning, session locking, and a failure-contained tool sink.
- Evidence includes the full core suite and public HTTP demo-plugin
  integration.