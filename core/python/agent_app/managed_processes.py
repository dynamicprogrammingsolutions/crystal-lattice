from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any, Callable, Protocol, TypeVar

from agent_core.utils import get_logger


MANAGED_PROCESS_REGISTRY_RUNTIME_KEY = "agent_app.managed_process_registry"


class ManagedProcess(Protocol):
    """Opaque application-lifetime background work owned by a plugin."""

    def start(self) -> None:
        """Launch background work and return promptly."""

    def close(self) -> None:
        """Signal shutdown, invalidate late work, and return promptly."""


class RuntimeStoreWithGetOrCreate(Protocol):
    def get_or_create(self, key: str, factory: Callable[[], Any]) -> Any:
        """Return the value for ``key``, creating it atomically when absent."""


class ManagedProcessAlreadyExistsError(RuntimeError):
    def __init__(self, process_id: str) -> None:
        super().__init__(f"Managed process {process_id!r} is already registered")
        self.process_id = process_id


class ManagedProcessRegistryClosedError(RuntimeError):
    pass


@dataclass
class _ManagedProcessEntry:
    process: ManagedProcess
    starting: bool = True
    remove_requested: bool = False


ManagedProcessT = TypeVar("ManagedProcessT", bound=ManagedProcess)


class ManagedProcessRegistry:
    """Registry for opaque in-memory process objects owned by one application."""

    def __init__(self) -> None:
        self._condition = threading.Condition(threading.RLock())
        self._entries: dict[str, _ManagedProcessEntry] = {}
        self._starting_count = 0
        self._closing = False
        self._closed = False
        self._logger = get_logger("ManagedProcessRegistry")

    def start(
        self,
        process_id: str,
        process: ManagedProcessT,
    ) -> ManagedProcessT:
        """Register and start ``process`` under ``process_id``."""

        self._validate_process_id(process_id)
        self._validate_process(process)
        entry = _ManagedProcessEntry(process=process)

        with self._condition:
            if self._closed:
                raise ManagedProcessRegistryClosedError("Managed process registry is closed")
            if process_id in self._entries:
                raise ManagedProcessAlreadyExistsError(process_id)
            self._entries[process_id] = entry
            self._starting_count += 1

        try:
            process.start()
        except BaseException:
            with self._condition:
                if self._entries.get(process_id) is entry:
                    self._entries.pop(process_id, None)
            try:
                self._safe_close(process_id, process, phase="startup_cleanup")
            finally:
                with self._condition:
                    self._starting_count -= 1
                    self._condition.notify_all()
            raise

        close_after_start = False
        with self._condition:
            if self._entries.get(process_id) is entry:
                if self._closed:
                    self._entries.pop(process_id, None)
                    close_after_start = True
                elif entry.remove_requested:
                    self._entries.pop(process_id, None)
                else:
                    entry.starting = False

            if not close_after_start:
                self._starting_count -= 1
                self._condition.notify_all()

        if close_after_start:
            try:
                self._safe_close(process_id, process, phase="close_during_start")
            finally:
                with self._condition:
                    self._starting_count -= 1
                    self._condition.notify_all()
            raise ManagedProcessRegistryClosedError(
                "Managed process registry closed while the process was starting"
            )

        return process

    def get(self, process_id: str) -> ManagedProcess | None:
        """Return the registered process, including while it is starting."""

        self._validate_process_id(process_id)
        with self._condition:
            entry = self._entries.get(process_id)
            return entry.process if entry is not None else None

    def remove(self, process_id: str, process: ManagedProcess) -> bool:
        """Remove only the entry matching both ``process_id`` and identity."""

        self._validate_process_id(process_id)
        with self._condition:
            entry = self._entries.get(process_id)
            if entry is None or entry.process is not process:
                return False
            if self._closed:
                return False
            if entry.starting:
                entry.remove_requested = True
            else:
                self._entries.pop(process_id, None)
            return True

    def close(self) -> None:
        """Close every registered process and reject future starts."""

        with self._condition:
            if self._closed:
                while self._closing:
                    self._condition.wait()
                return
            self._closed = True
            self._closing = True
            while self._starting_count:
                self._condition.wait()
            entries = list(self._entries.items())
            self._entries.clear()

        try:
            for process_id, entry in entries:
                self._safe_close(process_id, entry.process, phase="registry_close")
        finally:
            with self._condition:
                self._closing = False
                self._condition.notify_all()

    @staticmethod
    def _validate_process_id(process_id: str) -> None:
        if not isinstance(process_id, str) or not process_id:
            raise ValueError("process_id must be a non-empty string")

    @staticmethod
    def _validate_process(process: ManagedProcess) -> None:
        if not callable(getattr(process, "start", None)):
            raise TypeError("managed process must define start()")
        if not callable(getattr(process, "close", None)):
            raise TypeError("managed process must define close()")

    def _safe_close(
        self,
        process_id: str,
        process: ManagedProcess,
        *,
        phase: str,
    ) -> None:
        try:
            process.close()
        except Exception as exc:
            self._logger.warning(
                "managed_process_close_failed",
                process_id=process_id,
                phase=phase,
                error=str(exc),
            )


def get_managed_process_registry(
    runtime_store: RuntimeStoreWithGetOrCreate,
) -> ManagedProcessRegistry:
    """Return the application-owned managed process registry."""

    get_or_create = getattr(runtime_store, "get_or_create", None)
    if not callable(get_or_create):
        raise TypeError("runtime_store must define get_or_create()")
    registry = get_or_create(
        MANAGED_PROCESS_REGISTRY_RUNTIME_KEY,
        ManagedProcessRegistry,
    )
    if not isinstance(registry, ManagedProcessRegistry):
        raise TypeError("Runtime store managed-process key contains an incompatible value")
    return registry


__all__ = [
    "MANAGED_PROCESS_REGISTRY_RUNTIME_KEY",
    "ManagedProcess",
    "ManagedProcessAlreadyExistsError",
    "ManagedProcessRegistry",
    "ManagedProcessRegistryClosedError",
    "get_managed_process_registry",
]
