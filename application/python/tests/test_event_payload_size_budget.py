"""Size-budget regression tests for published events.

These tests do not assert on specific event fields (like ``session``). Instead
they enforce a coarse size budget relative to the largest message in each
session. The goal is to catch accidental re-introduction of full-session
payloads in events.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


ROOT = Path(__file__).resolve().parents[3]
APP_PY = ROOT / "application/python"
CORE_PY = ROOT / "core/python"
for path in (ROOT, APP_PY, CORE_PY):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _json_size_bytes(value: Any) -> int:
    return len(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _assert_events_within_size_budget(
    *,
    events: List[Dict[str, Any]],
    app: Any,
    multiplier: int = 2,
    overhead_bytes: int = 4096,
) -> None:
    session_ids = {
        ev.get("session_id")
        for ev in events
        if isinstance(ev, dict) and isinstance(ev.get("session_id"), str)
    }
    assert session_ids

    max_message_sizes: Dict[str, int] = {}
    for session_id in session_ids:
        ctx = app.load_session(session_id)
        assert ctx is not None
        _core, _base_config, session = ctx
        session_dict = session.to_dict()
        raw_messages = session_dict.get("messages") or []
        messages = [m for m in raw_messages if isinstance(m, dict)]
        assert messages
        max_message_sizes[session_id] = max(_json_size_bytes(m) for m in messages)

    failures: List[str] = []
    for ev in events:
        session_id = ev.get("session_id")
        if not isinstance(session_id, str):
            continue
        budget = max_message_sizes[session_id] * multiplier + overhead_bytes
        size = _json_size_bytes(ev)
        if size > budget:
            failures.append(
                f"event too large: type={ev.get('type')!r} id={ev.get('event_id')!r} "
                f"size={size}B budget={budget}B session_id={session_id}"
            )

    assert not failures, "\n".join(failures[:10])


def _padding_message(idx: int) -> str:
    return f"padding-{idx}-" + ("x" * 800)


@pytest.mark.parametrize("surface", ["server", "terminal"])
def test_event_payload_size_budget_message_modified(tmp_path: Path, surface: str) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import server as server_mod
    from agent_terminal_app import terminal as term_mod

    config_path = Path(server_mod.__file__).resolve().parent / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=store)

    if surface == "server":
        create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
        session_id = create["session"]["session_id"]
        for idx in range(20):
            server_mod.add_message(
                session_id,
                {"role": "user", "content": _padding_message(idx), "metadata": None},
                app_instance=app,
            )

        server_mod.update_message(
            session_id,
            0,
            {"content": "modified"},
            app_instance=app,
        )
    else:
        term_app = term_mod.TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            agent_app=app,
        )
        session = term_app.start_new_session(agent_id="default")
        session_id = session.session_id
        for idx in range(20):
            term_app.append_user_message(_padding_message(idx), metadata=None)
        term_app.modify_message(0, "modified")

    events = app.get_event_store().list(session_id=session_id, limit=20000)
    assert any(ev.get("type") == "message_modified" for ev in events)
    _assert_events_within_size_budget(events=events, app=app)


@pytest.mark.parametrize("surface", ["server", "terminal"])
def test_event_payload_size_budget_messages_deleted(tmp_path: Path, surface: str) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import server as server_mod
    from agent_terminal_app import terminal as term_mod

    config_path = Path(server_mod.__file__).resolve().parent / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=store)

    if surface == "server":
        create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
        session_id = create["session"]["session_id"]
        for idx in range(20):
            server_mod.add_message(
                session_id,
                {"role": "user", "content": _padding_message(idx), "metadata": None},
                app_instance=app,
            )

        server_mod.delete_messages(
            session_id,
            {"indices": [1]},
            app_instance=app,
        )
    else:
        term_app = term_mod.TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            agent_app=app,
        )
        session = term_app.start_new_session(agent_id="default")
        session_id = session.session_id
        for idx in range(20):
            term_app.append_user_message(_padding_message(idx), metadata=None)
        term_app.delete_messages([1])

    events = app.get_event_store().list(session_id=session_id, limit=20000)
    assert any(ev.get("type") == "messages_deleted" for ev in events)
    _assert_events_within_size_budget(events=events, app=app)


@pytest.mark.parametrize("surface", ["server", "terminal"])
def test_event_payload_size_budget_session_fork(tmp_path: Path, surface: str) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import server as server_mod
    from agent_terminal_app import terminal as term_mod

    config_path = Path(server_mod.__file__).resolve().parent / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=store)

    if surface == "server":
        create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
        session_id = create["session"]["session_id"]
        for idx in range(20):
            server_mod.add_message(
                session_id,
                {"role": "user", "content": _padding_message(idx), "metadata": None},
                app_instance=app,
            )

        fork = server_mod.fork_session(session_id, {"index": -1}, app_instance=app)
        fork_session_id = fork["session"]["session_id"]
    else:
        term_app = term_mod.TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            agent_app=app,
        )
        session = term_app.start_new_session(agent_id="default")
        session_id = session.session_id
        for idx in range(20):
            term_app.append_user_message(_padding_message(idx), metadata=None)
        forked = term_app.fork_session(-1)
        fork_session_id = forked.session_id

    all_events = app.get_event_store().list(limit=20000)
    assert any(
        ev.get("type") == "session_created" and ev.get("session_id") == fork_session_id
        for ev in all_events
    )
    _assert_events_within_size_budget(events=all_events, app=app)
