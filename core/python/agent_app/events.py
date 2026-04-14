from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Iterator, Tuple
from threading import Lock
from contextlib import contextmanager
from itertools import count
import uuid


class EventStore(Protocol):
    """Abstract interface for publishing and listing application events."""

    def publish(self, event: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - interface
        ...

    def list(
        self,
        *,
        since_id: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        ...

    def get_latest_event_id(
        self,
        *,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional[str]:  # pragma: no cover - interface
        """Return the event_id of the most recent matching event.

        When both ``request_id`` and ``session_id`` are ``None``, this
        returns the latest event_id across the entire store, or
        ``None`` if the store is empty.
        """
        ...

    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:  # pragma: no cover - interface
        """Return the stored event with the given ``event_id``, if any."""
        ...

    # Cursor and locking helpers

    def advance_session_cursor(self, session_id: str, event_id: str) -> None:  # pragma: no cover - interface
        """Advance the per-session cursor for ``session_id`` to ``event_id``."""
        ...

    def get_session_cursor_event_id(self, session_id: str) -> Optional[str]:  # pragma: no cover - interface
        """Return the latest cursor event id for ``session_id``, if known."""
        ...

    def acquire_session_lock(self, session_id: str) -> Iterator[None]:  # pragma: no cover - interface
        """Yield under a process-local lock for ``session_id``."""
        ...


class InMemoryEventStore(EventStore):
    """Simple in-memory event store for testing and local usage.

    Events are not persisted across process restarts. Access is protected by
    a lock so that background streaming threads can safely publish while
    callers poll via :meth:`list`.
    """

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._counter = count(1)
        self._instance_id = uuid.uuid4().hex
        self._lock = Lock()
        # Optional shared state for per-session cursors and locks. These are
        # used by application instances that share this store so that
        # checkpoint cursors and filesystem access are coordinated across
        # frontends within a process.
        self._session_cursors: Dict[str, Optional[str]] = {}
        self._session_locks: Dict[str, Lock] = {}
        self._session_locks_lock = Lock()

    def _next_id(self) -> str:
        return f"{self._instance_id}:{next(self._counter)}"

    def _parse_event_id(self, value: Any) -> Tuple[Optional[str], Optional[int]]:
        if isinstance(value, int):
            return None, value
        if not isinstance(value, str) or not value:
            return None, None
        if value == "0":
            return None, 0
        if ":" not in value:
            # Legacy unscoped ids are ambiguous across process restarts.
            # Replay from the beginning instead of risking skipped events.
            return None, 0

        instance_id, _, counter_text = value.partition(":")
        try:
            counter = int(counter_text)
        except Exception:  # pragma: no cover - defensive
            return instance_id or None, None
        return instance_id or None, counter

    def publish(self, event: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            stored = {**event}
            stored.setdefault("event_id", self._next_id())
            self._events.append(stored)
            return stored

    def list(
        self,
        *,
        since_id: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        def _counter_for_current_instance(value: Any) -> int:
            instance_id, counter = self._parse_event_id(value)
            if counter is None:
                return -1
            if instance_id is None:
                return counter
            if instance_id != self._instance_id:
                return 0
            return counter

        since = _counter_for_current_instance(since_id) if since_id is not None else 0

        with self._lock:
            result: List[Dict[str, Any]] = []
            for ev in self._events:
                _event_instance, event_counter = self._parse_event_id(ev.get("event_id"))
                if event_counter is None or event_counter <= since:
                    continue
                if request_id is not None and ev.get("request_id") != request_id:
                    continue
                if session_id is not None and ev.get("session_id") != session_id:
                    continue
                result.append(ev)
                if len(result) >= limit:
                    break
            return result

    def get_latest_event_id(
        self,
        *,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional[str]:
        """Return the event_id of the most recent matching event.

        When both filters are ``None``, this returns the event_id of
        the last event in the store, or ``None`` if no events have
        been published.
        """

        with self._lock:
            for ev in reversed(self._events):
                if request_id is not None and ev.get("request_id") != request_id:
                    continue
                if session_id is not None and ev.get("session_id") != session_id:
                    continue
                event_id = ev.get("event_id")
                if isinstance(event_id, str):
                    return event_id
                try:
                    # Accept integer-like ids but normalise to str.
                    if isinstance(event_id, int):
                        return str(event_id)
                except Exception:  # pragma: no cover - defensive
                    pass
            return None

    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Return the stored event with the given ``event_id``, if any.

        Event ids are assigned monotonically increasing integer-like strings,
        but this helper performs a simple linear search over the in-memory
        list so callers do not need to depend on that representation.
        """

        if not isinstance(event_id, str) or not event_id:
            return None

        with self._lock:
            for ev in self._events:
                if ev.get("event_id") == event_id:
                    return ev
        return None

    # ------------------------------------------------------------------
    # Optional helpers: per-session cursor and lock coordination
    # ------------------------------------------------------------------

    def advance_session_cursor(self, session_id: str, event_id: str) -> None:
        """Advance the per-session cursor for ``session_id``.

        The cursor is stored in the shared event store instance so that
        multiple :class:`AgentApplication` objects using this store can
        observe a consistent view of persistence boundaries.
        """

        if isinstance(session_id, str) and isinstance(event_id, str):
            self._session_cursors[session_id] = event_id

    def get_session_cursor_event_id(self, session_id: str) -> Optional[str]:
        """Return the latest cursor event id for ``session_id`` if known."""

        if not isinstance(session_id, str) or not session_id:
            return None
        return self._session_cursors.get(session_id)

    @contextmanager
    def acquire_session_lock(self, session_id: str) -> Iterator[None]:
        """Yield under a process-local lock for ``session_id``.

        This mirrors :meth:`AgentApplication.acquire_session_lock` but lives
        on the shared event store so that multiple application instances
        using the same store coordinate access to a session's persisted
        state and cursor.
        """

        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        with self._session_locks_lock:
            lock = self._session_locks.get(session_id)
            if lock is None:
                lock = Lock()
                self._session_locks[session_id] = lock
        with lock:
            yield
