from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol
from threading import Lock
from itertools import count


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


class InMemoryEventStore(EventStore):
    """Simple in-memory event store for testing and local usage.

    Events are not persisted across process restarts. Access is protected by
    a lock so that background streaming threads can safely publish while
    callers poll via :meth:`list`.
    """

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._counter = count(1)
        self._lock = Lock()

    def _next_id(self) -> str:
        return str(next(self._counter))

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
        def _to_int(value: Any) -> int:
            try:
                return int(value)
            except Exception:  # pragma: no cover - defensive
                return -1

        since = _to_int(since_id) if since_id is not None else 0

        with self._lock:
            result: List[Dict[str, Any]] = []
            for ev in self._events:
                if _to_int(ev.get("event_id")) <= since:
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
