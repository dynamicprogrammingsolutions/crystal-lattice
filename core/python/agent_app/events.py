from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Iterator, Tuple, TypedDict
from threading import Lock
from contextlib import contextmanager
from itertools import count
import uuid
import time


_INTERNAL_PUBLISHED_AT = "__event_store_published_at_monotonic"
_INTERNAL_COUNTER = "__event_store_counter"


class EventListResult(TypedDict):
    events: List[Dict[str, Any]]
    latest_event_id: Optional[str]
    cursor_expired: bool


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
    ) -> EventListResult:  # pragma: no cover - interface
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

    def __init__(
        self,
        *,
        max_events_global: Optional[int] = 10000,
        max_event_age_seconds: Optional[float] = None,
    ) -> None:
        self._events: List[Dict[str, Any]] = []
        self._counter = count(1)
        self._instance_id = uuid.uuid4().hex
        self._lock = Lock()
        self._max_events_global = max_events_global
        self._max_event_age_seconds = max_event_age_seconds
        self._highest_evicted_counter_global = 0
        self._highest_evicted_counter_by_session: Dict[str, int] = {}
        self._highest_evicted_counter_by_request: Dict[str, int] = {}
        # Optional shared state for per-session cursors and locks. These are
        # used by application instances that share this store so that
        # checkpoint cursors and filesystem access are coordinated across
        # frontends within a process.
        self._session_cursors: Dict[str, Optional[str]] = {}
        self._session_locks: Dict[str, Lock] = {}
        self._session_locks_lock = Lock()

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
            counter = next(self._counter)
            stored = {**event}
            stored.setdefault("event_id", f"{self._instance_id}:{counter}")
            stored[_INTERNAL_COUNTER] = counter
            stored[_INTERNAL_PUBLISHED_AT] = time.monotonic()
            self._events.append(stored)
            self._prune_locked()
            return self._to_public_event(stored)

    def list(
        self,
        *,
        since_id: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> EventListResult:
        def _counter_for_current_instance(value: Any) -> int:
            instance_id, counter = self._parse_event_id(value)
            if counter is None:
                return 0
            if instance_id is None:
                return counter
            if instance_id != self._instance_id:
                return 0
            return counter

        since = _counter_for_current_instance(since_id) if since_id is not None else 0

        with self._lock:
            latest_event_id: Optional[str] = None
            for ev in reversed(self._events):
                if request_id is not None and ev.get("request_id") != request_id:
                    continue
                if session_id is not None and ev.get("session_id") != session_id:
                    continue
                event_id = ev.get("event_id")
                if isinstance(event_id, str):
                    latest_event_id = event_id
                    break

            result: List[Dict[str, Any]] = []
            for ev in self._events:
                event_counter = ev.get(_INTERNAL_COUNTER)
                if not isinstance(event_counter, int) or event_counter <= since:
                    continue
                if request_id is not None and ev.get("request_id") != request_id:
                    continue
                if session_id is not None and ev.get("session_id") != session_id:
                    continue
                result.append(self._to_public_event(ev))
                if len(result) >= limit:
                    break
            return {
                "events": result,
                "latest_event_id": latest_event_id,
                "cursor_expired": self._cursor_expired_locked(
                    since_id=since_id,
                    request_id=request_id,
                    session_id=session_id,
                ),
            }

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

        Generated IDs contain the store instance and an increasing local
        counter. Callers should treat them as opaque cursors; this helper
        performs a linear search over the in-memory list without requiring
        callers to parse the representation.
        """

        if not isinstance(event_id, str) or not event_id:
            return None

        with self._lock:
            for ev in self._events:
                if ev.get("event_id") == event_id:
                    return self._to_public_event(ev)
        return None

    def _scope_highest_evicted_counter_locked(
        self,
        *,
        request_id: Optional[str],
        session_id: Optional[str],
    ) -> int:
        if isinstance(request_id, str) and request_id:
            return self._highest_evicted_counter_by_request.get(request_id, 0)
        if isinstance(session_id, str) and session_id:
            return self._highest_evicted_counter_by_session.get(session_id, 0)
        return self._highest_evicted_counter_global

    def _cursor_expired_locked(
        self,
        *,
        since_id: Optional[str],
        request_id: Optional[str],
        session_id: Optional[str],
    ) -> bool:
        if not isinstance(since_id, str) or not since_id or since_id == "0":
            return False

        instance_id, counter = self._parse_event_id(since_id)
        if counter is None or counter <= 0:
            return False
        if instance_id != self._instance_id:
            return False

        return self._scope_highest_evicted_counter_locked(
            request_id=request_id,
            session_id=session_id,
        ) >= counter

    def _record_evicted_event_locked(self, ev: Dict[str, Any]) -> None:
        counter = ev.get(_INTERNAL_COUNTER)
        if not isinstance(counter, int):
            return

        if counter > self._highest_evicted_counter_global:
            self._highest_evicted_counter_global = counter

        session_id = ev.get("session_id")
        if isinstance(session_id, str) and session_id:
            current = self._highest_evicted_counter_by_session.get(session_id, 0)
            if counter > current:
                self._highest_evicted_counter_by_session[session_id] = counter

        request_id = ev.get("request_id")
        if isinstance(request_id, str) and request_id:
            current = self._highest_evicted_counter_by_request.get(request_id, 0)
            if counter > current:
                self._highest_evicted_counter_by_request[request_id] = counter

    def _prune_locked(self) -> None:
        evicted: List[Dict[str, Any]] = []

        if isinstance(self._max_event_age_seconds, (int, float)) and self._max_event_age_seconds >= 0:
            cutoff = time.monotonic() - float(self._max_event_age_seconds)
            keep_from = 0
            for idx, ev in enumerate(self._events):
                published_at = ev.get(_INTERNAL_PUBLISHED_AT)
                if not isinstance(published_at, (int, float)) or published_at >= cutoff:
                    keep_from = idx
                    break
            else:
                keep_from = len(self._events)

            if keep_from > 0:
                evicted.extend(self._events[:keep_from])
                self._events = self._events[keep_from:]

        if isinstance(self._max_events_global, int) and self._max_events_global >= 0:
            overflow = len(self._events) - self._max_events_global
            if overflow > 0:
                evicted.extend(self._events[:overflow])
                self._events = self._events[overflow:]

        for ev in evicted:
            self._record_evicted_event_locked(ev)

    def _to_public_event(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: value
            for key, value in ev.items()
            if key not in {_INTERNAL_PUBLISHED_AT, _INTERNAL_COUNTER}
        }

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
