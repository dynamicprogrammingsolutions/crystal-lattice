"""Unit tests for :mod:`plugins.session_actions_app` application plugin.

These tests exercise the SessionActionsAppPlugin directly via the
application-layer ``AgentApplication.execute_application_action`` helper.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session

# Ensure provider plugin is importable for dotted-path loading.
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from plugins.session_actions_app import SessionActionsAppPlugin  # noqa: F401


def _make_config_with_session_actions(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.session_actions_app.SessionActionsAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "session_actions": {"allow_delete": True},
        },
    }

    path = tmp_path / "config_session_actions.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    config_path = _make_config_with_session_actions(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    for text in contents:
        session = core.add_message(session, "user", text, None, base_config)

    app.save_session(session)
    return session.session_id


def test_copy_session_creates_new_session_with_same_messages(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    original_id = _create_session_with_messages(app, ["one", "two"])

    result = app.execute_application_action(
        plugin_id="session_actions",
        action_id="copy_session",
        params={"session_id": original_id, "source": "test"},
    )

    created = result.get("created_session_ids") or []
    assert len(created) == 1
    new_id = created[0]
    assert isinstance(new_id, str) and new_id != original_id

    ctx_orig = app.load_session(original_id)
    ctx_new = app.load_session(new_id)
    assert ctx_orig is not None
    assert ctx_new is not None

    _core_o, _base_o, session_orig = ctx_orig
    _core_n, _base_n, session_new = ctx_new

    assert [m.content for m in session_new.messages] == [
        m.content for m in session_orig.messages
    ]

    events = app.get_event_store().list(session_id=new_id, limit=10)
    kinds = {ev.get("type") for ev in events}
    assert "session_created" in kinds


def test_copy_session_selected_session_depends_on_source(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    original_id = _create_session_with_messages(app, ["one", "two"])

    # From a non-session-list source, the new session should be
    # selected by default.
    res_view = app.execute_application_action(
        plugin_id="session_actions",
        action_id="copy_session",
        params={"session_id": original_id, "source": "session_view"},
    )
    created_view = res_view.get("created_session_ids") or []
    assert len(created_view) == 1
    assert res_view.get("selected_session_id") == created_view[0]

    # When triggered from the session list, the plugin should not set
    # a selected session id, allowing callers to stay on the list.
    res_list = app.execute_application_action(
        plugin_id="session_actions",
        action_id="copy_session",
        params={"session_id": original_id, "source": "session_list"},
    )
    assert "selected_session_id" not in res_list or res_list.get("selected_session_id") is None


def test_fork_session_at_copies_prefix_up_to_index(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    original_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = app.execute_application_action(
        plugin_id="session_actions",
        action_id="fork_session_at",
        params={"session_id": original_id, "index": 1, "source": "test"},
    )

    created = result.get("created_session_ids") or []
    assert len(created) == 1
    fork_id = created[0]

    ctx_orig = app.load_session(original_id)
    ctx_fork = app.load_session(fork_id)
    assert ctx_orig is not None
    assert ctx_fork is not None

    _core_o, _base_o, session_orig = ctx_orig
    _core_f, _base_f, session_fork = ctx_fork

    assert len(session_fork.messages) == 2
    assert [m.content for m in session_fork.messages] == [
        m.content for m in session_orig.messages[:2]
    ]


def test_delete_messages_by_indices_and_range(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3", "m4"])

    # Delete specific indices.
    res_indices = app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_messages",
        params={"session_id": session_id, "indices": [1, 3]},
    )

    deleted_indices = sorted(res_indices.get("deleted_indices") or [])
    assert deleted_indices == [1, 3]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    remaining_contents = [m.content for m in session.messages]
    assert remaining_contents == ["m0", "m2", "m4"]

    # Delete using Python-style range semantics: start from index 1 to end.
    res_range = app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_messages",
        params={"session_id": session_id, "start": 1},
    )

    deleted_range = sorted(res_range.get("deleted_indices") or [])
    assert deleted_range == [1, 2]

    ctx2 = app.load_session(session_id)
    assert ctx2 is not None
    _core2, _base2, session2 = ctx2
    remaining_contents2 = [m.content for m in session2.messages]
    assert remaining_contents2 == ["m0"]


def test_delete_session_respects_allow_delete_flag(tmp_path: Path) -> None:
    # First, with allow_delete enabled (default in helper config).
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["m0"])

    res = app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_session",
        params={"session_id": session_id},
    )

    deleted = res.get("deleted_session_ids") or []
    assert deleted == [session_id]
    assert app.load_session(session_id) is None

    # Now, build a config that disables deletion and ensure the
    # plugin raises a ValueError when called.
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.session_actions_app.SessionActionsAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "session_actions": {"allow_delete": False},
        },
    }

    cfg_path = tmp_path / "config_no_delete.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    app2 = AgentApplication(str(cfg_path), str(tmp_path / "sessions2"), event_store=InMemoryEventStore())

    # Seed a session; this uses the application with deletion disabled
    # purely so that there is a valid id to reference.
    core, base_config, session = app2.create_session("default")
    session = core.add_message(session, "user", "hello", None, base_config)
    app2.save_session(session)

    with pytest.raises(ValueError):
        _ = app2.execute_application_action(
            plugin_id="session_actions",
            action_id="delete_session",
            params={"session_id": session.session_id},
        )


def test_delete_session_works_even_if_agent_id_is_unknown(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["m0"])

    # Corrupt the stored metadata so that it references an agent id that is no
    # longer present in the configuration.
    session_path = tmp_path / "sessions" / f"{session_id}.json"
    data = json.loads(session_path.read_text(encoding="utf-8"))
    metadata = data.get("metadata")
    assert isinstance(metadata, dict)
    metadata["agent_id"] = "missing-agent"
    session_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    res = app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_session",
        params={"session_id": session_id},
    )

    assert res.get("deleted_session_ids") == [session_id]
    assert app.load_session_record(session_id) is None
