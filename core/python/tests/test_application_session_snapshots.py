from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_app.application_future import AgentApplication, ReadonlySessionViewError
from agent_app.sessions import FilesystemSnapshotSelectionStore
from agent_core import AgentCore

# Make dotted-path test plugins available to the application loader.
from tests.dummy_provider import DummyProvider  # noqa: F401


def _write_dummy_provider_config(tmp_path: Path) -> Path:
    cfg = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "dummy": {
                "provider": "dummy_provider",
                "model": "dummy-model",
            }
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config_snapshots.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_snapshot_selection_is_isolated_per_application_instance(tmp_path: Path) -> None:
    config_path = _write_dummy_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    server_app = AgentApplication(
        str(config_path),
        str(session_root),
        core_factory=AgentCore,
        snapshot_selection_store=FilesystemSnapshotSelectionStore(session_root / ".snapshots"),
    )
    terminal_app = AgentApplication(
        str(config_path),
        str(session_root),
        core_factory=AgentCore,
    )

    core, base_config, session = server_app.create_session("default")
    session = core.add_message(session, "user", "first", config=base_config)
    server_app.save_session(session)

    snapshot = server_app.create_session_snapshot(session.session_id, reason="manual")

    live_session = core.add_message(session, "user", "second", config=base_config)
    server_app.save_session(live_session)
    server_app.select_session_snapshot(session.session_id, snapshot.snapshot_id)

    selected = server_app.load_session_record(session.session_id)
    live = terminal_app.load_session_record(session.session_id)

    assert selected is not None
    assert live is not None
    assert len(selected.messages) == 1
    assert len(live.messages) == 2
    assert server_app.get_selected_session_snapshot(session.session_id) == snapshot.snapshot_id

    with pytest.raises(ReadonlySessionViewError):
        server_app.save_session(live_session)


def test_restore_snapshot_restores_live_session_and_clears_selection(tmp_path: Path) -> None:
    config_path = _write_dummy_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(
        str(config_path),
        str(session_root),
        core_factory=AgentCore,
        snapshot_selection_store=FilesystemSnapshotSelectionStore(session_root / ".snapshots"),
    )

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "first", config=base_config)
    app.save_session(session)
    snapshot = app.create_session_snapshot(session.session_id, reason="manual")

    live_session = core.add_message(session, "user", "second", config=base_config)
    app.save_session(live_session)
    app.select_session_snapshot(session.session_id, snapshot.snapshot_id)

    restored = app.restore_session_snapshot(session.session_id, snapshot.snapshot_id)
    snapshots = app.list_session_snapshots(session.session_id)
    reasons = {record.reason for record in snapshots}

    assert len(restored.messages) == 1
    assert app.get_selected_session_snapshot(session.session_id) is None
    assert "before restore" in reasons