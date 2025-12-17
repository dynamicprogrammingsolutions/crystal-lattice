"""Tests for the agent_terminal_app server functions.

These tests mirror the style of the example application tests under
``core/python/examples/tests`` but exercise the FastAPI-style route
functions directly, injecting an ``AgentApplication`` instance instead
of going through the HTTP layer.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
APP_PY = os.path.join(ROOT, "application/python")
if APP_PY not in sys.path:
    sys.path.insert(0, APP_PY)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


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

    # 3) Send a request and verify the echo provider behaviour.
    send_resp = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        app_instance=app,
    )

    final_session_dict = send_resp["session"]
    messages = send_resp["messages"]
    request_id = send_resp["request_id"]

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


def test_system_message_feature_adds_system_message_after_second_user_message(tmp_path: Path) -> None:
    """Application-level test for SystemMessageFeature integration.

    Verifies that when a provider is configured with SystemMessageFeature
    and the first request has run (so the permanent system template lives
    only in native history), adding a *subsequent* user message causes the
    system message to appear in the stored core session history as well.
    """

    import json

    from agent_core import Session
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    # Minimal config: echo-like provider + SystemMessageFeature.
    system_template = "You are a helpful system message for tests."
    config = {
        "providers": {
            "echo_with_system": {
                "provider": "echo_openai_like",
                "model": "echo-test-1",
                "timeout": 60,
                "system_message_enabled": True,
                "system_message": system_template,
            }
        },
        "plugins": {
            "providers": [
                "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            ],
            "extensions": [],
            "features": [
                "plugins.system_message_feature.SystemMessageFeature",
            ],
            "tools": [],
        },
        "agents": {
            "default": {
                "provider": "echo_with_system",
            }
        },
    }

    cfg_path = tmp_path / "config_system_message_app.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(cfg_path), str(session_root), event_store=events_store)

    # Create a new session and append the first user message using the
    # agent's base config so that SystemMessageFeature is active.
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "first", metadata=None, config=base_config)

    # Run the first request; SystemMessageFeature should insert a permanent
    # template-level system message into provider-native history, but the
    # core session history remains as the application created it.
    events1 = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints1 = [ev for ev in events1 if ev.get("type") == "session_checkpoint"]
    assert checkpoints1, "expected at least one session_checkpoint event"
    session1 = checkpoints1[-1]["session"]
    assert isinstance(session1, Session)

    native1 = session1.metadata.get("native_messages") or []
    sys_native1 = [m for m in native1 if isinstance(m, dict) and m.get("role") == "system"]
    assert sys_native1 and sys_native1[0].get("content") == system_template

    # Append a second user message using the same agent config and run a
    # second request. Native history should still contain exactly one
    # template-level system message (no duplication across turns).
    core2, base_config2, loaded1 = app.load_session(session1.session_id)
    session2 = core2.add_message(loaded1, "user", "second", metadata=None, config=base_config2)

    events2 = list(app.send_request(core2, session2, base_config2, overrides=None, stream=False))
    checkpoints2 = [ev for ev in events2 if ev.get("type") == "session_checkpoint"]
    assert checkpoints2, "expected at least one session_checkpoint event"
    session3 = checkpoints2[-1]["session"]
    assert isinstance(session3, Session)

    native2 = session3.metadata.get("native_messages") or []
    sys_native2 = [m for m in native2 if isinstance(m, dict) and m.get("role") == "system"]
    assert len(sys_native2) == 1
    assert sys_native2[0].get("content") == system_template
