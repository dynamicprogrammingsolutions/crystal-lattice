"""Unit tests for :mod:`session_pinned_app` application plugin.

These tests exercise the SessionPinnedAppPlugin directly via the
application-layer ``AgentApplication.execute_application_action`` helper.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from session_pinned_app import SessionPinnedAppPlugin  # noqa: F401


def _get_mutations(result: Dict[str, Any]) -> Dict[str, Any]:
    mutations = result.get("mutations")
    return mutations if isinstance(mutations, dict) else {}


def _make_config_with_session_pinned(
    tmp_path: Path,
    *,
    metadata_key: str = "pinned",
) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "session_pinned_app.SessionPinnedAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "session_pinned_metadata_key": metadata_key,
        },
    }

    path = tmp_path / "config_session_pinned.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(
    tmp_path: Path,
    *,
    metadata_key: str = "pinned",
) -> AgentApplication:
    config_path = _make_config_with_session_pinned(
        tmp_path,
        metadata_key=metadata_key,
    )
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _create_session(app: AgentApplication) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    app.save_session(session)
    return session.session_id


def test_session_pinned_contributes_legacy_toggle_and_boolean_filter(
    tmp_path: Path,
) -> None:
    app = _build_app(tmp_path, metadata_key="favorite")

    elements = app.get_application_ui_schema()
    legacy_toggle = next(
        element
        for element in elements
        if element.get("ui_type") == "session_list_toggle_pinned"
    )
    pin_filter = next(
        element
        for element in elements
        if element.get("ui_type") == "session_list_filter"
    )

    assert legacy_toggle["action_id"] == "toggle_session_pinned"
    assert pin_filter == {
        "ui_type": "session_list_filter",
        "id": "pinned_state",
        "label": "Pinned",
        "icon": "star",
        "order": 10,
        "type": "boolean",
        "match": "equals",
        "data": "metadata.favorite",
        "missing_value": False,
        "default": None,
        "options": [
            {
                "value": False,
                "label": "Not pinned",
                "icon": "star",
                "tone": "muted",
            },
            {
                "value": True,
                "label": "Pinned",
                "icon": "star",
                "tone": "warning",
            },
        ],
        "plugin": "session_pinned",
    }

    schema = app.get_session_list_filter_schema()
    normalized = next(
        item for item in schema["filters"] if item["id"] == "pinned_state"
    )
    assert normalized["data"] == "metadata.favorite"
    assert normalized["default"] is None


def test_toggle_session_pinned_toggles_metadata_and_ids(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session(app)

    # First toggle: should pin the session.
    result1 = app.execute_application_action(
        plugin_id="session_pinned",
        action_id="toggle_session_pinned",
        params={"session_id": session_id},
    )

    updated1 = _get_mutations(result1).get("updated_session_ids") or []
    assert updated1 == [session_id]

    ctx1 = app.load_session(session_id)
    assert ctx1 is not None
    _core1, _base1, session1 = ctx1
    md1 = session1.metadata if isinstance(session1.metadata, dict) else {}
    assert md1.get("pinned") is True

    # Second toggle: should unpin the session.
    result2 = app.execute_application_action(
        plugin_id="session_pinned",
        action_id="toggle_session_pinned",
        params={"session_id": session_id},
    )

    updated2 = _get_mutations(result2).get("updated_session_ids") or []
    assert updated2 == [session_id]

    ctx2 = app.load_session(session_id)
    assert ctx2 is not None
    _core2, _base2, session2 = ctx2
    md2 = session2.metadata if isinstance(session2.metadata, dict) else {}
    assert md2.get("pinned") is False


def test_pin_filter_tracks_toggle_mutations_and_missing_values(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    first_id = _create_session(app)
    second_id = _create_session(app)

    all_ids = [
        item["session_id"]
        for item in app.list_session_summaries(
            filter_values={"pinned_state": None},
            apply_filter_defaults=True,
        )
    ]
    assert set(all_ids) == {first_id, second_id}

    initially_unpinned = app.list_session_summaries(
        filter_values={"pinned_state": False},
        apply_filter_defaults=True,
    )
    assert {item["session_id"] for item in initially_unpinned} == {
        first_id,
        second_id,
    }
    assert (
        app.list_session_summaries(
            filter_values={"pinned_state": True},
            apply_filter_defaults=True,
        )
        == []
    )

    app.execute_application_action(
        plugin_id="session_pinned",
        action_id="toggle_session_pinned",
        params={"session_id": first_id},
    )

    pinned = app.list_session_summaries(
        filter_values={"pinned_state": True},
        apply_filter_defaults=True,
    )
    assert [item["session_id"] for item in pinned] == [first_id]
    unpinned = app.list_session_summaries(
        filter_values={"pinned_state": False},
        apply_filter_defaults=True,
    )
    assert [item["session_id"] for item in unpinned] == [second_id]


def test_session_pinned_publishes_metadata_updated_event(tmp_path: Path) -> None:
    config_path = _make_config_with_session_pinned(tmp_path)
    session_root = tmp_path / "sessions_events"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    session_id = _create_session(app)

    _ = app.execute_application_action(
        plugin_id="session_pinned",
        action_id="toggle_session_pinned",
        params={"session_id": session_id},
    )

    evs = events.list(session_id=session_id, limit=20)["events"]
    types = {ev.get("type") for ev in evs}
    assert "session_metadata_updated" in types

    meta_events = [ev for ev in evs if ev.get("type") == "session_metadata_updated"]
    assert meta_events
    ev = meta_events[-1]
    assert ev.get("session_id") == session_id
    fields = ev.get("fields") or []
    assert "pinned" in fields
    assert [ev for ev in evs if ev.get("type") == "checkpoint"]
