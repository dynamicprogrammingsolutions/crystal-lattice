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
            return list(result)
