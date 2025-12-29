from __future__ import annotations

from pathlib import Path
from typing import List
import threading

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import AgentCore


def _make_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": {
            "providers": ["tests.dummy_provider.DummyProvider"],
        },
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def test_shared_event_store_shares_cursors_between_applications(tmp_path: Path) -> None:
    """advance_session_cursor is shared across applications using one store.

    Two AgentApplication instances that are constructed with the same
    InMemoryEventStore should observe a consistent per-session cursor so
    that polling clients can rely on a single persistence boundary.
    """

    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    store = InMemoryEventStore()

    app1 = AgentApplication(
        str(config_path), str(session_root), core_factory=AgentCore, event_store=store
    )
    app2 = AgentApplication(
        str(config_path), str(session_root), core_factory=AgentCore, event_store=store
    )

    core1, base_config1, session1 = app1.create_session("default")
    # Append a single user message and record a checkpoint so that the
    # cursor advances via the shared event store.
    session1 = core1.add_message(session1, "user", "hello")
    app1.save_session(session1)
    cursor_id = app1.record_checkpoint(session1.session_id, None)

    assert isinstance(cursor_id, str) and cursor_id
    assert app1.get_session_cursor_event_id(session1.session_id) == cursor_id
    # The second application, using the same event store, should see the
    # same cursor without having recorded it itself.
    assert app2.get_session_cursor_event_id(session1.session_id) == cursor_id


def test_shared_event_store_shares_locks_between_applications(tmp_path: Path) -> None:
    """acquire_session_lock coordinates access across applications.

    When multiple AgentApplication instances share an InMemoryEventStore,
    acquiring a lock for the same session_id from both should serialize
    access via the shared store-level lock implementation.
    """

    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    store = InMemoryEventStore()

    app1 = AgentApplication(
        str(config_path), str(session_root), core_factory=AgentCore, event_store=store
    )
    app2 = AgentApplication(
        str(config_path), str(session_root), core_factory=AgentCore, event_store=store
    )

    core1, base_config1, session1 = app1.create_session("default")
    session_id = session1.session_id

    order: List[str] = []

    def worker(app: AgentApplication, tag: str) -> None:
        with app.acquire_session_lock(session_id):
            order.append(f"{tag}-enter")
            order.append(f"{tag}-exit")

    t1 = threading.Thread(target=worker, args=(app1, "app1"))
    t2 = threading.Thread(target=worker, args=(app2, "app2"))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Both workers should have executed their critical sections, and
    # each pair of (enter, exit) markers for a given tag must be
    # adjacent in the log, demonstrating that the shared lock
    # serialized access across applications.
    assert sorted(order) == ["app1-enter", "app1-exit", "app2-enter", "app2-exit"]

    for tag in ("app1", "app2"):
        enter = f"{tag}-enter"
        exit = f"{tag}-exit"
        ei = order.index(enter)
        xi = order.index(exit)
        assert xi == ei + 1

