from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any, Callable, Protocol, Sequence


APPLICATION_OPERATION_SERVICE_RUNTIME_KEY = "agent_app.application_operations"


class RuntimeStoreWithGetOrCreate(Protocol):
    def get_or_create(self, key: str, factory: Callable[[], Any]) -> Any:
        """Return the value for ``key``, creating it atomically when absent."""


@dataclass(frozen=True)
class ApplicationOperationRegistration:
    """Minimal identity for one active application operation."""

    operation_id: str
    owner_id: str
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "owner_id": self.owner_id,
            "session_id": self.session_id,
        }


class ApplicationOperationBusyError(RuntimeError):
    def __init__(
        self,
        exclusivity_key: str,
        current: ApplicationOperationRegistration,
    ) -> None:
        super().__init__(
            f"Application operation exclusivity key {exclusivity_key!r} "
            f"is owned by {current.operation_id!r}"
        )
        self.exclusivity_key = exclusivity_key
        self.current = current


class ApplicationOperationClosedError(RuntimeError):
    pass


class ApplicationOperationLeaseReleasedError(RuntimeError):
    pass


def session_operation_exclusivity_key(session_id: str) -> str:
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("session_id must be a non-empty string")
    return f"session:{session_id}"


@dataclass
class _OperationEntry:
    registration: ApplicationOperationRegistration
    lease_token: object
    exclusivity_keys: tuple[str, ...]


class ApplicationOperationLease:
    def __init__(
        self,
        service: "ApplicationOperationService",
        operation_id: str,
        lease_token: object,
    ) -> None:
        self._service = service
        self.operation_id = operation_id
        self._lease_token = lease_token
        self._lock = threading.Lock()
        self._released = False

    def registration(self) -> ApplicationOperationRegistration:
        with self._lock:
            if self._released:
                raise ApplicationOperationLeaseReleasedError(
                    f"Application operation lease {self.operation_id!r} is released"
                )
            return self._service._registration(
                self.operation_id,
                self._lease_token,
            )

    def release(self) -> bool:
        with self._lock:
            if self._released:
                return False
            removed = self._service._release(
                self.operation_id,
                self._lease_token,
            )
            self._released = True
            return removed


class ApplicationOperationService:
    """Active operation registration, lookup, and exclusivity."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: dict[str, _OperationEntry] = {}
        self._exclusive: dict[str, str] = {}
        self._closed = False

    def reserve(
        self,
        *,
        operation_id: str,
        owner_id: str,
        session_id: str | None = None,
        exclusivity_keys: Sequence[str] = (),
    ) -> ApplicationOperationLease:
        self._validate_text(operation_id, "operation_id")
        self._validate_text(owner_id, "owner_id")
        if session_id is not None:
            self._validate_text(session_id, "session_id")
        normalized_keys = tuple(exclusivity_keys)
        if len(set(normalized_keys)) != len(normalized_keys):
            raise ValueError("exclusivity_keys must not contain duplicates")
        for key in normalized_keys:
            self._validate_text(key, "exclusivity_key")

        registration = ApplicationOperationRegistration(
            operation_id=operation_id,
            owner_id=owner_id,
            session_id=session_id,
        )
        lease_token = object()

        with self._lock:
            if self._closed:
                raise ApplicationOperationClosedError(
                    "Application operation service is closed"
                )
            if operation_id in self._entries:
                raise ValueError(
                    f"Application operation {operation_id!r} already exists"
                )
            for key in normalized_keys:
                current_id = self._exclusive.get(key)
                if current_id is not None:
                    current = self._entries[current_id].registration
                    raise ApplicationOperationBusyError(key, current)
            entry = _OperationEntry(
                registration=registration,
                lease_token=lease_token,
                exclusivity_keys=normalized_keys,
            )
            self._entries[operation_id] = entry
            for key in normalized_keys:
                self._exclusive[key] = operation_id

        return ApplicationOperationLease(self, operation_id, lease_token)

    def get(self, operation_id: str) -> ApplicationOperationRegistration | None:
        self._validate_text(operation_id, "operation_id")
        with self._lock:
            entry = self._entries.get(operation_id)
            return entry.registration if entry is not None else None

    def get_by_exclusivity_key(
        self,
        exclusivity_key: str,
    ) -> ApplicationOperationRegistration | None:
        self._validate_text(exclusivity_key, "exclusivity_key")
        with self._lock:
            operation_id = self._exclusive.get(exclusivity_key)
            if operation_id is None:
                return None
            entry = self._entries.get(operation_id)
            return entry.registration if entry is not None else None

    def list_active(
        self,
        *,
        session_id: str | None = None,
        owner_id: str | None = None,
    ) -> list[ApplicationOperationRegistration]:
        if session_id is not None:
            self._validate_text(session_id, "session_id")
        if owner_id is not None:
            self._validate_text(owner_id, "owner_id")
        with self._lock:
            registrations = [
                entry.registration
                for entry in self._entries.values()
                if (session_id is None or entry.registration.session_id == session_id)
                and (owner_id is None or entry.registration.owner_id == owner_id)
            ]
        return sorted(registrations, key=lambda item: item.operation_id)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._entries.clear()
            self._exclusive.clear()

    def _registration(
        self,
        operation_id: str,
        lease_token: object,
    ) -> ApplicationOperationRegistration:
        with self._lock:
            return self._require_entry(operation_id, lease_token).registration

    def _release(self, operation_id: str, lease_token: object) -> bool:
        with self._lock:
            entry = self._entries.get(operation_id)
            if entry is None or entry.lease_token is not lease_token:
                return False
            self._entries.pop(operation_id, None)
            for key in entry.exclusivity_keys:
                if self._exclusive.get(key) == operation_id:
                    self._exclusive.pop(key, None)
            return True

    def _require_entry(self, operation_id: str, lease_token: object) -> _OperationEntry:
        entry = self._entries.get(operation_id)
        if entry is None or entry.lease_token is not lease_token:
            raise ApplicationOperationLeaseReleasedError(
                f"Application operation lease {operation_id!r} is no longer current"
            )
        return entry

    @staticmethod
    def _validate_text(value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} must be a non-empty string")


def get_application_operation_service(
    runtime_store: RuntimeStoreWithGetOrCreate,
) -> ApplicationOperationService:
    get_or_create = getattr(runtime_store, "get_or_create", None)
    if not callable(get_or_create):
        raise TypeError("runtime_store must define get_or_create()")
    service = get_or_create(
        APPLICATION_OPERATION_SERVICE_RUNTIME_KEY,
        ApplicationOperationService,
    )
    if not isinstance(service, ApplicationOperationService):
        raise TypeError(
            "Runtime store application-operation key contains an incompatible value"
        )
    return service


__all__ = [
    "APPLICATION_OPERATION_SERVICE_RUNTIME_KEY",
    "ApplicationOperationBusyError",
    "ApplicationOperationClosedError",
    "ApplicationOperationLease",
    "ApplicationOperationLeaseReleasedError",
    "ApplicationOperationRegistration",
    "ApplicationOperationService",
    "get_application_operation_service",
    "session_operation_exclusivity_key",
]
