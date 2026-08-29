"""Unit tests for :mod:`session_actions_app` application plugin.

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

# Ensure provider + app plugin are importable for dotted-path loading.
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from session_actions_app import SessionActionsAppPlugin  # noqa: F401


def _get_mutations(result: Dict[str, Any]) -> Dict[str, Any]:
    mutations = result.get("mutations")
    return mutations if isinstance(mutations, dict) else {}


def _get_ui_effects(result: Dict[str, Any]) -> Dict[str, Any]:
    ui_effects = result.get("ui_effects")
    return ui_effects if isinstance(ui_effects, dict) else {}


def _make_config_with_session_actions(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "session_actions_app.SessionActionsAppPlugin",
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

    created = _get_mutations(result).get("created_session_ids") or []
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
    created_view = _get_mutations(res_view).get("created_session_ids") or []
    assert len(created_view) == 1
    assert _get_ui_effects(res_view).get("navigate_to_session_id") == created_view[0]

    # When triggered from the session list, the plugin should not set
    # a selected session id, allowing callers to stay on the list.
    res_list = app.execute_application_action(
        plugin_id="session_actions",
        action_id="copy_session",
        params={"session_id": original_id, "source": "session_list"},
    )
    assert _get_ui_effects(res_list).get("navigate_to_session_id") is None


def test_fork_session_at_copies_prefix_up_to_index(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    original_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = app.execute_application_action(
        plugin_id="session_actions",
        action_id="fork_session_at",
        params={"session_id": original_id, "index": 1, "source": "test"},
    )

    created = _get_mutations(result).get("created_session_ids") or []
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


def test_delete_from_here_deletes_message_and_all_later_messages(
    tmp_path: Path,
) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3", "m4"])

    # Simulate the "Delete from here" message action: start=2, no end.
    result = app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_messages",
        params={"session_id": session_id, "start": 2},
    )

    deleted_indices = sorted(result.get("deleted_indices") or [])
    assert deleted_indices == [2, 3, 4]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    remaining_contents = [m.content for m in session.messages]
    assert remaining_contents == ["m0", "m1"]


def test_delete_from_here_at_first_message_removes_all(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["m0", "m1", "m2"])

    result = app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_messages",
        params={"session_id": session_id, "start": 0},
    )

    deleted_indices = sorted(result.get("deleted_indices") or [])
    assert deleted_indices == [0, 1, 2]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    assert len(session.messages) == 0


def test_delete_messages_creates_restoreable_automatic_snapshot(
    tmp_path: Path,
) -> None:
    app = _build_app(tmp_path)
    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_messages",
        params={"session_id": session_id, "start": 2},
    )

    snapshots = app.list_session_snapshots(session_id)
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.reason == "Before deleting messages [2:]"
    assert snapshot.metadata == {
        "origin": "automatic",
        "plugin": "session_actions",
        "action": "delete_messages",
        "deleted_indices": [2, 3],
        "range": {"start": 2, "end": 4},
    }

    restored = app.restore_session_snapshot(session_id, snapshot.snapshot_id)
    assert [message.content for message in restored.messages] == [
        "m0",
        "m1",
        "m2",
        "m3",
    ]


def test_noop_delete_does_not_create_snapshot(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    session_id = _create_session_with_messages(app, ["m0"])

    result = app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_messages",
        params={"session_id": session_id, "indices": []},
    )

    assert result["message"] == "No messages deleted."
    assert app.list_session_snapshots(session_id) == []


def test_failed_delete_save_removes_provisional_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _build_app(tmp_path)
    session_id = _create_session_with_messages(app, ["m0", "m1"])

    def fail_save(*args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise RuntimeError("save failed")

    monkeypatch.setattr(app, "save_session", fail_save)

    with pytest.raises(RuntimeError, match="save failed"):
        app.execute_application_action(
            plugin_id="session_actions",
            action_id="delete_messages",
            params={"session_id": session_id, "indices": [1]},
        )

    assert app.list_session_snapshots(session_id) == []


def test_delete_from_here_ui_element_is_present() -> None:
    """Verify the delete_from_here message action is exposed in UI elements."""
    plugin = SessionActionsAppPlugin()
    plugin.init({"application": {"session_actions": {"allow_delete": True}}})
    elements = plugin.get_ui_elements(plugin._state)

    message_actions = [el for el in elements if el.get("ui_type") == "message_action"]
    ids = [el["id"] for el in message_actions]
    assert "delete_from_here" in ids

    delete_from_here = next(
        el for el in message_actions if el["id"] == "delete_from_here"
    )
    assert delete_from_here["label"] == "Delete from here"
    assert delete_from_here["action_id"] == "delete_messages"
    assert delete_from_here["param_map"]["start"] == "$message.index"
    assert delete_from_here["dialog"]["kind"] == "confirm"


def test_delete_session_respects_allow_delete_flag(tmp_path: Path) -> None:
    # First, with allow_delete enabled (default in helper config).
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["m0"])

    res = app.execute_application_action(
        plugin_id="session_actions",
        action_id="delete_session",
        params={"session_id": session_id},
    )

    deleted = _get_mutations(res).get("deleted_session_ids") or []
    assert deleted == [session_id]
    assert app.load_session(session_id) is None

    # Now, build a config that disables deletion and ensure the
    # plugin raises a ValueError when called.
    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "session_actions_app.SessionActionsAppPlugin",
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

    app2 = AgentApplication(
        str(cfg_path),
        str(tmp_path / "sessions2"),
        event_store=InMemoryEventStore(),
    )

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

    assert _get_mutations(res).get("deleted_session_ids") == [session_id]
    assert app.load_session_record(session_id) is None
