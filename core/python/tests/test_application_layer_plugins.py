"""Plugin configuration tests for the future application layer.

These tests exercise the plugin catalog and per-agent / per-session
plugin selection used by :class:`agent_app.application_future.AgentApplication`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_core import AgentCore, Session

# Import dummy plugins so they are available for dotted-path loading.
from .dummy_provider import DummyProvider  # noqa: F401
from .dummy_tool import DummyCalculator  # noqa: F401
from .dummy_extension import DummyExtension  # noqa: F401
from .dummy_feature import DummyFeature  # noqa: F401


def _make_full_plugin_config(tmp_path: Path, agent_plugins: List[str] | None = None) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_extension.DummyExtension",
            "tests.dummy_feature.DummyFeature",
            "tests.dummy_tool.DummyCalculator",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    if agent_plugins is not None:
        cfg["agents"]["default"]["plugins"] = list(agent_plugins)

    path = tmp_path / "config_plugins.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def test_list_plugins_exposes_all_kinds_and_ids(tmp_path: Path) -> None:
    config_path = _make_full_plugin_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    plugins = app.list_plugins()
    by_kind: Dict[str, List[str]] = {}
    for entry in plugins:
        kind = entry["kind"]
        by_kind.setdefault(kind, []).append(entry["id"])

    assert "providers" in by_kind
    assert "extensions" in by_kind
    assert "features" in by_kind
    assert "tools" in by_kind

    assert "dummy_provider" in by_kind["providers"]
    assert "dummy_extension" in by_kind["extensions"]
    assert "dummy_feature" in by_kind["features"]
    assert "dummy_calculator" in by_kind["tools"]


def test_get_agent_plugins_round_trips_configured_list(tmp_path: Path) -> None:
    plugins_list = ["dummy_provider", "dummy_calculator"]
    config_path = _make_full_plugin_config(tmp_path, agent_plugins=plugins_list)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    assert app.get_agent_plugins("default") == plugins_list

    # When plugins key is omitted, None means "all plugins enabled".
    config_path2 = _make_full_plugin_config(tmp_path, agent_plugins=None)
    session_root2 = tmp_path / "sessions2"
    app2 = AgentApplication(str(config_path2), str(session_root2), core_factory=AgentCore)

    assert app2.get_agent_plugins("default") is None

    with pytest.raises(KeyError):
        _ = app2.get_agent_plugins("unknown")


def test_create_session_uses_agent_plugin_list(tmp_path: Path) -> None:
    # Only provider + tool enabled via agent-level list.
    plugins_list = ["dummy_provider", "dummy_calculator"]
    config_path = _make_full_plugin_config(tmp_path, agent_plugins=plugins_list)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    assert base_config["provider"] == "dummy_provider"
    assert session.metadata == {"agent_id": "default"}

    providers = getattr(core, "_providers")
    features = getattr(core, "_features")
    tools = getattr(core, "_tools")

    # One provider with no extensions.
    assert len(providers) == 1
    provider_wrapper = providers[0]
    assert provider_wrapper.plugin_class.__name__ == "DummyProvider"
    assert provider_wrapper.extensions == []

    # No features enabled.
    assert features == []

    # One tool enabled.
    assert len(tools) == 1
    tool_wrapper = tools[0]
    assert tool_wrapper.plugin_class.__name__ == "DummyCalculator"


def test_create_session_uses_all_plugins_when_agent_list_missing(tmp_path: Path) -> None:
    # No agent-level plugins list: all configured plugins are enabled.
    config_path = _make_full_plugin_config(tmp_path, agent_plugins=None)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    assert base_config["provider"] == "dummy_provider"
    assert session.metadata == {"agent_id": "default"}

    providers = getattr(core, "_providers")
    features = getattr(core, "_features")
    tools = getattr(core, "_tools")

    assert len(providers) == 1
    provider_wrapper = providers[0]
    assert provider_wrapper.plugin_class.__name__ == "DummyProvider"
    # One extension attached to the provider.
    assert len(provider_wrapper.extensions) == 1
    assert provider_wrapper.extensions[0].plugin_class.__name__ == "DummyExtension"

    assert len(features) == 1
    assert features[0].plugin_class.__name__ == "DummyFeature"

    assert len(tools) == 1
    assert tools[0].plugin_class.__name__ == "DummyCalculator"


def test_load_session_uses_session_metadata_plugins(tmp_path: Path) -> None:
    # Start with all plugins enabled, then restrict via session metadata.
    config_path = _make_full_plugin_config(tmp_path, agent_plugins=None)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    # Persist a new session object with an explicit plugins list.
    md = dict(session.metadata or {})
    md["plugins"] = ["dummy_provider", "nonexistent_plugin"]
    new_session = Session(session_id=session.session_id, messages=list(session.messages), metadata=md)
    app.save_session(new_session)

    ctx = app.load_session(new_session.session_id)
    assert ctx is not None
    core2, base_config2, loaded_session = ctx

    assert base_config2 == base_config
    assert loaded_session.metadata["agent_id"] == "default"
    assert loaded_session.metadata["plugins"] == md["plugins"]

    providers = getattr(core2, "_providers")
    features = getattr(core2, "_features")
    tools = getattr(core2, "_tools")

    # Only the provider is enabled; extension, feature, and tool are disabled.
    assert len(providers) == 1
    provider_wrapper = providers[0]
    assert provider_wrapper.plugin_class.__name__ == "DummyProvider"
    assert provider_wrapper.extensions == []

    assert features == []
    assert tools == []


def test_load_session_raises_when_no_provider_enabled(tmp_path: Path) -> None:
    # Config has a provider, but session metadata disables all providers.
    config_path = _make_full_plugin_config(tmp_path, agent_plugins=None)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    md = dict(session.metadata or {})
    md["plugins"] = ["dummy_calculator"]  # tool only, no providers
    new_session = Session(session_id=session.session_id, messages=list(session.messages), metadata=md)
    app.save_session(new_session)

    with pytest.raises(RuntimeError) as exc:
        _ = app.load_session(new_session.session_id)

    assert "No provider plugins enabled" in str(exc.value)
