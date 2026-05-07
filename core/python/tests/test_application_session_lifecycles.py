from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_core import AgentCore

from .dummy_app_plugin import DummyAppPlugin  # noqa: F401
from .dummy_lifecycle_app_plugin import DummyLifecycleAppPlugin  # noqa: F401
from .dummy_lifecycle_extension import DummyLifecycleExtension  # noqa: F401
from .dummy_provider import (  # noqa: F401
    DummyProvider,
    FailingOnceDummyProvider,
    reset_failing_dummy_provider_state,
)


def _write_config(
    tmp_path: Path,
    *,
    provider_class: str = "tests.dummy_provider.DummyProvider",
) -> Path:
    provider_name = (
        "failing_dummy_provider"
        if provider_class.endswith("FailingOnceDummyProvider")
        else "dummy_provider"
    )
    cfg: Dict[str, Any] = {
        "providers": {
            "dummy": {"provider": provider_name, "model": "test-model"},
            "other": {"provider": provider_name, "model": "other-model"},
        },
        "plugins": [
            provider_class,
            "tests.dummy_lifecycle_extension.DummyLifecycleExtension",
            "tests.dummy_lifecycle_app_plugin.DummyLifecycleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "dummy"},
            "other": {"provider": "other"},
        },
    }
    path = tmp_path / "config_lifecycles.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_create_and_delete_session_run_lifecycle_actions(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    assert base_config["provider"] == "dummy_provider"
    assert session.metadata["app_created_marker"] is True
    assert session.metadata["saved_by_extension"] is True
    assert session.metadata["overrides"]["created_by_extension"] is True
    assert "session_create" in session.metadata["extension_lifecycle_log"]
    assert "session_save_prepare" in session.metadata["extension_lifecycle_log"]

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    _core2, _base2, loaded_session = loaded
    assert loaded_session.metadata == session.metadata

    wrapper = app._app_plugins["dummy_lifecycle_app_plugin"]
    plugin = wrapper.plugin
    assert isinstance(plugin, DummyLifecycleAppPlugin)

    app.delete_session(session.session_id)

    assert app.load_session_record(session.session_id) is None
    assert any(record["action_id"] == "app_on_session_delete_prepare" for record in plugin.executed)


def test_request_prepare_and_complete_lifecycles_update_checkpoint_session(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello", config=base_config)
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, stream=False))

    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected session checkpoints during request"
    final_session = checkpoints[-1]["session"]
    assert final_session.metadata["request_completed_by_extension"] is True
    assert final_session.metadata["overrides"]["prepared_by_extension"] is True
    assert "request_prepare" in final_session.metadata["extension_lifecycle_log"]
    assert "request_complete" in final_session.metadata["extension_lifecycle_log"]


def test_request_error_lifecycle_records_error_metadata(tmp_path: Path) -> None:
    reset_failing_dummy_provider_state()
    config_path = _write_config(
        tmp_path,
        provider_class="tests.dummy_provider.FailingOnceDummyProvider",
    )
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "fail please", config=base_config)
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, stream=False))

    kinds = [ev.get("type") for ev in events]
    assert "error" in kinds
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    final_session = checkpoints[-1]["session"]
    assert final_session.metadata["request_error_message"] == "Simulated provider failure"
    assert "request_error" in final_session.metadata["extension_lifecycle_log"]


def test_fork_and_agent_switch_run_lifecycle_actions(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello", config=base_config)
    app.save_session(session)

    _fork_core, _fork_base, forked = app.fork_session(
        core,
        session,
        base_config,
        upto_index=0,
        new_session_id="forked-session",
    )
    assert forked.session_id == "forked-session"
    assert forked.metadata["fork_source_session_id"] == session.session_id
    assert "session_fork" in forked.metadata["extension_lifecycle_log"]

    _switched_core, _switched_base, switched = app.update_agent("other", session)
    assert switched.metadata["agent_id"] == "other"
    assert switched.metadata["agent_switch_prepare_to"] == "other"
    assert switched.metadata["agent_switch_complete_to"] == "other"


def test_agent_switch_resets_stale_session_plugin_selection(tmp_path: Path) -> None:
    config = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"},
            "other": {"provider": "failing_dummy_provider", "model": "other-model"},
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_provider.FailingOnceDummyProvider",
        ],
        "agents": {
            "default": {
                "provider": "dummy",
                "disabled_plugins": ["failing_dummy_provider"],
            },
            "other": {
                "provider": "other",
                "disabled_plugins": ["dummy_provider"],
            },
        },
    }
    config_path = tmp_path / "config_switch_plugins.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore)

    _core, _base_config, session = app.create_session("default")
    session = type(session)(
        session_id=session.session_id,
        messages=session.messages,
        metadata={**(session.metadata or {}), "plugins": ["dummy_provider"]},
    )

    _switched_core, switched_base, switched = app.update_agent("other", session)

    assert switched_base["provider"] == "failing_dummy_provider"
    assert switched.metadata["agent_id"] == "other"
    assert switched.metadata["plugins"] == ["failing_dummy_provider"]
