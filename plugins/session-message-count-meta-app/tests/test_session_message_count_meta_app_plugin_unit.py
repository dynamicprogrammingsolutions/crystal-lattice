"""Unit tests for :mod:`session_message_count_meta_app`.

These tests exercise the SessionMessageCountMetaAppPlugin directly via the
application-layer ``AgentApplication.execute_application_action`` helper.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from session_message_count_meta_app import SessionMessageCountMetaAppPlugin  # noqa: F401


def _make_config_with_message_count(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "session_message_count_meta_app.SessionMessageCountMetaAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }

    path = tmp_path / "config_session_message_count_meta.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config_with_message_count(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    for text in contents:
        session = core.add_message(session, "user", text, None, base_config)

    app.save_session(session)
    return session.session_id


def test_compute_session_message_count_meta_returns_expected_count(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["one", "two", "three"])

    result = app.execute_application_action(
        plugin_id="session_message_count_meta",
        action_id="compute_session_message_count_meta",
        params={"session_id": session_id},
    )

    fields = result.get("session_list_fields") or {}
    assert fields.get("message_count") == 3


def test_session_message_count_meta_ui_schema_includes_meta_field(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    elements = app.get_application_ui_schema()

    # Expect a meta field with data "message_count".
    meta_fields = [
        e
        for e in elements
        if e.get("plugin") == "session_message_count_meta"
        and e.get("ui_type") == "session_list_field"
        and e.get("data") == "message_count"
    ]

    assert meta_fields, "expected a session_list_field for message_count"
