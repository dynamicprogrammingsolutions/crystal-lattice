"""Unit tests for :mod:`plugins.session_timestamp_meta_app`.

These tests exercise the SessionTimestampMetaAppPlugin UI schema and
its ``trigger == "session_list"`` action that computes
``session_created_at`` and ``session_updated_at`` fields.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from plugins.session_timestamp_meta_app import (  # noqa: F401
    SessionTimestampMetaAppPlugin,
)


def _make_config_with_timestamp_meta(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": {
            "providers": [
                "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            ],
            "features": [],
            "tools": [],
            "extensions": [],
        },
        "agents": {
            "default": {"provider": "echo"},
        },
        "application_plugins": [
            "plugins.session_timestamp_meta_app.SessionTimestampMetaAppPlugin",
        ],
        "application": {},
    }

    path = tmp_path / "config_session_timestamp_meta.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config_with_timestamp_meta(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_session_timestamp_meta_ui_schema_includes_created_and_updated(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    elements = app.get_application_ui_schema()
    fields = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "session_timestamp_meta"
        and el.get("ui_type") == "session_list_field"
        and el.get("role") == "meta"
    ]

    assert fields, "expected session_list_field entries for timestamp meta"

    by_data = {f.get("data"): f for f in fields}
    assert "session_updated_at" in by_data
    assert "session_created_at" in by_data

    for key in ("session_updated_at", "session_created_at"):
        field = by_data[key]
        md = field.get("metadata") or {}
        assert md.get("format") == "datetime"


def _make_session_with_timestamps(app: AgentApplication, timestamps: List[str]) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    from agent_core import Message

    messages: List[Message] = []
    for idx, ts in enumerate(timestamps):
        md: Dict[str, Any] = {"timestamp": ts}
        messages.append(Message(role="user", content=f"m{idx}", metadata=md))

    from agent_core import Session as CoreSession

    session = CoreSession(session_id=session.session_id, messages=messages, metadata=session.metadata)
    app.save_session(session)
    return session.session_id


def test_session_timestamp_meta_action_computes_created_and_updated(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    # Build a session with known timestamps.
    ts_values = [
        "2025-01-01T00:00:00+00:00",
        "2025-01-02T12:00:00+00:00",
        "2025-01-03T06:00:00+00:00",
    ]
    session_id = _make_session_with_timestamps(app, ts_values)

    # Execute the session_list action directly.
    result = app.execute_application_action(
        "session_timestamp_meta",
        "compute_session_time_meta",
        {"session_id": session_id},
    )

    fields = result.get("session_list_fields") or {}
    created = fields.get("session_created_at")
    updated = fields.get("session_updated_at")

    assert isinstance(created, (int, float))
    assert isinstance(updated, (int, float))
    # The created timestamp should be earlier than the updated timestamp.
    assert created < updated


def test_session_timestamp_meta_action_uses_modified_when_missing(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    # Create a session without message-level timestamps.
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)
    session = core.add_message(session, "user", "hello", None, base_config)
    app.save_session(session)

    # Simulate a session summary with a known modified timestamp.
    fake_modified = 1_700_000_000.0

    result = app.execute_application_action(
        "session_timestamp_meta",
        "compute_session_time_meta",
        {
            "session_id": session.session_id,
            "session_summary": {"modified": fake_modified},
        },
    )

    fields = result.get("session_list_fields") or {}
    created = fields.get("session_created_at")
    updated = fields.get("session_updated_at")

    assert created == fake_modified
    assert updated == fake_modified
