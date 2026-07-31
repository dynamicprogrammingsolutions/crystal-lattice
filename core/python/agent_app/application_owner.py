from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import threading
from typing import Any, Callable, Dict, Protocol
import uuid

from .events import EventStore


class ApplicationReloadPendingError(RuntimeError):
    """Raised when a new operation is admitted while reload is pending."""

    error_type = "application_reload_pending"


class ApplicationControl(Protocol):
    def request_reload(
        self,
        *,
        reason: str,
        on_failure: Callable[[], None] | None = None,
    ) -> Dict[str, Any]:
        """Register a full application reload and return its accepted result."""


@dataclass
class _ReloadRequest:
    reload_id: str
    reason: str
    notification: Dict[str, Any]
    on_failure: Callable[[], None] | None


class ApplicationOperation:
    """A retained application reference counted by its owning coordinator."""

    def __init__(self, owner: "AgentApplicationOwner", application: Any) -> None:
        self._owner = owner
        self.application = application
        self._released = False

    def __enter__(self) -> Any:
        return self.application

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.release()

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        self._owner._release_operation()


class AgentApplicationOwner(ApplicationControl):
    """Own one replaceable AgentApplication and coordinate quiescent reload."""

    def __init__(
        self,
        factory: Callable[[ApplicationControl], Any],
        *,
        event_store: EventStore,
    ) -> None:
        self._factory = factory
        self._event_store = event_store
        self._condition = threading.Condition(threading.RLock())
        self._application: Any = None
        self._active_operations = 0
        self._reload: _ReloadRequest | None = None
        self._reload_threads: Dict[str, threading.Thread] = {}
        self._replacement_listeners: list[Callable[[Any], None]] = []
        self._closed = False
        self._application = self._factory(self)

    @property
    def current(self) -> Any:
        with self._condition:
            if self._closed:
                raise RuntimeError("Application owner is closed")
            return self._application

    @property
    def reload_pending(self) -> bool:
        with self._condition:
            return self._reload is not None

    def add_replacement_listener(self, listener: Callable[[Any], None]) -> None:
        with self._condition:
            self._replacement_listeners.append(listener)

    def acquire_operation(self) -> ApplicationOperation:
        with self._condition:
            if self._closed:
                raise RuntimeError("Application owner is closed")
            if self._reload is not None:
                raise ApplicationReloadPendingError(
                    "Application reload is pending; try again after it completes"
                )
            application = self._application
            self._active_operations += 1
        return ApplicationOperation(self, application)

    def retain_operation(self, application: Any) -> ApplicationOperation:
        """Retain an application already admitted by an outer operation."""

        with self._condition:
            if self._closed:
                raise RuntimeError("Application owner is closed")
            self._active_operations += 1
        return ApplicationOperation(self, application)

    def request_reload(
        self,
        *,
        reason: str,
        on_failure: Callable[[], None] | None = None,
    ) -> Dict[str, Any]:
        normalized_reason = str(reason or "application_action")
        with self._condition:
            if self._closed:
                raise RuntimeError("Application owner is closed")
            if self._reload is not None:
                raise ApplicationReloadPendingError(
                    "Application reload is already pending"
                )
            reload_id = f"reload_{uuid.uuid4().hex}"
            notification = self._new_notification(
                reload_id,
                status="pending",
                severity="info",
                title="Application reload requested",
                body="Current work will finish before the application reloads.",
            )
            request = _ReloadRequest(
                reload_id=reload_id,
                reason=normalized_reason,
                notification=notification,
                on_failure=on_failure,
            )
            self._reload = request
            worker = threading.Thread(
                target=self._run_reload,
                args=(request,),
                name=f"application-reload-{reload_id}",
                daemon=True,
            )
            self._reload_threads[reload_id] = worker

        self._publish_control_event(
            "application_reload_requested",
            request,
            notification=notification,
        )
        self._publish_notification("application_notification_created", notification)
        worker.start()
        return {
            "status": "ok",
            "reload_status": "accepted",
            "reload_id": reload_id,
            "message": "Application reload requested.",
            "display": notification["display"],
        }

    def wait_for_reload(
        self,
        reload_id: str,
        *,
        timeout: float | None = None,
    ) -> bool:
        with self._condition:
            worker = self._reload_threads.get(reload_id)
        if worker is None:
            return True
        worker.join(timeout=timeout)
        return not worker.is_alive()

    def list_notifications(self) -> list[Dict[str, Any]]:
        with self._condition:
            request = self._reload
            if request is None:
                return []
            return [request.notification]

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            application = self._application
            self._condition.notify_all()
        if application is not None:
            application.close()

    def _release_operation(self) -> None:
        with self._condition:
            if self._active_operations > 0:
                self._active_operations -= 1
            self._condition.notify_all()

    def _run_reload(self, request: _ReloadRequest) -> None:
        candidate: Any = None
        old_application: Any = None
        listeners: list[Callable[[Any], None]] = []
        swapped = False
        try:
            with self._condition:
                while self._active_operations > 0 and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return

            self._publish_control_event("application_reload_ready", request)
            candidate = self._factory(self)

            with self._condition:
                if self._closed:
                    candidate.close()
                    return
                old_application = self._application
                listeners = list(self._replacement_listeners)
                self._application = candidate
                swapped = True

            for listener in listeners:
                listener(candidate)

            old_application.close()
            completed = self._updated_notification(
                request.notification,
                status="resolved",
                severity="success",
                title="Application reload completed",
                body="The replacement application is active.",
            )
            request.notification = completed
            with self._condition:
                self._reload = None
                self._condition.notify_all()
            self._publish_control_event(
                "application_reload_completed",
                request,
                notification=completed,
            )
            self._publish_notification("application_notification_updated", completed)
        except Exception as exc:
            if swapped and old_application is not None:
                with self._condition:
                    if self._application is candidate:
                        self._application = old_application
                for listener in listeners:
                    try:
                        listener(old_application)
                    except Exception:
                        pass
            if candidate is not None:
                try:
                    candidate.close()
                except Exception:
                    pass
            rollback_error: str | None = None
            if request.on_failure is not None:
                try:
                    request.on_failure()
                except Exception as rollback_exc:
                    rollback_error = str(rollback_exc) or type(rollback_exc).__name__
            detail = str(exc) or type(exc).__name__
            if rollback_error:
                detail = f"{detail}; rollback failed: {rollback_error}"
            failed = self._updated_notification(
                request.notification,
                status="resolved",
                severity="error",
                title="Application reload failed",
                body=detail,
            )
            request.notification = failed
            with self._condition:
                self._reload = None
                self._condition.notify_all()
            self._publish_control_event(
                "application_reload_failed",
                request,
                notification=failed,
                detail=detail,
            )
            self._publish_notification("application_notification_updated", failed)
        finally:
            with self._condition:
                self._reload_threads.pop(request.reload_id, None)

    def _publish_control_event(
        self,
        event_type: str,
        request: _ReloadRequest,
        **extra: Any,
    ) -> None:
        self._safe_publish(
            {
                "type": event_type,
                "reload_id": request.reload_id,
                "reason": request.reason,
                **extra,
            }
        )

    def _publish_notification(
        self,
        event_type: str,
        notification: Dict[str, Any],
    ) -> None:
        self._safe_publish(
            {
                "type": event_type,
                "notification": notification,
            }
        )

    def _safe_publish(self, event: Dict[str, Any]) -> None:
        try:
            self._event_store.publish(event)
        except Exception:
            # Reload must not fail because user-facing notification delivery did.
            return

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @classmethod
    def _new_notification(
        cls,
        reload_id: str,
        *,
        status: str,
        severity: str,
        title: str,
        body: str,
    ) -> Dict[str, Any]:
        timestamp = cls._timestamp()
        return {
            "id": f"notification_{reload_id}",
            "key": "application:reload",
            "kind": "notification",
            "status": status,
            "severity": severity,
            "title": title,
            "body": body,
            "created_at": timestamp,
            "updated_at": timestamp,
            "source": {"plugin": "application_owner", "subsystem": "reload"},
            "display": {
                "format": "text",
                "title": title,
                "body": body,
                "variant": severity,
                "presentation": "inline",
                "dismissible": True,
            },
            "model_visibility": "hidden",
        }

    @classmethod
    def _updated_notification(
        cls,
        notification: Dict[str, Any],
        *,
        status: str,
        severity: str,
        title: str,
        body: str,
    ) -> Dict[str, Any]:
        return {
            **notification,
            "status": status,
            "severity": severity,
            "title": title,
            "body": body,
            "updated_at": cls._timestamp(),
            "display": {
                **notification.get("display", {}),
                "title": title,
                "body": body,
                "variant": severity,
            },
        }


__all__ = [
    "AgentApplicationOwner",
    "ApplicationControl",
    "ApplicationOperation",
    "ApplicationReloadPendingError",
]
