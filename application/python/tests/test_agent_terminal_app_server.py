"""Tests for the agent_terminal_app server functions.

These tests mirror the style of the example application tests under
``core/python/examples/tests`` but exercise the FastAPI-style route
functions directly, injecting an ``AgentApplication`` instance instead
of going through the HTTP layer.
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

import threading
import time

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Message, Session

# Make dotted-path test plugins available to the application plugin loader.
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from tests.dummy_provider import DummyProvider  # noqa: F401


def _make_multi_provider_echo_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "echo-model"},
            "dummy": {"provider": "dummy_provider", "model": "dummy-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "tests.dummy_provider.DummyProvider",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
    }

    path = tmp_path / "config_multi_provider_echo.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _wait_for_request_completion(app: AgentApplication, session_id: str, timeout_seconds: float = 10.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        events = app.get_event_store().list(session_id=session_id, limit=100)
        kinds = {ev.get("type") for ev in events}
        if "final" in kinds or "request_completed" in kinds:
            return
        time.sleep(0.05)
    raise AssertionError("timed out waiting for final/request_completed events")


def test_server_flow_with_echo_provider(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the agent_terminal_app test"

    # 1) Create a new session with a system message via the route function.
    create_resp = server_mod.create_session(
        {"agent_id": "default", "system_message": system_message},
        app_instance=app,
    )
    session_dict = create_resp["session"]
    session_id = session_dict["session_id"]
    assert isinstance(session_id, str) and session_id

    # 2) Add a user message.
    add_resp = server_mod.add_message(
        session_id,
        {"role": "user", "content": user_message, "metadata": None},
        app_instance=app,
    )
    updated_session = add_resp["session"]
    assert updated_session["session_id"] == session_id

    # 3) Send a request asynchronously and verify echo provider behaviour.
    send_resp = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        app_instance=app,
    )

    assert send_resp.get("status") == "started"
    request_id = send_resp.get("request_id")
    assert isinstance(request_id, str) and request_id

    # Wait for the background worker to finish and record a final event.
    deadline = time.time() + 30.0
    final_kinds: set[str] = set()
    while time.time() < deadline:
        events = app.get_event_store().list(session_id=session_id, limit=100)
        final_kinds = {ev.get("type") for ev in events}
        if "final" in final_kinds or "request_completed" in final_kinds:
            break
        time.sleep(0.1)

    assert ("final" in final_kinds) or ("request_completed" in final_kinds), (
        "timed out waiting for final/request_completed events",
    )

    # Reload the final session from the application to avoid relying on
    # the shape of the streaming events.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, final_session = ctx
    session_dict = final_session.to_dict()

    history = session_dict.get("messages") or []
    assert history, "expected at least one message in the final session"
    # For the echo config we only require that the call completes and
    # that the session history was not corrupted; we do not assert on
    # the exact assistant content here.

    # 4) Basic check that events were recorded for this session.
    events = app.get_event_store().list(session_id=session_id, limit=100)
    kinds = {ev.get("type") for ev in events}
    assert "session_created" in kinds
    assert "message_appended" in kinds
    assert "request_started" in kinds or "final" in kinds


def test_server_delete_preserves_native_history_with_multiple_loaded_providers(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    config_path = _make_multi_provider_echo_config(tmp_path)
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session(
        {"agent_id": "default"},
        app_instance=app,
    )
    session_id = create_resp["session"]["session_id"]

    ctx = app.load_session(session_id)
    assert ctx is not None
    core, _base_config, _session = ctx
    assert len(getattr(core, "_providers")) == 1
    assert getattr(core, "_providers")[0].plugin_class.__name__ == "EchoOpenAILikeProvider"

    provider = EchoOpenAILikeProvider()
    native_messages = provider.to_native_messages(
        [
            {"role": "system", "content": "Keep native history."},
            {"role": "user", "content": "first turn"},
            {"role": "assistant", "content": "reply"},
        ],
        {},
    )
    rebuilt_core = provider.from_native_messages(native_messages, {})
    normalized_core = core._normalize_final_core_with_native_indices(
        rebuilt_core,
        native_messages,
        baseline_offset=0,
    )
    persisted_messages = [
        Message(
            role=message["role"],
            content=message.get("content", ""),
            metadata=message.get("metadata"),
        )
        for message in normalized_core
    ]
    session = Session(
        session_id=session_id,
        messages=persisted_messages,
        metadata={
            "agent_id": "default",
            "native_messages": native_messages,
            "native_messages_integrity": core._compute_native_integrity(persisted_messages),
        },
    )
    app.save_session(session)

    native_before = (session.metadata or {}).get("native_messages")
    assert isinstance(native_before, list)
    assert native_before

    delete_resp = server_mod.delete_messages(
        session_id,
        {"indices": [1]},
        app_instance=app,
    )

    deleted_metadata = delete_resp["session"].get("metadata") or {}
    native_after_delete = deleted_metadata.get("native_messages")
    assert isinstance(native_after_delete, list)
    assert native_after_delete
    assert [message["content"] for message in delete_resp["session"]["messages"]] == [
        "Keep native history.",
        "reply",
    ]

    final_ctx = app.load_session(session_id)
    assert final_ctx is not None
    final_core, _final_base_config, final_session = final_ctx
    assert len(getattr(final_core, "_providers")) == 1
    assert getattr(final_core, "_providers")[0].plugin_class.__name__ == "EchoOpenAILikeProvider"
    assert isinstance((final_session.metadata or {}).get("native_messages"), list)


def test_send_request_single_flight_blocks_while_running(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello", "metadata": None},
        app_instance=app,
    )

    started_evt = threading.Event()
    release_evt = threading.Event()
    call_count = 0
    seen_request_ids: list[str | None] = []

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
    ):
        nonlocal call_count
        call_count += 1
        seen_request_ids.append(request_id)
        started_evt.set()
        yield {
            "type": "request_started",
            "session_id": session_id,
            "request_id": request_id,
            "stream": bool(stream),
        }
        release_evt.wait(timeout=5)
        yield {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [],
        }
        yield {
            "type": "request_completed",
            "session_id": session_id,
            "request_id": request_id,
        }

    app.send_request = _fake_send_request  # type: ignore[assignment]

    resp1 = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        app_instance=app,
    )
    assert resp1.get("status") == "started"
    rid = resp1.get("request_id")
    assert isinstance(rid, str) and rid

    resp2 = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        app_instance=app,
    )
    assert resp2 == {"status": "already_running", "request_id": rid}

    assert started_evt.wait(timeout=2.0), "background worker did not start"
    assert call_count == 1
    assert seen_request_ids == [rid]

    release_evt.set()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server_mod._get_active_send_request_id(session_id) is None:
            break
        time.sleep(0.05)

    assert server_mod._get_active_send_request_id(session_id) is None


def test_send_request_idempotency_key_replays_request_id(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello", "metadata": None},
        app_instance=app,
    )

    release_evt = threading.Event()
    call_count = 0

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
    ):
        nonlocal call_count
        call_count += 1
        yield {
            "type": "request_started",
            "session_id": session_id,
            "request_id": request_id,
            "stream": bool(stream),
        }
        release_evt.wait(timeout=5)
        yield {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [],
        }
        yield {
            "type": "request_completed",
            "session_id": session_id,
            "request_id": request_id,
        }

    app.send_request = _fake_send_request  # type: ignore[assignment]

    import uuid

    idem_key = f"test-{uuid.uuid4()}"

    resp1 = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        idempotency_key=idem_key,
        app_instance=app,
    )
    assert resp1.get("status") == "started"
    rid = resp1.get("request_id")
    assert isinstance(rid, str) and rid

    resp2 = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        idempotency_key=idem_key,
        app_instance=app,
    )
    assert resp2 == resp1

    deadline = time.time() + 2.0
    while time.time() < deadline and call_count < 1:
        time.sleep(0.01)
    assert call_count == 1

    release_evt.set()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server_mod._get_active_send_request_id(session_id) is None:
            break
        time.sleep(0.05)

    assert server_mod._get_active_send_request_id(session_id) is None

    resp3 = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        idempotency_key=idem_key,
        app_instance=app,
    )
    assert resp3 == resp1
    assert call_count == 1


def test_send_message_endpoint_appends_and_starts_request(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    started_evt = threading.Event()
    release_evt = threading.Event()
    call_count = 0
    seen_request_ids: list[str | None] = []

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
    ):
        nonlocal call_count
        call_count += 1
        seen_request_ids.append(request_id)
        started_evt.set()
        yield {
            "type": "request_started",
            "session_id": session_id,
            "request_id": request_id,
            "stream": bool(stream),
        }
        release_evt.wait(timeout=5)
        yield {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [],
        }
        yield {
            "type": "request_completed",
            "session_id": session_id,
            "request_id": request_id,
        }

    app.send_request = _fake_send_request  # type: ignore[assignment]

    resp = server_mod.send_message(
        session_id,
        {
            "message": {"role": "user", "content": "hello", "metadata": None},
            "config_overrides": {},
        },
        app_instance=app,
    )
    assert resp.get("status") == "started"
    rid = resp.get("request_id")
    assert isinstance(rid, str) and rid

    assert started_evt.wait(timeout=2.0), "background worker did not start"
    assert call_count == 1
    assert seen_request_ids == [rid]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, session = ctx
    session_dict = session.to_dict()
    messages = session_dict.get("messages") or []
    assert len(messages) == 1
    assert messages[0].get("role") == "user"
    assert messages[0].get("content") == "hello"

    release_evt.set()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server_mod._get_active_send_request_id(session_id) is None:
            break
        time.sleep(0.05)

    assert server_mod._get_active_send_request_id(session_id) is None


def test_send_message_endpoint_rejects_when_active(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    started_evt = threading.Event()
    release_evt = threading.Event()
    call_count = 0

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
    ):
        nonlocal call_count
        call_count += 1
        started_evt.set()
        yield {
            "type": "request_started",
            "session_id": session_id,
            "request_id": request_id,
            "stream": bool(stream),
        }
        release_evt.wait(timeout=5)
        yield {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [],
        }
        yield {
            "type": "request_completed",
            "session_id": session_id,
            "request_id": request_id,
        }

    app.send_request = _fake_send_request  # type: ignore[assignment]

    resp1 = server_mod.send_message(
        session_id,
        {
            "message": {"role": "user", "content": "one", "metadata": None},
            "config_overrides": {},
        },
        app_instance=app,
    )
    rid = resp1.get("request_id")
    assert isinstance(rid, str) and rid
    assert started_evt.wait(timeout=2.0)

    with pytest.raises(HTTPException) as excinfo:
        server_mod.send_message(
            session_id,
            {
                "message": {"role": "user", "content": "two", "metadata": None},
                "config_overrides": {},
            },
            app_instance=app,
        )

    err = excinfo.value
    assert err.status_code == 409
    assert isinstance(err.detail, dict)
    assert err.detail.get("request_id") == rid

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, session = ctx
    messages = session.to_dict().get("messages") or []
    assert len(messages) == 1
    assert messages[0].get("content") == "one"
    assert call_count == 1

    release_evt.set()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server_mod._get_active_send_request_id(session_id) is None:
            break
        time.sleep(0.05)

    assert server_mod._get_active_send_request_id(session_id) is None


def test_send_message_endpoint_idempotency_replays_without_double_append(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    release_evt = threading.Event()
    call_count = 0

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
    ):
        nonlocal call_count
        call_count += 1
        yield {
            "type": "request_started",
            "session_id": session_id,
            "request_id": request_id,
            "stream": bool(stream),
        }
        release_evt.wait(timeout=5)
        yield {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [],
        }
        yield {
            "type": "request_completed",
            "session_id": session_id,
            "request_id": request_id,
        }

    app.send_request = _fake_send_request  # type: ignore[assignment]

    import uuid

    idem_key = f"test-{uuid.uuid4()}"

    resp1 = server_mod.send_message(
        session_id,
        {
            "message": {"role": "user", "content": "hello", "metadata": None},
            "config_overrides": {},
        },
        idempotency_key=idem_key,
        app_instance=app,
    )
    resp2 = server_mod.send_message(
        session_id,
        {
            "message": {"role": "user", "content": "hello", "metadata": None},
            "config_overrides": {},
        },
        idempotency_key=idem_key,
        app_instance=app,
    )

    assert resp2 == resp1

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, session = ctx
    messages = session.to_dict().get("messages") or []
    assert len(messages) == 1

    deadline = time.time() + 2.0
    while time.time() < deadline and call_count < 1:
        time.sleep(0.01)
    assert call_count == 1

    release_evt.set()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server_mod._get_active_send_request_id(session_id) is None:
            break
        time.sleep(0.05)

    assert server_mod._get_active_send_request_id(session_id) is None


def test_send_message_endpoint_idempotency_key_reused_with_different_payload_conflicts(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    release_evt = threading.Event()

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
    ):
        yield {
            "type": "request_started",
            "session_id": session_id,
            "request_id": request_id,
            "stream": bool(stream),
        }
        release_evt.wait(timeout=5)
        yield {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [],
        }
        yield {
            "type": "request_completed",
            "session_id": session_id,
            "request_id": request_id,
        }

    app.send_request = _fake_send_request  # type: ignore[assignment]

    import uuid

    idem_key = f"test-{uuid.uuid4()}"

    _ = server_mod.send_message(
        session_id,
        {
            "message": {"role": "user", "content": "one", "metadata": None},
            "config_overrides": {},
        },
        idempotency_key=idem_key,
        app_instance=app,
    )

    release_evt.set()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server_mod._get_active_send_request_id(session_id) is None:
            break
        time.sleep(0.05)

    assert server_mod._get_active_send_request_id(session_id) is None

    with pytest.raises(HTTPException) as excinfo:
        server_mod.send_message(
            session_id,
            {
                "message": {"role": "user", "content": "two", "metadata": None},
                "config_overrides": {},
            },
            idempotency_key=idem_key,
            app_instance=app,
        )

    assert excinfo.value.status_code == 409

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, session = ctx
    messages = session.to_dict().get("messages") or []
    assert len(messages) == 1
    assert messages[0].get("content") == "one"


def test_create_session_idempotency_key_replays_session_id(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    import uuid

    idem_key = f"test-{uuid.uuid4()}"

    resp1 = server_mod.create_session(
        {"agent_id": "default"},
        idempotency_key=idem_key,
        app_instance=app,
    )
    resp2 = server_mod.create_session(
        {"agent_id": "default"},
        idempotency_key=idem_key,
        app_instance=app,
    )

    sid1 = resp1["session"]["session_id"]
    sid2 = resp2["session"]["session_id"]
    assert sid2 == sid1
    assert len(list(session_root.glob("*.json"))) == 1


def test_get_session_ui_schema_includes_ui_types(tmp_path: Path) -> None:
    """GET /sessions/{session_id}/ui-schema exposes full UI entries.

    Uses the default config so that provider, extension, and feature
    plugins contribute both configuration and footer / status metadata
    to the schema.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "default_config.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    resp = server_mod.get_session_ui_schema(session_id, app_instance=app)
    elements = resp.get("elements")
    assert isinstance(elements, list)

    ui_types = {el.get("ui_type") for el in elements if isinstance(el, dict)}

    # Configuration entries (either explicit or defaulted) should be present.
    assert "config" in {t or "config" for t in ui_types}

    # The default config registers extensions that contribute message_footer
    # and status_bar elements (for example, timestamp_extension and
    # openrouter_usage_extension). We only require that such entries are
    # surfaced, not the exact count.
    assert "message_footer" in ui_types
    assert "status_bar" in ui_types


def test_get_session_ui_schema_respects_session_overrides(tmp_path: Path) -> None:
    """GET /sessions/{id}/ui-schema returns different elements when overrides change.

    Uses default config with openrouter_usage extension, which returns no
    elements when show_usage is false.
    """
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "default_config.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Baseline: no overrides → openrouter_usage contributes footer/status_bar elements.
    resp1 = server_mod.get_session_ui_schema(session_id, app_instance=app)
    elements1 = resp1.get("elements") or []
    from_openrouter_usage1 = [
        el for el in elements1 if isinstance(el, dict) and el.get("plugin") == "openrouter_usage"
    ]
    assert len(from_openrouter_usage1) > 0, "expected openrouter_usage elements without overrides"

    # Set override that disables usage UI.
    server_mod.patch_session_overrides(
        session_id,
        {"key": "show_usage", "value": False},
        app_instance=app,
    )

    # With show_usage: false, openrouter_usage contributes no elements.
    resp2 = server_mod.get_session_ui_schema(session_id, app_instance=app)
    elements2 = resp2.get("elements") or []
    from_openrouter_usage2 = [
        el for el in elements2 if isinstance(el, dict) and el.get("plugin") == "openrouter_usage"
    ]
    assert len(from_openrouter_usage2) == 0, (
        "expected no openrouter_usage elements when show_usage is false"
    )
    assert len(elements2) < len(elements1), (
        "schema should have fewer elements when usage UI is disabled"
    )


def test_get_session_config_schema_exposes_known_keys(tmp_path: Path) -> None:
  """GET /sessions/{id}/config/schema returns flattened config entries.

  Uses the OpenRouter application-layer config so that plugin config
  schema entries are present and can be queried by key.
  """

  from agent_terminal_app import server as server_mod

  base_dir = Path(server_mod.__file__).resolve().parent
  config_path = base_dir / "config_openrouter_app_layer.json"
  session_root = tmp_path / "sessions"

  events = InMemoryEventStore()
  app = AgentApplication(str(config_path), str(session_root), event_store=events)

  create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
  session_id = create_resp["session"]["session_id"]

  resp = server_mod.get_session_config_schema(session_id, app_instance=app)
  schema = resp.get("schema")
  assert isinstance(schema, list)

  keys = {entry.get("key") for entry in schema if isinstance(entry, dict)}
  # openrouter_reasoning_extension contributes these keys to the config schema.
  assert "reasoning_effort" in keys
  assert "enable_reasoning" in keys


def test_get_session_config_schema_exposes_known_keys(tmp_path: Path) -> None:
  """GET /sessions/{id}/config/schema exposes plugin config entries.

  Uses the OpenRouter application-layer config so that real plugin
  config schema entries are present.
  """

  from agent_terminal_app import server as server_mod

  base_dir = Path(server_mod.__file__).resolve().parent
  config_path = base_dir / "config_openrouter_app_layer.json"
  session_root = tmp_path / "sessions"

  events = InMemoryEventStore()
  app = AgentApplication(str(config_path), str(session_root), event_store=events)

  create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
  session_id = create_resp["session"]["session_id"]

  resp = server_mod.get_session_config_schema(session_id, app_instance=app)
  schema = resp.get("schema")
  assert isinstance(schema, list)

  keys = {entry.get("key") for entry in schema if isinstance(entry, dict)}
  assert "reasoning_effort" in keys
  assert "enable_reasoning" in keys


def test_get_session_base_config_returns_mapping(tmp_path: Path) -> None:
  """GET /sessions/{id}/config/base returns a config mapping."""

  from agent_terminal_app import server as server_mod

  base_dir = Path(server_mod.__file__).resolve().parent
  config_path = base_dir / "config_openrouter_app_layer.json"
  session_root = tmp_path / "sessions"

  events = InMemoryEventStore()
  app = AgentApplication(str(config_path), str(session_root), event_store=events)

  create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
  session_id = create_resp["session"]["session_id"]

  resp = server_mod.get_session_base_config(session_id, app_instance=app)
  cfg = resp.get("config")
  assert isinstance(cfg, dict)


def test_session_plugins_endpoints_roundtrip(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "default_config.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    listed = server_mod.get_session_plugins(session_id, app_instance=app)["plugins"]
    assert isinstance(listed, list) and listed

    ids: list[str] = []
    for entry in listed:
        assert isinstance(entry, dict)
        assert isinstance(entry.get("id"), str) and entry["id"]
        assert isinstance(entry.get("enabled"), bool)
        assert isinstance(entry.get("source"), str)
        assert isinstance(entry.get("active"), bool)
        ids.append(entry["id"])

    subset = ids[:2]
    put_resp = server_mod.put_session_plugins(
        session_id, {"enabled": subset}, app_instance=app
    )
    updated_session = put_resp["session"]
    metadata = updated_session.get("metadata") or {}
    assert metadata.get("plugins") == subset

    put_plugins = put_resp["plugins"]
    assert isinstance(put_plugins, list)
    for entry in put_plugins:
        assert isinstance(entry, dict)
        assert entry.get("source") == "session"
        if entry.get("id") in subset:
            assert entry.get("enabled") is True
        else:
            assert entry.get("enabled") is False

    deleted = server_mod.delete_session_plugins(session_id, app_instance=app)
    deleted_session = deleted["session"]
    deleted_metadata = deleted_session.get("metadata") or {}
    assert "plugins" not in deleted_metadata

    deleted_plugins = deleted["plugins"]
    assert isinstance(deleted_plugins, list) and deleted_plugins
    assert all(p.get("source") != "session" for p in deleted_plugins if isinstance(p, dict))


def test_run_send_request_background_helper_sends_and_persists(tmp_path: Path) -> None:
    """Internal helper _run_send_request_background mirrors /send behaviour.

    This test calls the helper directly to ensure that it drives the
    send_request flow to completion and persists the final session.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the _run_send_request_background test"

    create_resp = server_mod.create_session(
        {"agent_id": "default", "system_message": system_message},
        app_instance=app,
    )
    session_dict = create_resp["session"]
    session_id = session_dict["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": user_message, "metadata": None},
        app_instance=app,
    )

    # Run the helper synchronously; it should process the request to
    # completion and save the final session.
    server_mod._run_send_request_background(app, session_id, {})

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, final_session = ctx
    session_dict = final_session.to_dict()
    history = session_dict.get("messages") or []
    assert history, "expected at least one message in the final session"

    evs = app.get_event_store().list(session_id=session_id, limit=100)
    kinds = {ev.get("type") for ev in evs}
    assert "request_started" in kinds
    assert "final" in kinds or "request_completed" in kinds

    # A checkpoint marker should also have been recorded for this session.
    checkpoint_events = [ev for ev in evs if ev.get("type") == "checkpoint"]
    assert checkpoint_events, "expected at least one checkpoint event for the session"


def test_session_overrides_get_and_patch_round_trip(tmp_path: Path) -> None:
    """GET/PATCH /sessions/{id}/overrides round-trips a single key.

    Verifies that overrides are persisted on the session metadata and
    exposed again via the GET endpoint.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Initially there should be no overrides.
    get_resp = server_mod.get_session_overrides(session_id, app_instance=app)
    assert get_resp == {"overrides": {}}

    # Patch a single override and verify it is persisted.
    server_mod.patch_session_overrides(
        session_id,
        {"key": "reasoning_effort", "value": "high"},
        app_instance=app,
    )

    get_resp2 = server_mod.get_session_overrides(session_id, app_instance=app)
    overrides = get_resp2.get("overrides") or {}
    assert overrides.get("reasoning_effort") == "high"

    # Confirm that the session metadata was updated on disk.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, session = ctx
    md = session.metadata or {}
    stored = md.get("overrides") or {}
    assert stored.get("reasoning_effort") == "high"


def test_session_overrides_patch_bulk_merges_with_existing(tmp_path: Path) -> None:
    """PATCH /sessions/{id}/overrides merges bulk values with existing.

    Starts with an override for one key, then bulk-updates another and
    verifies that both remain in the mapping.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Seed a single-key override.
    server_mod.patch_session_overrides(
        session_id,
        {"key": "enable_reasoning", "value": True},
        app_instance=app,
    )

    # Bulk update another key.
    server_mod.patch_session_overrides(
        session_id,
        {"values": {"reasoning_effort": "medium"}},
        app_instance=app,
    )

    get_resp = server_mod.get_session_overrides(session_id, app_instance=app)
    overrides = get_resp.get("overrides") or {}
    assert overrides.get("enable_reasoning") is True
    assert overrides.get("reasoning_effort") == "medium"


def test_delete_session_override_removes_key_and_preserves_others(tmp_path: Path) -> None:
    """DELETE /sessions/{id}/overrides/{key} removes a single override key."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Seed two overrides.
    server_mod.patch_session_overrides(
        session_id,
        {"values": {"enable_reasoning": True, "reasoning_effort": "high"}},
        app_instance=app,
    )

    # Delete only reasoning_effort.
    server_mod.delete_session_override(session_id, "reasoning_effort", app_instance=app)

    resp = server_mod.get_session_overrides(session_id, app_instance=app)
    overrides = resp.get("overrides") or {}
    assert overrides.get("enable_reasoning") is True
    assert "reasoning_effort" not in overrides


def test_delete_session_override_is_idempotent_for_missing_key(tmp_path: Path) -> None:
    """Deleting a non-existent override key is a no-op."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # No overrides set; deleting a key should be a no-op.
    before = server_mod.get_session_overrides(session_id, app_instance=app)
    server_mod.delete_session_override(session_id, "nonexistent", app_instance=app)
    after = server_mod.get_session_overrides(session_id, app_instance=app)
    assert before == after


def test_get_session_base_config_returns_mapping(tmp_path: Path) -> None:
    """GET /sessions/{id}/config/base exposes base agent config as mapping."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    resp = server_mod.get_session_base_config(session_id, app_instance=app)
    cfg = resp.get("config")
    assert isinstance(cfg, dict)


def test_delete_session_override_removes_key_and_preserves_others(tmp_path: Path) -> None:
    """DELETE /sessions/{id}/overrides/{key} drops only the requested key."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    server_mod.patch_session_overrides(
        session_id,
        {"values": {"enable_reasoning": True, "reasoning_effort": "high"}},
        app_instance=app,
    )

    server_mod.delete_session_override(session_id, "reasoning_effort", app_instance=app)

    get_resp = server_mod.get_session_overrides(session_id, app_instance=app)
    overrides = get_resp.get("overrides") or {}
    assert overrides.get("enable_reasoning") is True
    assert "reasoning_effort" not in overrides


def test_delete_session_override_is_idempotent_when_key_missing(tmp_path: Path) -> None:
    """DELETE /sessions/{id}/overrides/{key} is idempotent for missing keys."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # No overrides set; deleting a non-existent key should not fail.
    resp = server_mod.delete_session_override(session_id, "nonexistent", app_instance=app)
    assert isinstance(resp.get("session"), dict)


def test_checkpoint_cursor_after_final_event(tmp_path: Path) -> None:
    """After a request, cursor_event_id is after the final event.

    The test runs a non-streaming request to completion via the
    background helper and verifies that the checkpoint marker recorded
    for the session has a higher ``event_id`` than the last ``final``
    event and that ``cursor_event_id`` from the messages endpoint
    matches that marker.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello from final", "metadata": None},
        app_instance=app,
    )

    # Run the helper synchronously to drive the non-streaming request.
    server_mod._run_send_request_background(app, session_id, {})

    evs = app.get_event_store().list(session_id=session_id, limit=200)
    final_events = [ev for ev in evs if ev.get("type") == "final"]
    checkpoint_events = [ev for ev in evs if ev.get("type") == "checkpoint"]

    assert final_events, "expected at least one final event for the session"
    assert checkpoint_events, "expected at least one checkpoint event for the session"

    last_final = final_events[-1]
    last_checkpoint = checkpoint_events[-1]

    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except Exception:
            return -1

    assert _to_int(last_checkpoint.get("event_id")) > _to_int(
        last_final.get("event_id")
    )

    resp = server_mod.list_session_messages(session_id, app_instance=app)
    assert resp["cursor_event_id"] == last_checkpoint.get("event_id")


def test_run_send_request_background_merges_session_and_http_overrides(tmp_path: Path) -> None:
    """Background send merges metadata overrides with HTTP overrides.

    The per-session overrides stored in session.metadata["overrides"]
    must be merged with any config_overrides passed via HTTP, with the
    HTTP-provided values taking precedence on conflicts.
    """

    from agent_terminal_app import server as server_mod
    from agent_core import Session

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Attach some per-session overrides directly to the stored session.
    ctx = app.load_session(session_id)
    assert ctx is not None
    core, base_config, session = ctx
    existing_md = session.metadata or {}
    new_md = {
        **existing_md,
        "overrides": {"foo": "session", "both": "session"},
    }
    session_with_overrides = Session(
        session_id=session.session_id,
        messages=session.messages,
        metadata=new_md,
    )
    app.save_session(session_with_overrides)

    captured: dict[str, Any] = {}

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        stream: bool = True,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        captured["overrides"] = overrides_arg
        return []

    # Monkeypatch AgentApplication.send_request.
    app.send_request = _fake_send_request  # type: ignore[assignment]

    # HTTP-provided overrides should be merged on top.
    http_overrides = {"bar": "http", "both": "http"}
    server_mod._run_send_request_background(app, session_id, http_overrides)

    merged = captured.get("overrides") or {}
    assert merged == {"foo": "session", "both": "http", "bar": "http"}


def test_run_send_request_background_uses_session_overrides_when_http_empty(tmp_path: Path) -> None:
    """Background send uses only session overrides when HTTP none provided."""

    from agent_terminal_app import server as server_mod
    from agent_core import Session

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    ctx = app.load_session(session_id)
    assert ctx is not None
    core, base_config, session = ctx
    existing_md = session.metadata or {}
    new_md = {
        **existing_md,
        "overrides": {"alpha": 1, "beta": 2},
    }
    session_with_overrides = Session(
        session_id=session.session_id,
        messages=session.messages,
        metadata=new_md,
    )
    app.save_session(session_with_overrides)

    captured: dict[str, Any] = {}

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        stream: bool = True,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        captured["overrides"] = overrides_arg
        return []

    app.send_request = _fake_send_request  # type: ignore[assignment]

    server_mod._run_send_request_background(app, session_id, {})

    merged = captured.get("overrides") or {}
    assert merged == {"alpha": 1, "beta": 2}


def test_list_session_messages_includes_cursor_event_id_after_request(tmp_path: Path) -> None:
    """GET /sessions/{session_id}/messages returns cursor_event_id.

    The test runs a request to completion using the background helper
    and then verifies that the messages endpoint exposes the
    event_id of the latest checkpoint marker for that session.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_dict = create_resp["session"]
    session_id = session_dict["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello", "metadata": None},
        app_instance=app,
    )

    server_mod._run_send_request_background(app, session_id, {})

    evs = app.get_event_store().list(session_id=session_id, limit=100)
    checkpoint_events = [ev for ev in evs if ev.get("type") == "checkpoint"]
    assert checkpoint_events, "expected at least one checkpoint event for the session"
    last_id = checkpoint_events[-1].get("event_id")
    assert isinstance(last_id, str) and last_id

    resp = server_mod.list_session_messages(session_id, app_instance=app)
    assert resp["cursor_event_id"] == last_id


def test_list_session_messages_exposes_active_request_id_during_and_after_request(
    tmp_path: Path,
) -> None:
    """GET /sessions/{id}/messages exposes active_request_id semantics.

    During an in-flight request, the last checkpoint's request_id
    should be surfaced as active_request_id. After the request has
    completed and a post-completion checkpoint has been recorded, the
    messages endpoint should report active_request_id as null.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    # Create a session and append a single user message.
    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello", "metadata": None},
        app_instance=app,
    )

    # Monkeypatch AgentApplication.send_request to capture the generated
    # events without running a real provider. We simulate the core
    # contract: initial request_started, one session_checkpoint, final,
    # request_completed.
    captured_events: list[Dict[str, Any]] = []

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
    ) -> list[Dict[str, Any]]:
        rid = request_id or "req-test"
        # request_started
        captured_events.append(
            {
                "type": "request_started",
                "session_id": session_id,
                "request_id": rid,
                "stream": bool(stream),
            }
        )
        # internal session_checkpoint carrying the live Session
        captured_events.append(
            {
                "type": "session_checkpoint",
                "session_id": session_id,
                "request_id": rid,
                "session": session_arg,
            }
        )
        # final
        captured_events.append(
            {
                "type": "final",
                "session_id": session_id,
                "request_id": rid,
                "messages": [],
            }
        )
        # request_completed
        captured_events.append(
            {
                "type": "request_completed",
                "session_id": session_id,
                "request_id": rid,
            }
        )
        # The helper iterates over this list.
        return iter(captured_events)  # type: ignore[return-value]

    app.send_request = _fake_send_request  # type: ignore[assignment]

    # Drive the background helper once. This should:
    # - persist a checkpoint with request_id == rid during the request
    # - then record a post-completion checkpoint with request_id None
    server_mod._run_send_request_background(app, session_id, {})

    # Verify that at least one checkpoint exists with a non-null request_id
    # (during the request) and that the last checkpoint has request_id None
    # due to the post-completion marker.
    evs = app.get_event_store().list(session_id=session_id, limit=200)
    checkpoints = [ev for ev in evs if ev.get("type") == "checkpoint"]
    assert checkpoints, "expected checkpoint events for the session"

    request_ids = [ev.get("request_id") for ev in checkpoints]
    assert any(isinstance(rid, str) and rid for rid in request_ids)
    assert checkpoints[-1].get("request_id") is None

    # The messages endpoint should now expose the last checkpoint as the
    # cursor and report active_request_id as null, since the request has
    # completed.
    resp = server_mod.list_session_messages(session_id, app_instance=app)
    assert resp["cursor_event_id"] == checkpoints[-1].get("event_id")
    assert resp.get("active_request_id") is None


def test_events_endpoint_bootstrap_returns_latest_event_id(tmp_path: Path) -> None:
    """GET /events with no filters returns only latest_event_id.

    When called without since_id, session_id, or request_id, the
    events endpoint should not replay the entire history. Instead it
    returns an empty events list plus the latest event_id so that
    clients can start polling from "now".
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Publish a couple of events for distinct sessions.
    s1_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    s1 = s1_resp["session"]["session_id"]
    server_mod.add_message(
        s1,
        {"role": "user", "content": "one", "metadata": None},
        app_instance=app,
    )

    s2_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    s2 = s2_resp["session"]["session_id"]
    server_mod.add_message(
        s2,
        {"role": "user", "content": "two", "metadata": None},
        app_instance=app,
    )

    # Directly call the route function with no filters.
    resp = server_mod.list_events(app_instance=app)
    events_payload = resp.get("events")
    latest_event_id = resp.get("latest_event_id")

    assert isinstance(events_payload, list) and events_payload == []
    # The latest event id should correspond to the last event published
    # in the store.
    assert isinstance(latest_event_id, str) and latest_event_id


def test_events_endpoint_uses_session_cursor_as_default_since_id(tmp_path: Path) -> None:
    """GET /events?session_id=... uses cursor when since_id omitted.

    After a checkpoint is recorded for a session, polling /events for
    that session without an explicit since_id should return only
    events after the cursor.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Add a user message and run a request to completion so that a
    # checkpoint is recorded for this session.
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "before", "metadata": None},
        app_instance=app,
    )
    server_mod._run_send_request_background(app, session_id, {})

    # Capture the cursor and then publish an additional synthetic event
    # for the same session after the checkpoint.
    cursor_id = app.get_session_cursor_event_id(session_id)
    assert isinstance(cursor_id, str) and cursor_id

    extra = app.publish_event({"type": "debug_marker", "session_id": session_id})
    extra_id = extra.get("event_id")
    assert isinstance(extra_id, str) and extra_id

    # Calling /events with only session_id should start from the
    # cursor, returning only the extra event for this session.
    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    returned_ids = {ev.get("event_id") for ev in payload}
    assert extra_id in returned_ids
    # Older events (including the checkpoint itself) should not be
    # included in this batch.
    assert cursor_id not in returned_ids


def test_events_endpoint_compacts_partials(tmp_path: Path) -> None:
    """GET /events omits redundant partials when a final is present.

    When a batch contains both partial and final events for the same
    request, only the final should be returned for that request.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Publish a sequence of partial events followed by a final for the
    # same (session_id, request_id) pair.
    request_id = "req-1"
    app.publish_event(
        {"type": "partial", "session_id": session_id, "request_id": request_id}
    )
    app.publish_event(
        {"type": "partial", "session_id": session_id, "request_id": request_id}
    )
    app.publish_event(
        {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [
                {"role": "assistant", "content": "done", "metadata": {}},
            ],
        }
    )

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    types = [ev.get("type") for ev in payload if ev.get("session_id") == session_id]
    # Final must be present.
    assert "final" in types
    # All partials for this request should have been compacted away.
    assert "partial" not in [
        ev.get("type")
        for ev in payload
        if ev.get("session_id") == session_id and ev.get("request_id") == request_id
    ]


def test_events_endpoint_merges_consecutive_partials(tmp_path: Path) -> None:
    """GET /events merges consecutive partials for the same request.

    When a batch contains only partial events for a request (no
    final yet), consecutive partials should be merged so that callers
    receive a single event with concatenated content/reasoning.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    request_id = "req-merge"
    # Two partials with both reasoning and content pieces.
    app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {
                "role": "assistant",
                "content": "Hello, ",
                "metadata": {"reasoning": "think1 "},
            },
        }
    )
    app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {
                "role": "assistant",
                "content": "world",
                "metadata": {"reasoning": "think2"},
            },
        }
    )

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    # For this request we should see a single merged partial.
    partials = [
        ev
        for ev in payload
        if ev.get("type") == "partial" and ev.get("session_id") == session_id
    ]
    assert len(partials) == 1

    msg = partials[0].get("message") or {}
    md = msg.get("metadata") or {}
    assert msg.get("content") == "Hello, world"
    assert md.get("reasoning") == "think1 think2"


def test_events_endpoint_respects_compaction_flags(tmp_path: Path) -> None:
    """Disabling compaction flags leaves event batches unchanged.

    This test toggles the AgentApplication compaction flags to verify
    that they can be used to disable dropping and merging behavior for
    debugging and tests.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]
    request_id = "req-flags"

    # Publish two partials and a final.
    ev1 = app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {"role": "assistant", "content": "a", "metadata": {}},
        }
    )
    ev2 = app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {"role": "assistant", "content": "b", "metadata": {}},
        }
    )
    ev3 = app.publish_event(
        {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [
                {"role": "assistant", "content": "ab", "metadata": {}},
            ],
        }
    )

    # Disable all compaction.
    app._enable_event_compaction = False

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    ids = [ev.get("event_id") for ev in payload]
    assert ids[:3] == [ev1.get("event_id"), ev2.get("event_id"), ev3.get("event_id")]


def test_events_endpoint_compacts_tool_partials(tmp_path: Path) -> None:
    """GET /events drops tool_partial events once tool_results is present."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]
    request_id = "req-tools"
    tool_call_id = "call-1"

    # Two streaming tool_partial chunks followed by a final tool_results.
    app.publish_event(
        {
            "type": "tool_partial",
            "session_id": session_id,
            "request_id": request_id,
            "tool_call_id": tool_call_id,
            "phase": "stream",
            "payload": {"part": "alpha "},
        }
    )
    app.publish_event(
        {
            "type": "tool_partial",
            "session_id": session_id,
            "request_id": request_id,
            "tool_call_id": tool_call_id,
            "phase": "stream",
            "payload": {"part": "beta"},
        }
    )
    app.publish_event(
        {
            "type": "tool_results",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [
                {
                    "role": "tool",
                    "content": "final",
                    "metadata": {"tool_call_id": tool_call_id},
                }
            ],
        }
    )

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    types = [
        ev.get("type")
        for ev in payload
        if ev.get("session_id") == session_id and ev.get("request_id") == request_id
    ]
    assert "tool_results" in types
    assert "tool_partial" not in types


def test_events_endpoint_preserves_inflight_partials(tmp_path: Path) -> None:
    """GET /events keeps in-flight partials when no final/results exist.

    For requests that have not yet produced a final or tool_results
    event, partial and tool_partial events should not be dropped by the
    compaction pass.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]
    request_id = "req-inflight"

    app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {"role": "assistant", "content": "a", "metadata": {}},
        }
    )
    app.publish_event(
        {
            "type": "tool_partial",
            "session_id": session_id,
            "request_id": request_id,
            "tool_call_id": "tc1",
            "phase": "stream",
            "payload": {"part": "x"},
        }
    )

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    types = [
        ev.get("type")
        for ev in payload
        if ev.get("session_id") == session_id and ev.get("request_id") == request_id
    ]
    # Both partial and tool_partial should still be present (they may
    # be merged with any additional partials, but not dropped).
    assert "partial" in types
    assert "tool_partial" in types


def test_list_sessions_endpoint_returns_metadata_for_created_sessions(tmp_path: Path) -> None:
    """GET /sessions returns basic metadata for stored sessions.

    The test creates two sessions with user messages via the existing
    create_session and add_message endpoints, then verifies that the
    list_sessions endpoint returns entries for both with appropriate
    previews and metadata.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Create two sessions with a single user message each.
    create1 = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id1 = create1["session"]["session_id"]
    server_mod.add_message(
        session_id1,
        {"role": "user", "content": "first session hello", "metadata": None},
        app_instance=app,
    )

    create2 = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id2 = create2["session"]["session_id"]
    server_mod.add_message(
        session_id2,
        {"role": "user", "content": "second session hi", "metadata": None},
        app_instance=app,
    )

    resp = server_mod.list_sessions(app_instance=app)
    sessions = resp["sessions"]

    # Both sessions should be present with non-empty previews.
    ids = {entry["session_id"] for entry in sessions}
    assert session_id1 in ids and session_id2 in ids

    preview_by_id = {entry["session_id"]: entry["preview"] for entry in sessions}
    assert preview_by_id[session_id1] == "first session hello"
    assert preview_by_id[session_id2] == "second session hi"

    # Metadata should also be included for each session (at minimum the
    # agent_id stored by the application layer).
    metadata_by_id = {entry["session_id"]: entry.get("metadata") for entry in sessions}
    assert isinstance(metadata_by_id[session_id1], dict)
    assert isinstance(metadata_by_id[session_id2], dict)


def test_list_sessions_endpoint_uses_cached_entries_when_unchanged(tmp_path: Path) -> None:
    """GET /sessions reuses cached summaries when files are unchanged.

    This test exercises the caching layer indirectly by calling the
    ``list_sessions`` route multiple times and updating only one
    session between calls. The endpoint must reflect changes to the
    modified session while keeping previews for unchanged sessions
    intact.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Create two sessions with a single user message each.
    create1 = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id1 = create1["session"]["session_id"]
    server_mod.add_message(
        session_id1,
        {"role": "user", "content": "first session before", "metadata": None},
        app_instance=app,
    )

    create2 = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id2 = create2["session"]["session_id"]
    server_mod.add_message(
        session_id2,
        {"role": "user", "content": "second session before", "metadata": None},
        app_instance=app,
    )

    # Initial listing populates the cache.
    first = server_mod.list_sessions(app_instance=app)
    sessions_first = first["sessions"]
    preview_first = {entry["session_id"]: entry["preview"] for entry in sessions_first}

    assert preview_first[session_id1] == "first session before"
    assert preview_first[session_id2] == "second session before"

    # Update only the second session on disk so that its file mtime and
    # preview change. This simulates an external modification and
    # ensures that the caching layer notices the newer mtime.
    import json

    session_path2 = session_root / f"{session_id2}.json"
    raw = json.loads(session_path2.read_text(encoding="utf-8"))
    messages = raw.get("messages") or []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            msg["content"] = "second session after"
            break
    session_path2.write_text(json.dumps(raw), encoding="utf-8")

    # Force a strictly newer mtime for environments with coarse
    # timestamp resolution.
    stat_before = session_path2.stat()
    os.utime(session_path2, (stat_before.st_mtime + 2, stat_before.st_mtime + 2))

    second = server_mod.list_sessions(app_instance=app)
    sessions_second = second["sessions"]
    preview_second = {entry["session_id"]: entry["preview"] for entry in sessions_second}

    # The first session was not modified; its preview should remain the
    # same across calls.
    assert preview_second[session_id1] == "first session before"

    # The second session was updated; the preview should reflect the
    # latest first user message.
    assert preview_second[session_id2] == "second session after"


def test_list_sessions_endpoint_strips_native_messages_from_metadata(tmp_path: Path) -> None:
    """GET /sessions does not include heavy native_messages metadata.

    Some providers store a full copy of the conversation under
    ``metadata.native_messages``. This test ensures that the sessions
    list endpoint strips that field so the response stays small.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    # Patch the on-disk session file to include a heavy native_messages
    # field under metadata.
    import json

    session_path = session_root / f"{session_id}.json"
    raw = json.loads(session_path.read_text(encoding="utf-8"))
    meta = raw.get("metadata") or {}
    if not isinstance(meta, dict):
      meta = {}
    meta["native_messages"] = [
      {"role": "system", "content": "x" * 1000},
      {"role": "user", "content": "y" * 1000},
    ]
    raw["metadata"] = meta
    session_path.write_text(json.dumps(raw), encoding="utf-8")

    resp = server_mod.list_sessions(app_instance=app)
    sessions = resp["sessions"]
    meta_by_id = {
      entry["session_id"]: entry.get("metadata") for entry in sessions
    }
    assert session_id in meta_by_id
    meta_out = meta_by_id[session_id]
    assert isinstance(meta_out, dict)
    assert "native_messages" not in meta_out


def test_checkpoint_cursor_after_message_appended(tmp_path: Path) -> None:
    """After appending a message, cursor_event_id is after the event.

    The test appends a single user message via the HTTP-style route
    functions, then verifies that:

    * A ``message_appended`` event exists for the session.
    * A subsequent ``checkpoint`` event exists with a higher
      ``event_id``.
    * ``GET /sessions/{id}/messages`` exposes ``cursor_event_id``
      equal to that checkpoint's ``event_id``.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello", "metadata": None},
        app_instance=app,
    )

    # Inspect raw events for this session.
    evs = app.get_event_store().list(session_id=session_id, limit=100)
    appended = [ev for ev in evs if ev.get("type") == "message_appended"]
    checkpoints = [ev for ev in evs if ev.get("type") == "checkpoint"]

    assert appended, "expected message_appended event"
    assert checkpoints, "expected checkpoint event after append"

    last_appended = appended[-1]
    last_checkpoint = checkpoints[-1]

    assert "session" not in last_appended
    assert isinstance(last_appended.get("index"), int)
    assert isinstance(last_appended.get("message"), dict)

    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except Exception:
            return -1

    assert _to_int(last_checkpoint.get("event_id")) > _to_int(
        last_appended.get("event_id")
    )

    # The messages endpoint should expose the same cursor_event_id.
    resp = server_mod.list_session_messages(session_id, app_instance=app)
    assert resp["cursor_event_id"] == last_checkpoint.get("event_id")


def test_add_message_accepts_multipart_content_and_allows_empty_content(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    multipart = [
        {
            "type": "image",
            "content": {"url": "data:image/png;base64,AA=="},
            "metadata": {"filename": "a.png"},
        }
    ]

    resp = server_mod.add_message(
        session_id,
        {"role": "user", "content": "", "multipartContent": multipart, "metadata": None},
        app_instance=app,
    )

    session = resp["session"]
    last = session["messages"][-1]
    assert last["role"] == "user"
    assert last["content"] == ""
    assert last.get("multipartContent") == multipart

    evs = app.get_event_store().list(session_id=session_id, limit=100)
    appended = [ev for ev in evs if ev.get("type") == "message_appended"]
    assert appended, "expected message_appended event"
    msg = appended[-1].get("message")
    assert isinstance(msg, dict)
    assert msg.get("multipartContent") == multipart


def test_add_message_rejects_empty_content_without_multipart(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    with pytest.raises(HTTPException) as excinfo:
        server_mod.add_message(
            session_id,
            {"role": "user", "content": "   ", "metadata": None},
            app_instance=app,
        )

    assert excinfo.value.status_code == 400


def test_list_session_messages_endpoint_supports_slice_bounds(tmp_path: Path) -> None:
    """GET /sessions/{session_id}/messages lists and slices messages.

    The test creates a session with three user messages and verifies that
    the endpoint returns the full history as well as a negative-index
    slice selecting the last two messages.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    for content in ["one", "two", "three"]:
        server_mod.add_message(
            session_id,
            {"role": "user", "content": content, "metadata": None},
            app_instance=app,
        )

    # Full history
    full = server_mod.list_session_messages(session_id, app_instance=app)
    full_messages = full["messages"]
    assert [m["message"]["content"] for m in full_messages] == ["one", "two", "three"]

    # cursor_event_id is present (may be null if no cursor yet)
    assert "cursor_event_id" in full

    # Last two messages using a negative start index
    last_two = server_mod.list_session_messages(session_id, start=-2, app_instance=app)
    last_two_messages = last_two["messages"]
    assert [m["index"] for m in last_two_messages] == [1, 2]
    assert [m["message"]["content"] for m in last_two_messages] == ["two", "three"]


def test_cancel_request_endpoint_triggers_cancellation(tmp_path: Path) -> None:
    """POST /requests/{request_id}/cancel cooperates with send_request.

    The test schedules a cancellation for a specific request id and then
    runs AgentApplication.send_request with the same id, asserting that a
    ``request_cancelled`` event is produced instead of a normal final
    response.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Prepare a simple session with one user message.
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello", metadata=None, config=base_config)

    request_id = "test-request-id-123"

    # Request cancellation via the server endpoint before starting the call.
    server_mod.cancel_request(request_id, app_instance=app)

    events = list(
        app.send_request(
            core,
            session,
            base_config,
            overrides=None,
            stream=False,
            request_id=request_id,
        )
    )

    kinds = {ev.get("type") for ev in events}
    assert "request_started" in kinds
    assert "request_cancelled" in kinds
    assert "final" not in kinds


def test_get_api_data_returns_initial_state() -> None:
    """GET /api/data returns the initial DataStore contents.

    This exercises the FastAPI layer end-to-end via TestClient while
    resetting the module-level ``_bonjour_data_store`` to a known
    starting value.
    """

    from agent_terminal_app import server as server_mod
    from agent_terminal_app.server import app as fastapi_app

    # Reset the global store to a predictable state for this test.
    server_mod._bonjour_data_store = server_mod.DataStore({"message": "Initial data", "count": 0})

    client = TestClient(fastapi_app)
    resp = client.get("/api/data")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"] == {"message": "Initial data", "count": 0}
    ts = body.get("timestamp")
    assert isinstance(ts, str) and ts.endswith("Z")


def test_put_api_data_updates_store() -> None:
    """PUT /api/data merges into the store and subsequent GET reflects it."""

    from agent_terminal_app import server as server_mod
    from agent_terminal_app.server import app as fastapi_app

    server_mod._bonjour_data_store = server_mod.DataStore({"message": "Initial data", "count": 0})

    client = TestClient(fastapi_app)

    update = {"count": 5, "extra": "value"}
    resp = client.put("/api/data", json=update)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    updated = body["updated"]
    assert updated["message"] == "Initial data"
    assert updated["count"] == 5
    assert updated["extra"] == "value"

    # A subsequent GET should return the same updated mapping.
    resp2 = client.get("/api/data")
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["data"] == updated


def test_get_api_hello_matches_python_bonjour_shape() -> None:
    """GET /api/hello exposes the expected greeting shape."""

    from agent_terminal_app.server import app as fastapi_app

    client = TestClient(fastapi_app)
    resp = client.get("/api/hello")
    assert resp.status_code == 200

    body = resp.json()
    assert body["message"] == "Hello from Bonjour Server!"
    assert body["method"] == "GET"
    ts = body.get("timestamp")
    assert isinstance(ts, str) and ts.endswith("Z")


# ---------------------------------------------------------------------------
# HTTP integration test using FastAPI TestClient
# ---------------------------------------------------------------------------


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")

REPO_TMP_DIR = Path(__file__).resolve().parents[3] / "tmp"
REPO_TMP_DIR.mkdir(parents=True, exist_ok=True)

def _which(cmd: str) -> Optional[str]:
    import shutil

    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120):
    import subprocess

    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_ollama_model() -> None:
    """Ensure that Ollama and the tools-capable model are available, else skip."""

    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping HTTP Ollama tools test")
    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    try:
        cp = _run(["ollama", "pull", MODEL_TOOLS], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_TOOLS}: {msg}")
    except Exception as e:  # pragma: no cover - environment dependent
        pytest.skip(f"could not pull model {MODEL_TOOLS}: {e}")


@pytest.mark.ollama
def test_http_flow_with_tools_and_reasoning(ensure_ollama_model: None, tmp_path: Path) -> None:
    """End-to-end HTTP flow exercising tools and reasoning.

    The flow uses the real FastAPI app with config_openrouter_app_layer.json
    via TestClient:

    1. Create a session with a system message.
    2. Add a user message.
    3. Inject a pending shell tool call as an assistant message.
    4. Start /send in a background thread with a small artificial delay.
    5. Poll /events while the request is in progress.
    6. Verify that tool events and reasoning metadata are present.
    7. List messages and ensure user, assistant, and tool messages exist.
    """

    from agent_terminal_app import server as server_mod

    # Build an application instance using an Ollama tools config similar to
    # the core application-layer integration tests.
    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = tmp_path / "config_ollama_tools_app.json"

    ollama_cfg = {
        "providers": {
            "ollama_tools": {
                "provider": "openai_compatible",
                "model": MODEL_TOOLS,
                "base_url": OPENAI_BASE_URL,
                "timeout": 180,
                # Tool configuration, forwarded to FileReaderTool
                "allowed_paths": ["."],
                "max_file_size": 1024 * 1024,
            }
        },
        "plugins": [
            "plugins.openai_provider.OpenAICompatibleProvider",
            "plugins.openai_tools_extension.OpenAIToolsExtension",
            "plugins.ollama_thinking_extension.OllamaThinkingExtension",
            "plugins.file_reader_tool.FileReaderTool",
        ],
        "agents": {
            "default": {"provider": "ollama_tools"},
        },
    }

    config_path.write_text(__import__("json").dumps(ollama_cfg), encoding="utf-8")
    session_root = tmp_path / "sessions"

    event_store = InMemoryEventStore()
    app_instance = AgentApplication(str(config_path), str(session_root), event_store=event_store)

    # Wire the custom AgentApplication into the FastAPI app via dependency override.
    from agent_terminal_app.server import app, get_agent_app

    app.dependency_overrides[get_agent_app] = lambda: app_instance
    client = TestClient(app)

    try:
        # 1) Create a new session.
        system_message = (
            "You are a helpful assistant. When the user asks about file contents, "
            "you MUST use the read_file tool to inspect the file and then answer. "
            "Never guess. You also include brief reasoning in your metadata."
        )

        resp = client.post("/sessions", json={"agent_id": "default", "system_message": system_message})
        assert resp.status_code == 200
        session_id = resp.json()["session"]["session_id"]

        # 2) Add a user message.
        # Prepare a small temp file under the repository tmp directory so that
        # allowed_paths ["."] covers it.
        import tempfile

        with tempfile.NamedTemporaryFile("w+", delete=False, dir=REPO_TMP_DIR) as tf:
            tf.write("hello from ollama tools over HTTP")
            tf.flush()
            file_path = tf.name

        user_message = (
            "Use the tools to read this file and tell me its exact contents: "
            f"{file_path}. Do not answer without using tools."
        )
        resp = client.post(
            f"/sessions/{session_id}/messages",
            json={"role": "user", "content": user_message, "metadata": None},
        )
        assert resp.status_code == 200

        # 3) Start /send in a background thread with a small artificial delay
        # configured via the DelayExtension so that the request remains in
        # progress long enough for us to poll /events while it is running.
        overrides = {
            "allowed_paths": ["."],
            "working_directory": ".",
            "enable_delay_extension": True,
            "delay_seconds": 2.0,
        }

        send_resp_container: dict[str, Any] = {}

        def _run_send() -> None:
            r = client.post(f"/sessions/{session_id}/send", json={"config_overrides": overrides})
            send_resp_container["response"] = r

        send_thread = threading.Thread(target=_run_send)
        send_thread.start()

        # 5) Poll /events while the request is in progress.
        seen_event_types: set[str] = set()
        seen_tool_event = False
        seen_reasoning_in_final = False
        last_event_id: Optional[str] = None

        deadline = time.time() + 60.0
        while time.time() < deadline:
            params: Dict[str, Any] = {"session_id": session_id}
            if last_event_id is not None:
                params["since_id"] = last_event_id

            ev_resp = client.get("/events", params=params)
            assert ev_resp.status_code == 200
            batch = ev_resp.json().get("events", [])

            if batch:
                last_event_id = batch[-1].get("event_id") or last_event_id

            for ev in batch:
                etype = ev.get("type")
                if isinstance(etype, str):
                    seen_event_types.add(etype)

                if etype in {"tool_calls", "tool_results", "tool_partial"}:
                    seen_tool_event = True

                if etype == "final":
                    messages = ev.get("messages") or []
                    if messages:
                        last_msg = messages[-1]
                        md = last_msg.get("metadata") or {}
                        reasoning = md.get("reasoning")
                        if isinstance(reasoning, str) and reasoning.strip():
                            seen_reasoning_in_final = True

            if "final" in seen_event_types and "request_completed" in seen_event_types:
                break

            time.sleep(0.5)

        send_thread.join(timeout=10.0)
        assert not send_thread.is_alive(), "send_request thread did not finish in time"

        send_resp = send_resp_container.get("response")
        assert send_resp is not None
        assert send_resp.status_code == 200

        # 6) Basic assertions about the event stream.
        assert "request_started" in seen_event_types
        assert "request_completed" in seen_event_types
        assert "final" in seen_event_types
        assert seen_tool_event, "expected at least one tool-related event"
        assert seen_reasoning_in_final, "expected reasoning in final assistant metadata"

        # 7) List messages for the finished session and ensure history looks reasonable.
        list_resp = client.get(f"/sessions/{session_id}/messages")
        assert list_resp.status_code == 200
        messages = list_resp.json().get("messages", [])

        roles = [entry["message"]["role"] for entry in messages]
        assert "user" in roles
        assert "assistant" in roles
        assert "tool" in roles

    finally:
        # Remove overrides so other tests are unaffected.
        from agent_terminal_app.server import app as shared_app

        shared_app.dependency_overrides.clear()


def test_update_message_endpoint_modifies_content_and_emits_event(tmp_path: Path) -> None:
    """PATCH /sessions/{session_id}/messages/{index} updates message content.

    The test creates a session with a system and two user messages,
    modifies the last message via the endpoint, and verifies both the
    stored session and the emitted ``message_modified`` event.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Create a session and add a system plus two user messages.
    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "system", "content": "system", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "one", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "two", "metadata": None},
        app_instance=app,
    )

    # Modify the last message using a negative index.
    resp = server_mod.update_message(
        session_id,
        -1,
        {"content": "two modified"},
        app_instance=app,
    )
    session_dict = resp["session"]
    contents = [m["content"] for m in session_dict["messages"]]
    assert contents == ["system", "one", "two modified"]

    # Check that a message_modified event was recorded with the expected index.
    evs = app.get_event_store().list(session_id=session_id, limit=100)
    modified = [ev for ev in evs if ev.get("type") == "message_modified"]
    assert modified, "expected at least one message_modified event"
    last_ev = modified[-1]
    assert last_ev["index"] == 2
    assert last_ev["content"] == "two modified"
    assert "session" not in last_ev
    assert isinstance(last_ev.get("message"), dict)


def test_delete_messages_endpoint_supports_indices_range_and_last(tmp_path: Path) -> None:
    """DELETE /sessions/{session_id}/messages handles all deletion modes.

    The test exercises the ``indices``, ``range``, and ``last`` shapes
    and verifies both the resulting history and the reported indices.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Session with a system message and three user messages.
    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "system", "content": "system", "metadata": None},
        app_instance=app,
    )
    for content in ["one", "two", "three"]:
        server_mod.add_message(
            session_id,
            {"role": "user", "content": content, "metadata": None},
            app_instance=app,
        )

    # 1) Delete a single message by explicit index (remove "two").
    resp_indices = server_mod.delete_messages(
        session_id,
        {"indices": [2]},
        app_instance=app,
    )
    session_after_indices = resp_indices["session"]
    contents_indices = [m["content"] for m in session_after_indices["messages"]]
    assert contents_indices == ["system", "one", "three"]
    assert resp_indices["deleted_indices"] == [2]

    # 2) Delete specific indices (remove "one" and "three").
    resp_range = server_mod.delete_messages(
        session_id,
        {"indices": [1, 2]},
        app_instance=app,
    )
    session_after_range = resp_range["session"]
    contents_range = [m["content"] for m in session_after_range["messages"]]
    assert contents_range == ["system"]
    assert sorted(resp_range["deleted_indices"]) == [1, 2]

    # 3) Recreate messages and exercise range + last forms together.
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "one", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "two", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "three", "metadata": None},
        app_instance=app,
    )

    # Delete a slice [1:3) -> "one", "two".
    resp_slice = server_mod.delete_messages(
        session_id,
        {"range": {"start": 1, "end": 3}},
        app_instance=app,
    )
    contents_slice = [m["content"] for m in resp_slice["session"]["messages"]]
    assert contents_slice == ["system", "three"]
    assert resp_slice["deleted_indices"] == [1, 2]

    # Delete the last remaining user message via ``last``.
    resp_last = server_mod.delete_messages(
        session_id,
        {"last": 1},
        app_instance=app,
    )
    contents_last = [m["content"] for m in resp_last["session"]["messages"]]
    assert contents_last == ["system"]
    assert resp_last["deleted_indices"] == [1]


def test_fork_session_endpoint_creates_truncated_copy(tmp_path: Path) -> None:
    """POST /sessions/{session_id}/fork creates a new session with sliced history."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    source_session = create["session"]
    source_id = source_session["session_id"]

    # Add a system message and three user messages to the source session.
    server_mod.add_message(
        source_id,
        {"role": "system", "content": "system", "metadata": None},
        app_instance=app,
    )
    for content in ["one", "two", "three"]:
        server_mod.add_message(
            source_id,
            {"role": "user", "content": content, "metadata": None},
            app_instance=app,
        )

    # Fork up to and including index 2 ("two").
    fork_resp = server_mod.fork_session(
        source_id,
        {"index": 2},
        app_instance=app,
    )
    forked = fork_resp["session"]
    forked_id = forked["session_id"]

    assert forked_id != source_id
    assert fork_resp["source_session_id"] == source_id

    forked_contents = [m["content"] for m in forked["messages"]]
    assert forked_contents == ["system", "one", "two"]

    # A session_created event for the fork should be present.
    evs = app.get_event_store().list(session_id=forked_id, limit=20)
    created = [ev for ev in evs if ev.get("type") == "session_created"]
    assert created, "expected a session_created event for forked session"
    assert created[-1].get("source_session_id") == source_id
    assert created[-1].get("fork_upto_index") == 2
    assert "session" not in created[-1]


def test_agent_endpoints_list_and_switch_agents(tmp_path: Path) -> None:
    """GET /agents and /sessions/{id}/agent + PATCH switching behaviour."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # List configured agents.
    agents_resp = server_mod.list_agents(app_instance=app)
    agents = agents_resp["agents"]
    assert "default" in agents
    assert "alt" in agents

    # Create a session using the default agent.
    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    # The session's agent endpoint should report "default".
    agent_resp = server_mod.get_session_agent(session_id, app_instance=app)
    assert agent_resp["agent_id"] == "default"

    # Switch to the "alt" agent.
    switch_resp = server_mod.update_session_agent(
        session_id,
        {"agent_id": "alt"},
        app_instance=app,
    )
    assert switch_resp["agent_id"] == "alt"

    # The session metadata should reflect the new agent id.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, session = ctx
    md = session.metadata or {}
    assert md.get("agent_id") == "alt"


def test_get_session_agent_returns_value_even_if_agent_is_unknown(tmp_path: Path) -> None:
    """GET /sessions/{id}/agent should not require agent config resolution."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    session_path = session_root / f"{session_id}.json"
    raw = json.loads(session_path.read_text(encoding="utf-8"))
    metadata = raw.get("metadata")
    assert isinstance(metadata, dict)
    metadata["agent_id"] = "missing-agent"
    session_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    agent_resp = server_mod.get_session_agent(session_id, app_instance=app)
    assert agent_resp["agent_id"] == "missing-agent"


def test_list_session_messages_succeeds_when_agent_is_unknown(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod
    from agent_core import AgentCore

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    session = core.add_message(session, "user", "hello", None, base_config)
    app.save_session(session)
    session_id = session.session_id

    session_path = session_root / f"{session_id}.json"
    raw = json.loads(session_path.read_text(encoding="utf-8"))
    metadata = raw.get("metadata")
    assert isinstance(metadata, dict)
    metadata["agent_id"] = "missing-agent"
    session_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    resp = server_mod.list_session_messages(session_id, app_instance=app)
    messages = resp.get("messages") or []
    assert len(messages) == 1
    assert messages[0]["message"]["content"] == "hello"


def test_send_request_returns_400_when_agent_is_unknown(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    session_path = session_root / f"{session_id}.json"
    raw = json.loads(session_path.read_text(encoding="utf-8"))
    metadata = raw.get("metadata")
    assert isinstance(metadata, dict)
    metadata["agent_id"] = "missing-agent"
    session_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    with pytest.raises(server_mod.HTTPException) as excinfo:
        server_mod.send_request(session_id, app_instance=app)
    assert excinfo.value.status_code == 400
    assert "Unknown agent_id" in str(excinfo.value.detail)




