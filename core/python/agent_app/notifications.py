from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping
import uuid

from agent_core import Session
from agent_core.utils import get_logger


_SEVERITIES = {"info", "success", "warning", "error"}
_PRESENTATIONS = {"banner", "inline", "modal"}
_ACTIVE_NOTIFICATION_STATUSES = frozenset({"pending"})
_TERMINAL_NOTIFICATION_STATUSES = frozenset({"dismissed", "resolved", "expired"})
_NOTIFICATION_STATUSES = _ACTIVE_NOTIFICATION_STATUSES | _TERMINAL_NOTIFICATION_STATUSES
_RETENTION_POLICIES = frozenset(
    {"until_resolved", "ttl", "until_request_complete", "until_server_restart"}
)


class NotificationRevisionConflictError(RuntimeError):
    """Raised when a notification mutation targets a stale revision."""

    error_type = "notification_revision_conflict"

    def __init__(self, message: str, current: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.current = dict(current)


class NotificationTransitionError(RuntimeError):
    """Raised when a notification lifecycle transition is not valid."""

    error_type = "notification_transition_conflict"

    def __init__(self, message: str, current: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.current = dict(current)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty RFC3339 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def normalize_notification_retention(
    notification: Mapping[str, Any],
    *,
    existing: Mapping[str, Any] | None = None,
    request_id: str | None = None,
    owner_epoch: str | None = None,
) -> Dict[str, Any]:
    """Validate and normalize the versioned notification retention object."""

    retention_supplied = "retention" in notification
    raw = notification.get("retention")
    if raw is None and existing is not None:
        raw = existing.get("retention")
    if raw is None:
        raw = {"version": 1, "policy": "until_resolved"}
    if not isinstance(raw, Mapping):
        raise ValueError("notification.retention must be a mapping")

    version = raw.get("version", 1)
    if version != 1:
        raise ValueError("notification.retention.version must be 1")
    policy = raw.get("policy", "until_resolved")
    if policy not in _RETENTION_POLICIES:
        raise ValueError(
            "notification.retention.policy must be one of "
            f"{sorted(_RETENTION_POLICIES)}"
        )

    if policy == "until_resolved":
        return {"version": 1, "policy": policy}
    if policy == "ttl":
        expires_at = raw.get("expires_at")
        _parse_timestamp(expires_at, "notification.retention.expires_at")
        return {"version": 1, "policy": policy, "expires_at": expires_at}
    if policy == "until_request_complete":
        effective_request_id = request_id
        if effective_request_id is None:
            candidate = notification.get("request_id")
            if not isinstance(candidate, str) or not candidate:
                candidate = existing.get("request_id") if existing is not None else None
            effective_request_id = (
                candidate if isinstance(candidate, str) and candidate else None
            )
        if effective_request_id is None:
            raise ValueError(
                "until_request_complete retention requires an authoritative request_id"
            )
        return {"version": 1, "policy": policy}

    raw_owner_epoch = raw.get("owner_epoch")
    if owner_epoch is not None:
        if (
            retention_supplied
            and isinstance(raw_owner_epoch, str)
            and raw_owner_epoch
            and raw_owner_epoch != owner_epoch
        ):
            raise ValueError(
                "notification.retention.owner_epoch is owned by the runtime"
            )
        effective_owner_epoch = (
            raw_owner_epoch
            if not retention_supplied
            and isinstance(raw_owner_epoch, str)
            and raw_owner_epoch
            else owner_epoch
        )
    else:
        effective_owner_epoch = (
            raw_owner_epoch
            if isinstance(raw_owner_epoch, str) and raw_owner_epoch
            else None
        )
    if effective_owner_epoch is None:
        raise ValueError(
            "until_server_restart retention requires a runtime owner epoch"
        )
    return {
        "version": 1,
        "policy": policy,
        "owner_epoch": effective_owner_epoch,
    }


def notification_ttl_elapsed(
    notification: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a TTL notification is ineligible for fresh presentation."""

    retention = notification.get("retention")
    if not isinstance(retention, Mapping) or retention.get("policy") != "ttl":
        return False
    deadline = _parse_timestamp(
        retention.get("expires_at"),
        "notification.retention.expires_at",
    )
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("notification TTL comparison time must include a timezone")
    return current.astimezone(timezone.utc) >= deadline


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def notification_revision_token(notification: Mapping[str, Any]) -> int | str:
    """Return the current revision or the legacy timestamp compatibility token."""

    revision = notification.get("revision")
    if isinstance(revision, int) and not isinstance(revision, bool) and revision > 0:
        return revision
    updated_at = notification.get("updated_at")
    if isinstance(updated_at, str) and updated_at:
        return updated_at
    return 0


def is_active_notification(notification: Mapping[str, Any]) -> bool:
    return notification.get("status") in _ACTIVE_NOTIFICATION_STATUSES


def is_terminal_notification(notification: Mapping[str, Any]) -> bool:
    return notification.get("status") in _TERMINAL_NOTIFICATION_STATUSES


def _require_expected_revision(
    existing: Mapping[str, Any],
    expected_revision: int | str | None,
) -> None:
    if expected_revision is None:
        return
    current_revision = notification_revision_token(existing)
    if expected_revision != current_revision:
        raise NotificationRevisionConflictError(
            "Notification revision does not match the current record",
            existing,
        )


def _validate_transition(
    existing: Mapping[str, Any],
    target_status: str,
) -> None:
    current_status = existing.get("status")
    if current_status == target_status:
        return
    if current_status == "pending" and target_status in _TERMINAL_NOTIFICATION_STATUSES:
        return
    if current_status == "pending" and target_status == "pending":
        return
    raise NotificationTransitionError(
        f"Cannot transition notification from {current_status!r} to {target_status!r}",
        existing,
    )


def _normalize_notification(
    notification: Mapping[str, Any],
    *,
    existing: Mapping[str, Any] | None = None,
    request_id: str | None = None,
    owner_epoch: str | None = None,
    allowed_presentations: set[str] | None = None,
) -> Dict[str, Any]:
    if not isinstance(notification, Mapping):
        raise ValueError("notification must be a mapping")

    merged = {**(existing or {}), **notification}
    key = _require_text(merged.get("key"), "notification.key")
    title = _require_text(merged.get("title"), "notification.title")
    body = merged.get("body", "")
    if not isinstance(body, str):
        raise ValueError("notification.body must be a string")
    severity = merged.get("severity", "info")
    if severity not in _SEVERITIES:
        raise ValueError(f"notification.severity must be one of {sorted(_SEVERITIES)}")
    source = merged.get("source")
    if not isinstance(source, Mapping):
        raise ValueError("notification.source must be a mapping")
    _require_text(source.get("plugin"), "notification.source.plugin")
    display = merged.get("display")
    if not isinstance(display, Mapping):
        raise ValueError("notification.display must be a mapping")
    presentation = display.get("presentation", "inline")
    if presentation not in _PRESENTATIONS:
        raise ValueError(
            f"notification.display.presentation must be one of {sorted(_PRESENTATIONS)}"
        )
    if allowed_presentations is not None and presentation not in allowed_presentations:
        raise ValueError(
            "notification.display.presentation must be one of "
            f"{sorted(allowed_presentations)} for this notification scope"
        )
    model_visibility = merged.get("model_visibility", "hidden")
    if model_visibility != "hidden":
        raise ValueError("Stage 1 notifications require model_visibility='hidden'")
    kind = merged.get("kind", "notification")
    if kind != "notification":
        raise ValueError("Stage 1 notifications require kind='notification'")
    status = merged.get("status", "pending")
    if status not in _NOTIFICATION_STATUSES:
        raise ValueError(
            f"notification.status must be one of {sorted(_NOTIFICATION_STATUSES)}"
        )

    effective_request_id = (
        request_id if request_id is not None else merged.get("request_id")
    )
    retention = normalize_notification_retention(
        notification,
        existing=existing,
        request_id=(
            effective_request_id
            if isinstance(effective_request_id, str) and effective_request_id
            else None
        ),
        owner_epoch=owner_epoch,
    )
    now = _timestamp()
    notification_id = merged.get("id")
    if not isinstance(notification_id, str) or not notification_id:
        notification_id = f"notif_{uuid.uuid4().hex}"
    created_at = merged.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        created_at = now
    if existing is None:
        revision = 1
    else:
        current_revision = existing.get("revision")
        revision = (
            current_revision + 1
            if isinstance(current_revision, int)
            and not isinstance(current_revision, bool)
            and current_revision > 0
            else 1
        )

    return {
        **merged,
        "id": notification_id,
        "key": key,
        "kind": kind,
        "status": status,
        "revision": revision,
        "severity": severity,
        "title": title,
        "body": body,
        "created_at": created_at,
        "updated_at": now,
        "request_id": effective_request_id,
        "retention": retention,
        "source": dict(source),
        "display": {
            **display,
            "title": display.get("title", title),
            "body": display.get("body", body),
            "variant": display.get("variant", severity),
            "presentation": presentation,
        },
        "resolution": merged.get("resolution"),
        "dismissal": merged.get("dismissal"),
        "expiration": merged.get("expiration"),
        "model_visibility": "hidden",
    }


class SessionNotifications:
    """Persistent, evented session notification operations."""

    def __init__(self, app: Any) -> None:
        self._app = app

    def create(
        self,
        session_id: str,
        notification: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Dict[str, Any]:
        with self._app.acquire_session_lock(session_id):
            session = self._require_session(session_id)
            items = self._items(session)
            existing_index = next(
                (
                    index
                    for index, item in enumerate(items)
                    if item.get("key") == notification.get("key")
                    and is_active_notification(item)
                ),
                None,
            )
            if existing_index is None:
                stored = _normalize_notification(
                    notification,
                    request_id=request_id,
                    owner_epoch=self._app._notification_owner_epoch,
                )
                event_type = "session_notification_created"
                items = [*items, stored]
            else:
                stored = _normalize_notification(
                    notification,
                    existing=items[existing_index],
                    request_id=request_id,
                    owner_epoch=self._app._notification_owner_epoch,
                )
                items = [
                    stored if index == existing_index else item
                    for index, item in enumerate(items)
                ]
                event_type = "session_notification_updated"
            self._persist(session, items)
            self._publish(event_type, session_id, stored, request_id)
            return stored

    def update(
        self,
        session_id: str,
        notification_id: str,
        patch: Dict[str, Any],
        *,
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._update_matching(
            session_id,
            lambda item: item.get("id") == notification_id,
            patch,
            request_id=request_id,
            expected_revision=expected_revision,
            missing=f"Notification {notification_id!r} not found",
        )

    def update_by_key(
        self,
        session_id: str,
        key: str,
        patch: Dict[str, Any],
        *,
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._update_matching(
            session_id,
            lambda item: item.get("key") == key,
            patch,
            request_id=request_id,
            expected_revision=expected_revision,
            missing=f"Notification key {key!r} not found",
        )

    def resolve(
        self,
        session_id: str,
        notification_id: str,
        resolution: Dict[str, Any],
        *,
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(resolution, dict):
            raise ValueError("resolution must be a mapping")
        return self._transition_matching(
            session_id,
            lambda item: item.get("id") == notification_id,
            target_status="resolved",
            patch_factory=lambda: {
                "resolution": {**resolution, "resolved_at": _timestamp()},
            },
            request_id=request_id,
            expected_revision=expected_revision,
            missing=f"Notification {notification_id!r} not found",
            event_type="session_notification_resolved",
        )

    def dismiss(
        self,
        session_id: str,
        notification_id: str,
        *,
        reason: str | None = None,
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._transition_matching(
            session_id,
            lambda item: item.get("id") == notification_id,
            target_status="dismissed",
            patch_factory=lambda: {
                "dismissal": {
                    "dismissed_at": _timestamp(),
                    **(
                        {"reason": reason} if isinstance(reason, str) and reason else {}
                    ),
                },
            },
            request_id=request_id,
            expected_revision=expected_revision,
            missing=f"Notification {notification_id!r} not found",
            event_type="session_notification_dismissed",
        )

    def expire(
        self,
        session_id: str,
        notification_id: str,
        *,
        reason: str = "expired",
        request_id: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any]:
        return self._transition_matching(
            session_id,
            lambda item: item.get("id") == notification_id,
            target_status="expired",
            patch_factory=lambda: {
                "expiration": {
                    "expired_at": _timestamp(),
                    "reason": reason,
                },
            },
            request_id=request_id,
            expected_revision=expected_revision,
            missing=f"Notification {notification_id!r} not found",
            event_type="session_notification_expired",
        )

    def expire_request(
        self,
        session_id: str,
        request_id: str,
    ) -> list[Dict[str, Any]]:
        return self._expire_many(
            session_id,
            lambda item: (
                item.get("request_id") == request_id
                and isinstance(item.get("retention"), Mapping)
                and item["retention"].get("policy") == "until_request_complete"
            ),
            reason="request_completed",
            request_id=request_id,
        )

    def recover_owner_lifetime(
        self,
        session_id: str,
    ) -> list[Dict[str, Any]]:
        owner_epoch = self._app._notification_owner_epoch
        return self._expire_many(
            session_id,
            lambda item: (
                isinstance(item.get("retention"), Mapping)
                and item["retention"].get("policy") == "until_server_restart"
                and item["retention"].get("owner_epoch") != owner_epoch
            ),
            reason="owner_restarted",
            request_id=None,
        )

    def list(
        self,
        session_id: str,
        *,
        include_resolved: bool = False,
        include_terminal: bool | None = None,
    ) -> list[Dict[str, Any]]:
        self.recover_owner_lifetime(session_id)
        with self._app.acquire_session_lock(session_id):
            session = self._require_session(session_id)
            items = self._items(session)
            if include_terminal if include_terminal is not None else include_resolved:
                return items
            return [item for item in items if is_active_notification(item)]

    def _expire_many(
        self,
        session_id: str,
        predicate: Any,
        *,
        reason: str,
        request_id: str | None,
    ) -> list[Dict[str, Any]]:
        with self._app.acquire_session_lock(session_id):
            session = self._require_session(session_id)
            items = self._items(session)
            expired: list[Dict[str, Any]] = []
            next_items: list[Dict[str, Any]] = []
            for item in items:
                if not is_active_notification(item) or not predicate(item):
                    next_items.append(item)
                    continue
                stored = _normalize_notification(
                    {
                        "status": "expired",
                        "expiration": {
                            "expired_at": _timestamp(),
                            "reason": reason,
                        },
                    },
                    existing=item,
                    request_id=request_id,
                    owner_epoch=self._app._notification_owner_epoch,
                )
                expired.append(stored)
                next_items.append(stored)
            if not expired:
                return []
            self._persist(session, next_items)
            for stored in expired:
                self._publish(
                    "session_notification_expired",
                    session_id,
                    stored,
                    request_id,
                )
            return expired

    def _update_matching(
        self,
        session_id: str,
        predicate: Any,
        patch: Dict[str, Any],
        *,
        request_id: str | None,
        expected_revision: int | str | None,
        missing: str,
        event_type: str = "session_notification_updated",
    ) -> Dict[str, Any]:
        if not isinstance(patch, dict):
            raise ValueError("notification patch must be a mapping")
        with self._app.acquire_session_lock(session_id):
            session = self._require_session(session_id)
            items = self._items(session)
            index = next(
                (index for index, item in enumerate(items) if predicate(item)),
                None,
            )
            if index is None:
                raise KeyError(missing)
            _require_expected_revision(items[index], expected_revision)
            target_status = patch.get("status", items[index].get("status", "pending"))
            _validate_transition(items[index], target_status)
            stored = _normalize_notification(
                patch,
                existing=items[index],
                request_id=request_id,
                owner_epoch=self._app._notification_owner_epoch,
            )
            items = [
                stored if current_index == index else item
                for current_index, item in enumerate(items)
            ]
            self._persist(session, items)
            self._publish(event_type, session_id, stored, request_id)
            return stored

    def _transition_matching(
        self,
        session_id: str,
        predicate: Any,
        *,
        target_status: str,
        patch_factory: Any,
        request_id: str | None,
        expected_revision: int | str | None,
        missing: str,
        event_type: str,
    ) -> Dict[str, Any]:
        with self._app.acquire_session_lock(session_id):
            session = self._require_session(session_id)
            items = self._items(session)
            index = next(
                (index for index, item in enumerate(items) if predicate(item)),
                None,
            )
            if index is None:
                raise KeyError(missing)
            existing = items[index]
            _require_expected_revision(existing, expected_revision)
            if existing.get("status") == target_status:
                return existing
            _validate_transition(existing, target_status)
            stored = _normalize_notification(
                {
                    "status": target_status,
                    **patch_factory(),
                },
                existing=existing,
                request_id=request_id,
                owner_epoch=self._app._notification_owner_epoch,
            )
            items = [
                stored if current_index == index else item
                for current_index, item in enumerate(items)
            ]
            self._persist(session, items)
            self._publish(event_type, session_id, stored, request_id)
            return stored

    def _require_session(self, session_id: str) -> Session:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        session = self._app.load_live_session_record(session_id)
        if session is None:
            raise KeyError(f"Session {session_id!r} not found")
        return session

    @staticmethod
    def _items(session: Session) -> list[Dict[str, Any]]:
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        container = metadata.get("notifications")
        raw_items = container.get("items") if isinstance(container, dict) else []
        if not isinstance(raw_items, list):
            return []
        return [item for item in raw_items if isinstance(item, dict)]

    def _history_limit(self) -> int:
        application = self._app.get_application_config()
        notifications = (
            application.get("notifications") if isinstance(application, dict) else None
        )
        if not isinstance(notifications, dict):
            return 500
        value = notifications.get(
            "history_limit",
            notifications.get("max_items", 500),
        )
        return value if isinstance(value, int) and value > 0 else 500

    def _prune(self, items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        active = [item for item in items if is_active_notification(item)]
        terminal = [item for item in items if not is_active_notification(item)]
        terminal.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
        kept_ids = {
            item.get("id") for item in [*active, *terminal[: self._history_limit()]]
        }
        return [item for item in items if item.get("id") in kept_ids]

    def _persist(self, session: Session, items: list[Dict[str, Any]]) -> Session:
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        container = metadata.get("notifications")
        notification_metadata = container if isinstance(container, dict) else {}
        updated = Session(
            session_id=session.session_id,
            messages=session.messages,
            metadata={
                **metadata,
                "notifications": {
                    **notification_metadata,
                    "items": self._prune(items),
                },
            },
        )
        return self._app.save_session(updated, acquire_lock=False)

    def _publish(
        self,
        event_type: str,
        session_id: str,
        notification: Dict[str, Any],
        request_id: str | None,
    ) -> None:
        self._app.publish_event(
            {
                "type": event_type,
                "session_id": session_id,
                "request_id": request_id,
                "notification": notification,
            }
        )
        self._app.record_checkpoint(session_id, request_id)


class NotificationSink:
    """Failure-contained tool-facing session notification helper."""

    def __init__(self, app: Any, session_id: str, request_id: str) -> None:
        self._app = app
        self._session_id = session_id
        self._request_id = request_id
        self._logger = get_logger("notification_sink")

    def create(self, notification: Dict[str, Any]) -> Dict[str, Any] | None:
        return self._safe(
            "notification_create_failed",
            self._app.create_session_notification,
            self._session_id,
            notification,
            request_id=self._request_id,
        )

    def update(
        self, notification_id: str, patch: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        return self._safe(
            "notification_update_failed",
            self._app.update_session_notification,
            self._session_id,
            notification_id,
            patch,
            request_id=self._request_id,
        )

    def resolve(
        self, notification_id: str, resolution: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        return self._safe(
            "notification_resolve_failed",
            self._app.resolve_session_notification,
            self._session_id,
            notification_id,
            resolution,
            request_id=self._request_id,
        )

    def dismiss(
        self,
        notification_id: str,
        *,
        reason: str | None = None,
        expected_revision: int | str | None = None,
    ) -> Dict[str, Any] | None:
        return self._safe(
            "notification_dismiss_failed",
            self._app.dismiss_session_notification,
            self._session_id,
            notification_id,
            reason=reason,
            expected_revision=expected_revision,
            request_id=self._request_id,
        )

    def _safe(self, event: str, callback: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return callback(*args, **kwargs)
        except Exception as exc:
            self._logger.warning(event, error=str(exc))
            return None


__all__ = [
    "NotificationRevisionConflictError",
    "NotificationSink",
    "NotificationTransitionError",
    "SessionNotifications",
    "is_active_notification",
    "is_terminal_notification",
    "notification_revision_token",
]
