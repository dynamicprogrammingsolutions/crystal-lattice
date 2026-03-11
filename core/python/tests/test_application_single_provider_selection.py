from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from agent_app.application_future import AgentApplication
from agent_core import AgentCore, Session

# Make dotted-path plugin loading work in the config fixtures below.
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from .dummy_provider import DummyProvider  # noqa: F401


def _make_multi_provider_config(tmp_path: Path) -> Path:
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

    path = tmp_path / "config_multi_provider_selection.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _provider_names(core: AgentCore) -> list[str]:
    providers = getattr(core, "_providers")
    return [wrapper.plugin_class.__name__ for wrapper in providers]


def test_create_and_load_session_narrow_to_selected_provider(tmp_path: Path) -> None:
    config_path = _make_multi_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    assert base_config["provider"] == "echo_openai_like"
    assert _provider_names(core) == ["EchoOpenAILikeProvider"]

    ctx = app.load_session(session.session_id)
    assert ctx is not None
    loaded_core, loaded_base_config, loaded_session = ctx

    assert loaded_base_config == base_config
    assert loaded_session.session_id == session.session_id
    assert _provider_names(loaded_core) == ["EchoOpenAILikeProvider"]


def test_load_session_uses_session_overrides_to_select_one_provider(tmp_path: Path) -> None:
    config_path = _make_multi_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    _core, _base_config, session = app.create_session("default")
    metadata = dict(session.metadata or {})
    metadata["overrides"] = {"provider": "dummy_provider"}
    overridden_session = Session(
        session_id=session.session_id,
        messages=session.messages,
        metadata=metadata,
    )
    app.save_session(overridden_session)

    ctx = app.load_session(session.session_id)
    assert ctx is not None
    loaded_core, _loaded_base_config, loaded_session = ctx

    assert loaded_session.metadata == overridden_session.metadata
    assert _provider_names(loaded_core) == ["DummyProvider"]


def test_load_session_accepts_request_time_provider_override(tmp_path: Path) -> None:
    config_path = _make_multi_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    _core, _base_config, session = app.create_session("default")

    ctx = app.load_session(
        session.session_id,
        overrides={"provider": "tests.dummy_provider.DummyProvider"},
    )
    assert ctx is not None

    overridden_core, _loaded_base_config, _loaded_session = ctx
    assert _provider_names(overridden_core) == ["DummyProvider"]


def test_load_session_fails_explicitly_when_selected_provider_is_unknown(tmp_path: Path) -> None:
    config_path = _make_multi_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    _core, _base_config, session = app.create_session("default")

    with pytest.raises(RuntimeError, match="Unknown provider 'missing_provider'"):
        app.load_session(session.session_id, overrides={"provider": "missing_provider"})