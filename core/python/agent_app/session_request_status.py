"""Derived latest-request status for explicitly requested sessions."""

from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple

from agent_core import Session

from .sessions import SessionStore


SessionRequestStatusState = Literal[
    "idle",
    "not_started",
    "running",
    "succeeded",
    "interrupted",
]
SessionRequestStatusBasis = Literal["active_request", "session_tail"]


@dataclass(frozen=True)
class SessionRequestStatus:
    session_id: str
    request_id: Optional[str]
    state: SessionRequestStatusState
    basis: SessionRequestStatusBasis
    session_modified: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "session_id": self.session_id,
            "request_id": self.request_id,
            "state": self.state,
            "basis": self.basis,
            "session_modified": self.session_modified,
        }


@dataclass(frozen=True)
class SessionRequestStatusSnapshot:
    statuses: Tuple[SessionRequestStatus, ...]
    missing_session_ids: Tuple[str, ...]


@dataclass(frozen=True)
class _CachedSessionTail:
    revision: object
    state: SessionRequestStatusState


class SessionRequestStatusService:
    """Classify active work and persisted session tails without listing sessions."""

    def __init__(
        self,
        *,
        store: SessionStore,
        get_active_request_id: Callable[[str], Optional[str]],
        max_session_ids: int = 200,
    ) -> None:
        if max_session_ids <= 0:
            raise ValueError("max_session_ids must be positive")
        self._store = store
        self._get_active_request_id = get_active_request_id
        self._max_session_ids = max_session_ids
        self._cache: Dict[str, _CachedSessionTail] = {}
        self._lock = threading.RLock()

    @property
    def max_session_ids(self) -> int:
        return self._max_session_ids

    def invalidate(self, session_id: Optional[str] = None) -> None:
        with self._lock:
            if session_id is None:
                self._cache.clear()
            else:
                self._cache.pop(session_id, None)

    def query(self, session_ids: Sequence[str]) -> SessionRequestStatusSnapshot:
        normalized = self._normalize_session_ids(session_ids)
        statuses: List[SessionRequestStatus] = []
        missing: List[str] = []

        with self._lock:
            for session_id in normalized:
                record = self._store.get_record(session_id)
                if record is None:
                    self._cache.pop(session_id, None)
                    missing.append(session_id)
                    continue

                active_request_id = self._get_active_request_id(session_id)
                if active_request_id is not None:
                    statuses.append(
                        SessionRequestStatus(
                            session_id=session_id,
                            request_id=active_request_id,
                            state="running",
                            basis="active_request",
                            session_modified=record.modified,
                        )
                    )
                    continue

                cached = self._cache.get(session_id)
                if cached is None or cached.revision != record.revision:
                    session = self._store.load(session_id)
                    if session is None:
                        self._cache.pop(session_id, None)
                        missing.append(session_id)
                        continue
                    cached = _CachedSessionTail(
                        revision=record.revision,
                        state=self._classify_session_tail(session),
                    )
                    self._cache[session_id] = cached

                statuses.append(
                    SessionRequestStatus(
                        session_id=session_id,
                        request_id=None,
                        state=cached.state,
                        basis="session_tail",
                        session_modified=record.modified,
                    )
                )

        return SessionRequestStatusSnapshot(
            statuses=tuple(statuses),
            missing_session_ids=tuple(missing),
        )

    def _normalize_session_ids(self, session_ids: Sequence[str]) -> Tuple[str, ...]:
        if isinstance(session_ids, (str, bytes)) or not isinstance(
            session_ids, Sequence
        ):
            raise ValueError("session_ids must be a list of non-empty strings")

        normalized: List[str] = []
        seen: set[str] = set()
        for raw_session_id in session_ids:
            if not isinstance(raw_session_id, str) or not raw_session_id:
                raise ValueError("session_ids must contain only non-empty strings")
            if raw_session_id in seen:
                continue
            seen.add(raw_session_id)
            normalized.append(raw_session_id)

        if len(normalized) > self._max_session_ids:
            raise ValueError(
                f"session_ids cannot contain more than {self._max_session_ids} unique values"
            )
        return tuple(normalized)

    @staticmethod
    def _classify_session_tail(session: Session) -> SessionRequestStatusState:
        conversational = [
            message
            for message in session.messages
            if message.role in {"user", "assistant", "tool"}
        ]
        if not conversational:
            return "idle"

        tail = conversational[-1]
        if tail.role == "user":
            return "not_started"
        if tail.role != "assistant":
            return "interrupted"

        metadata = tail.metadata if isinstance(tail.metadata, dict) else {}
        tool_calls = metadata.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            return "interrupted"
        return "succeeded"


__all__ = [
    "SessionRequestStatus",
    "SessionRequestStatusBasis",
    "SessionRequestStatusService",
    "SessionRequestStatusSnapshot",
    "SessionRequestStatusState",
]
