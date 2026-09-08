from __future__ import annotations

from dataclasses import replace
from typing import Dict, Optional

import pytest

from agent_app.session_request_status import SessionRequestStatusService
from agent_app.sessions import SessionStoreRecord
from agent_core import Message, Session


class _Store:
    def __init__(self, sessions: Dict[str, Session]) -> None:
        self.sessions = sessions
        self.revisions = {session_id: 1 for session_id in sessions}
        self.load_count: Dict[str, int] = {}

    def list_records(self) -> list[SessionStoreRecord]:
        return [
            SessionStoreRecord(session_id, float(index), self.revisions[session_id])
            for index, session_id in enumerate(self.sessions, start=1)
        ]

    def get_record(self, session_id: str) -> Optional[SessionStoreRecord]:
        if session_id not in self.sessions:
            return None
        return SessionStoreRecord(
            session_id=session_id,
            modified=float(self.revisions[session_id]),
            revision=self.revisions[session_id],
        )

    def load(
        self,
        session_id: str,
        *,
        snapshot_id: Optional[str] = None,
    ) -> Optional[Session]:
        _ = snapshot_id
        self.load_count[session_id] = self.load_count.get(session_id, 0) + 1
        return self.sessions.get(session_id)

    def save(self, session: Session) -> None:
        self.sessions[session.session_id] = session
        self.revisions[session.session_id] = (
            self.revisions.get(session.session_id, 0) + 1
        )

    def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)
        self.revisions.pop(session_id, None)


def _session(session_id: str, *messages: Message) -> Session:
    return Session(session_id=session_id, messages=list(messages), metadata={})


def test_classifies_requested_session_tails_and_missing_ids() -> None:
    store = _Store(
        {
            "idle": _session(
                "idle",
                Message(role="system", content="setup"),
            ),
            "not-started": _session(
                "not-started",
                Message(role="user", content="question"),
            ),
            "completed": _session(
                "completed",
                Message(role="user", content="question"),
                Message(role="assistant", content="answer"),
            ),
            "tool-call": _session(
                "tool-call",
                Message(
                    role="assistant",
                    content="",
                    metadata={"tool_calls": [{"id": "call-1"}]},
                ),
            ),
            "tool-tail": _session(
                "tool-tail",
                Message(role="tool", content="partial result"),
            ),
        }
    )
    service = SessionRequestStatusService(
        store=store,
        get_active_request_id=lambda _session_id: None,
    )

    snapshot = service.query(
        [
            "idle",
            "not-started",
            "completed",
            "tool-call",
            "tool-tail",
            "missing",
            "completed",
        ]
    )

    assert [status.session_id for status in snapshot.statuses] == [
        "idle",
        "not-started",
        "completed",
        "tool-call",
        "tool-tail",
    ]
    assert [status.state for status in snapshot.statuses] == [
        "idle",
        "not_started",
        "succeeded",
        "interrupted",
        "interrupted",
    ]
    assert snapshot.missing_session_ids == ("missing",)


def test_active_request_overrides_cached_tail_without_reloading() -> None:
    store = _Store(
        {
            "session": _session(
                "session",
                Message(role="assistant", content="done"),
            )
        }
    )
    active: Dict[str, str] = {}
    service = SessionRequestStatusService(
        store=store,
        get_active_request_id=lambda session_id: active.get(session_id),
    )

    first = service.query(["session"]).statuses[0]
    active["session"] = "request-1"
    running = service.query(["session"]).statuses[0]
    active.clear()
    completed = service.query(["session"]).statuses[0]

    assert first.state == "succeeded"
    assert running.state == "running"
    assert running.request_id == "request-1"
    assert running.basis == "active_request"
    assert completed.state == "succeeded"
    assert store.load_count == {"session": 1}


def test_reloads_tail_only_after_store_revision_changes() -> None:
    original = _session("session", Message(role="user", content="question"))
    store = _Store({"session": original})
    service = SessionRequestStatusService(
        store=store,
        get_active_request_id=lambda _session_id: None,
    )

    assert service.query(["session"]).statuses[0].state == "not_started"
    assert service.query(["session"]).statuses[0].state == "not_started"

    store.save(
        replace(
            original,
            messages=[
                *original.messages,
                Message(role="assistant", content="answer"),
            ],
        )
    )

    assert service.query(["session"]).statuses[0].state == "succeeded"
    assert store.load_count == {"session": 2}


@pytest.mark.parametrize(
    "session_ids",
    [
        "session",
        [""],
        [1],
    ],
)
def test_rejects_invalid_explicit_id_inputs(session_ids: object) -> None:
    service = SessionRequestStatusService(
        store=_Store({}),
        get_active_request_id=lambda _session_id: None,
    )

    with pytest.raises(ValueError):
        service.query(session_ids)  # type: ignore[arg-type]


def test_bounds_unique_requested_ids() -> None:
    service = SessionRequestStatusService(
        store=_Store({}),
        get_active_request_id=lambda _session_id: None,
        max_session_ids=2,
    )

    with pytest.raises(ValueError, match="more than 2"):
        service.query(["a", "b", "c"])
