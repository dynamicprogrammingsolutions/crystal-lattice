from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, Iterator, Mapping, Protocol

from .notifications import (
    _normalize_notification,
    _require_expected_revision,
    _require_operation_match,
    _timestamp,
    _validate_transition,
    is_active_notification,
)


@dataclass(frozen=True)
class ApplicationNotificationMutation:
    notification: Dict[str, Any]
    event_type: str | None
    changed: bool


class ApplicationNotificationStore(Protocol):
    owner_epoch: str | None

    def create(
        self,
        notification: Dict[str, Any],
        *,
        request_id: str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        """Create or update the active record matching the notification key."""

    def update(
        self,
        notification_id: str,
        patch: Dict[str, Any],
        *,
        expected_revision: int | str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        """Update one application notification."""

    def resolve(
        self,
        notification_id: str,
        resolution: Dict[str, Any],
        *,
        expected_revision: int | str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        """Resolve one application notification."""

    def dismiss(
        self,
        notification_id: str,
        *,
        reason: str | None = None,
        expected_revision: int | str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        """Dismiss one application notification."""

    def expire(
        self,
        notification_id: str,
        *,
        reason: str = "expired",
        expected_revision: int | str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        """Expire one application notification."""

    def list(self, *, include_terminal: bool = True) -> list[Dict[str, Any]]:
        """List active records or active plus terminal history."""

    def recover_owner_lifetime(
        self,
        owner_epoch: str,
        *,
        history_limit: int = 500,
    ) -> list[ApplicationNotificationMutation]:
        """Expire pending records belonging to an earlier owner lifetime."""

    def expire_request(
        self,
        request_id: str,
        *,
        history_limit: int = 500,
    ) -> list[ApplicationNotificationMutation]:
        """Expire pending records belonging to a completed request."""

    def close(self) -> None:
        """Close resources owned by the store."""


class _BaseApplicationNotificationStore:
    def __init__(self, *, owner_epoch: str | None = None) -> None:
        self.owner_epoch = owner_epoch

    @contextmanager
    def _transaction(self, *, write: bool) -> Iterator[None]:
        raise NotImplementedError

    def _load_all_locked(self) -> list[Dict[str, Any]]:
        raise NotImplementedError

    def _get_locked(self, notification_id: str) -> Dict[str, Any] | None:
        raise NotImplementedError

    def _save_locked(self, notification: Dict[str, Any]) -> None:
        raise NotImplementedError

    def _delete_locked(self, notification_id: str) -> None:
        raise NotImplementedError

    @staticmethod
    def _normalized_history_limit(value: int) -> int:
        return (
            value
            if isinstance(value, int) and not isinstance(value, bool) and value > 0
            else 500
        )

    def _prune_history_locked(self, history_limit: int) -> None:
        terminal = [
            item for item in self._load_all_locked() if not is_active_notification(item)
        ]
        terminal.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
        for item in terminal[self._normalized_history_limit(history_limit) :]:
            notification_id = item.get("id")
            if isinstance(notification_id, str):
                self._delete_locked(notification_id)

    def create(
        self,
        notification: Dict[str, Any],
        *,
        request_id: str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        with self._transaction(write=True):
            key = notification.get("key") if isinstance(notification, dict) else None
            existing = next(
                (
                    item
                    for item in self._load_all_locked()
                    if item.get("key") == key and is_active_notification(item)
                ),
                None,
            )
            if existing is not None:
                _require_operation_match(existing, notification)
            stored = _normalize_notification(
                notification,
                existing=existing,
                request_id=request_id,
                owner_epoch=self.owner_epoch,
                allowed_presentations={"banner", "modal"},
            )
            self._save_locked(stored)
            self._prune_history_locked(history_limit)
            return ApplicationNotificationMutation(
                notification=stored,
                event_type=(
                    "application_notification_created"
                    if existing is None
                    else "application_notification_updated"
                ),
                changed=True,
            )

    def update(
        self,
        notification_id: str,
        patch: Dict[str, Any],
        *,
        expected_revision: int | str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        if not isinstance(patch, dict):
            raise ValueError("notification patch must be a mapping")
        with self._transaction(write=True):
            existing = self._require_locked(notification_id)
            _require_expected_revision(existing, expected_revision)
            target_status = patch.get("status", existing.get("status", "pending"))
            _validate_transition(existing, target_status)
            stored = _normalize_notification(
                patch,
                existing=existing,
                owner_epoch=self.owner_epoch,
                allowed_presentations={"banner", "modal"},
            )
            self._save_locked(stored)
            self._prune_history_locked(history_limit)
            return ApplicationNotificationMutation(
                notification=stored,
                event_type="application_notification_updated",
                changed=True,
            )

    def resolve(
        self,
        notification_id: str,
        resolution: Dict[str, Any],
        *,
        expected_revision: int | str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        if not isinstance(resolution, dict):
            raise ValueError("resolution must be a mapping")
        return self._transition(
            notification_id,
            target_status="resolved",
            patch={
                "resolution": {
                    **resolution,
                    "resolved_at": _timestamp(),
                }
            },
            expected_revision=expected_revision,
            event_type="application_notification_updated",
            history_limit=history_limit,
        )

    def dismiss(
        self,
        notification_id: str,
        *,
        reason: str | None = None,
        expected_revision: int | str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        return self._transition(
            notification_id,
            target_status="dismissed",
            patch={
                "dismissal": {
                    "dismissed_at": _timestamp(),
                    **(
                        {"reason": reason} if isinstance(reason, str) and reason else {}
                    ),
                }
            },
            expected_revision=expected_revision,
            event_type="application_notification_dismissed",
            history_limit=history_limit,
        )

    def expire(
        self,
        notification_id: str,
        *,
        reason: str = "expired",
        expected_revision: int | str | None = None,
        history_limit: int = 500,
    ) -> ApplicationNotificationMutation:
        return self._transition(
            notification_id,
            target_status="expired",
            patch={
                "expiration": {
                    "expired_at": _timestamp(),
                    "reason": reason,
                }
            },
            expected_revision=expected_revision,
            event_type="application_notification_expired",
            history_limit=history_limit,
        )

    def list(self, *, include_terminal: bool = True) -> list[Dict[str, Any]]:
        with self._transaction(write=False):
            notifications = self._load_all_locked()
            if include_terminal:
                return notifications
            return [item for item in notifications if is_active_notification(item)]

    def recover_owner_lifetime(
        self,
        owner_epoch: str,
        *,
        history_limit: int = 500,
    ) -> list[ApplicationNotificationMutation]:
        recovered: list[ApplicationNotificationMutation] = []
        self.owner_epoch = owner_epoch
        with self._transaction(write=True):
            for existing in self._load_all_locked():
                if not is_active_notification(existing):
                    continue
                retention = existing.get("retention")
                if not isinstance(retention, Mapping):
                    continue
                if retention.get("policy") != "until_server_restart":
                    continue
                if retention.get("owner_epoch") == owner_epoch:
                    continue
                stored = _normalize_notification(
                    {
                        "status": "expired",
                        "expiration": {
                            "expired_at": _timestamp(),
                            "reason": "owner_restarted",
                        },
                    },
                    existing=existing,
                    owner_epoch=owner_epoch,
                    allowed_presentations={"banner", "modal"},
                )
                self._save_locked(stored)
                recovered.append(
                    ApplicationNotificationMutation(
                        notification=stored,
                        event_type="application_notification_expired",
                        changed=True,
                    )
                )
            self._prune_history_locked(history_limit)
        return recovered

    def expire_request(
        self,
        request_id: str,
        *,
        history_limit: int = 500,
    ) -> list[ApplicationNotificationMutation]:
        expired: list[ApplicationNotificationMutation] = []
        with self._transaction(write=True):
            for existing in self._load_all_locked():
                retention = existing.get("retention")
                if (
                    not is_active_notification(existing)
                    or existing.get("request_id") != request_id
                    or not isinstance(retention, Mapping)
                    or retention.get("policy") != "until_request_complete"
                ):
                    continue
                stored = _normalize_notification(
                    {
                        "status": "expired",
                        "expiration": {
                            "expired_at": _timestamp(),
                            "reason": "request_completed",
                        },
                    },
                    existing=existing,
                    request_id=request_id,
                    owner_epoch=self.owner_epoch,
                    allowed_presentations={"banner", "modal"},
                )
                self._save_locked(stored)
                expired.append(
                    ApplicationNotificationMutation(
                        notification=stored,
                        event_type="application_notification_expired",
                        changed=True,
                    )
                )
            self._prune_history_locked(history_limit)
        return expired

    def _transition(
        self,
        notification_id: str,
        *,
        target_status: str,
        patch: Dict[str, Any],
        expected_revision: int | str | None,
        event_type: str,
        history_limit: int,
    ) -> ApplicationNotificationMutation:
        with self._transaction(write=True):
            existing = self._require_locked(notification_id)
            _require_expected_revision(existing, expected_revision)
            if existing.get("status") == target_status:
                return ApplicationNotificationMutation(
                    notification=existing,
                    event_type=None,
                    changed=False,
                )
            _validate_transition(existing, target_status)
            stored = _normalize_notification(
                {
                    "status": target_status,
                    **patch,
                },
                existing=existing,
                owner_epoch=self.owner_epoch,
                allowed_presentations={"banner", "modal"},
            )
            self._save_locked(stored)
            self._prune_history_locked(history_limit)
            return ApplicationNotificationMutation(
                notification=stored,
                event_type=event_type,
                changed=True,
            )

    def _require_locked(self, notification_id: str) -> Dict[str, Any]:
        existing = self._get_locked(notification_id)
        if existing is None:
            raise KeyError(f"Application notification {notification_id!r} not found")
        return existing


class InMemoryApplicationNotificationStore(_BaseApplicationNotificationStore):
    def __init__(self, *, owner_epoch: str | None = None) -> None:
        super().__init__(owner_epoch=owner_epoch)
        self._lock = threading.RLock()
        self._notifications: Dict[str, Dict[str, Any]] = {}

    @contextmanager
    def _transaction(self, *, write: bool) -> Iterator[None]:
        _ = write
        with self._lock:
            yield

    def _load_all_locked(self) -> list[Dict[str, Any]]:
        return list(self._notifications.values())

    def _get_locked(self, notification_id: str) -> Dict[str, Any] | None:
        return self._notifications.get(notification_id)

    def _save_locked(self, notification: Dict[str, Any]) -> None:
        self._notifications[notification["id"]] = notification

    def _delete_locked(self, notification_id: str) -> None:
        self._notifications.pop(notification_id, None)

    def close(self) -> None:
        return None


class SQLiteApplicationNotificationStore(_BaseApplicationNotificationStore):
    def __init__(
        self,
        path: str | Path,
        *,
        owner_epoch: str | None = None,
    ) -> None:
        super().__init__(owner_epoch=owner_epoch)
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            self.path,
            check_same_thread=False,
            isolation_level=None,
        )
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS application_notifications (
                id TEXT PRIMARY KEY,
                notification_key TEXT NOT NULL,
                status TEXT NOT NULL,
                revision INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                record_json TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
                application_notifications_status_updated_idx
            ON application_notifications(status, updated_at DESC)
            """
        )
        self._connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                application_notifications_active_key_idx
            ON application_notifications(notification_key)
            WHERE status = 'pending'
            """
        )
        self._closed = False

    @contextmanager
    def _transaction(self, *, write: bool) -> Iterator[None]:
        with self._lock:
            if self._closed:
                raise RuntimeError("Application notification store is closed")
            if not write:
                yield
                return
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                yield
            except Exception:
                self._connection.execute("ROLLBACK")
                raise
            else:
                self._connection.execute("COMMIT")

    def _load_all_locked(self) -> list[Dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT record_json
            FROM application_notifications
            ORDER BY created_at ASC, id ASC
            """
        ).fetchall()
        return [self._decode(row[0]) for row in rows]

    def _get_locked(self, notification_id: str) -> Dict[str, Any] | None:
        row = self._connection.execute(
            """
            SELECT record_json
            FROM application_notifications
            WHERE id = ?
            """,
            (notification_id,),
        ).fetchone()
        return None if row is None else self._decode(row[0])

    def _save_locked(self, notification: Dict[str, Any]) -> None:
        revision = notification.get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool):
            raise ValueError("application notification revision must be an integer")
        self._connection.execute(
            """
            INSERT INTO application_notifications (
                id,
                notification_key,
                status,
                revision,
                created_at,
                updated_at,
                record_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                notification_key = excluded.notification_key,
                status = excluded.status,
                revision = excluded.revision,
                created_at = excluded.created_at,
                updated_at = excluded.updated_at,
                record_json = excluded.record_json
            """,
            (
                notification["id"],
                notification["key"],
                notification["status"],
                revision,
                notification["created_at"],
                notification["updated_at"],
                json.dumps(
                    notification,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ),
            ),
        )

    def _delete_locked(self, notification_id: str) -> None:
        self._connection.execute(
            "DELETE FROM application_notifications WHERE id = ?",
            (notification_id,),
        )

    @staticmethod
    def _decode(value: str) -> Dict[str, Any]:
        decoded = json.loads(value)
        if not isinstance(decoded, dict):
            raise ValueError("Stored application notification must be a mapping")
        return decoded

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._connection.close()


def resolve_application_notification_store_path(
    config_path: str | Path,
    resolved_config: Mapping[str, Any],
) -> Path:
    config_file = Path(config_path).expanduser().resolve()
    default_path = config_file.parent / "application-notifications.sqlite3"
    application = resolved_config.get("application")
    if not isinstance(application, Mapping):
        return default_path
    notifications = application.get("notifications")
    if not isinstance(notifications, Mapping):
        return default_path
    store = notifications.get("store")
    if store is None:
        return default_path
    if not isinstance(store, Mapping):
        raise ValueError("application.notifications.store must be a mapping")
    store_type = store.get("type", "sqlite")
    if store_type != "sqlite":
        raise ValueError("application.notifications.store.type must be 'sqlite'")
    raw_path = store.get("path")
    if raw_path is None:
        return default_path
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(
            "application.notifications.store.path must be a non-empty string"
        )
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = config_file.parent / path
    return path.resolve()


__all__ = [
    "ApplicationNotificationMutation",
    "ApplicationNotificationStore",
    "InMemoryApplicationNotificationStore",
    "SQLiteApplicationNotificationStore",
    "resolve_application_notification_store_path",
]
