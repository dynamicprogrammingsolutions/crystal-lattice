"""Plugin package configuration tests for the future application layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from agent_app.application_future import AgentApplication
from agent_core import AgentCore, Session

# Import dummy plugins so they are available for dotted-path loading.
from .dummy_extension import DummyExtension  # noqa: F401
from .dummy_feature import DummyFeature  # noqa: F401
from .dummy_provider import DummyProvider  # noqa: F401
from .dummy_tool import DummyCalculator  # noqa: F401
from .dummy_tool_same_id import AlternateDummyCalculator  # noqa: F401


def _write_config(tmp_path: Path, config: Dict[str, Any], name: str = "config_plugins.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _make_app(tmp_path: Path, config: Dict[str, Any], name: str = "config_plugins.json") -> AgentApplication:
    config_path = _write_config(tmp_path, config, name=name)
    session_root = tmp_path / f"sessions-{name}"
    return AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)


def _core_plugin_names(core: AgentCore) -> Tuple[List[str], List[str], List[str], List[str]]:
    providers = [wrapper.plugin_class.__name__ for wrapper in getattr(core, "_providers")]
    extensions: List[str] = []
    for wrapper in getattr(core, "_providers"):
        extensions.extend(ext.plugin_class.__name__ for ext in wrapper.extensions)
    features = [wrapper.plugin_class.__name__ for wrapper in getattr(core, "_features")]
    tools = [wrapper.plugin_class.__name__ for wrapper in getattr(core, "_tools")]
    return providers, extensions, features, tools


def test_list_plugins_for_agent_uses_global_provider_and_agent_package_specs(tmp_path: Path) -> None:
    config = {
        "providers": {
            "primary": {
                "provider": "dummy_provider",
                "model": "test-model",
                "plugins": ["tests.dummy_extension.DummyExtension"],
            }
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {
            "alpha": {
                "provider": "primary",
                "plugins": ["tests.dummy_tool.DummyCalculator"],
            },
            "beta": {"provider": "primary"},
        },
    }

    app = _make_app(tmp_path, config)

    alpha_plugins = app.list_plugins_for_agent("alpha")
    beta_plugins = app.list_plugins_for_agent("beta")

    assert [entry["id"] for entry in alpha_plugins] == [
        "dummy_provider",
        "dummy_extension",
        "dummy_calculator",
    ]
    assert [entry["id"] for entry in beta_plugins] == [
        "dummy_provider",
        "dummy_extension",
    ]

    alpha_core, base_config, _alpha_session = app.create_session("alpha")
    assert base_config["provider"] == "dummy_provider"
    assert _core_plugin_names(alpha_core) == (
        ["DummyProvider"],
        ["DummyExtension"],
        [],
        ["DummyCalculator"],
    )

    beta_core, _base_config, _beta_session = app.create_session("beta")
    assert _core_plugin_names(beta_core) == (
        ["DummyProvider"],
        ["DummyExtension"],
        [],
        [],
    )


def test_provider_level_plugins_only_apply_to_agents_using_that_provider(tmp_path: Path) -> None:
    config = {
        "providers": {
            "tooling": {
                "provider": "dummy_provider",
                "model": "test-model",
                "plugins": ["tests.dummy_tool.DummyCalculator"],
            },
            "features": {
                "provider": "dummy_provider",
                "model": "test-model",
                "plugins": ["tests.dummy_feature.DummyFeature"],
            },
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {
            "tool-agent": {"provider": "tooling"},
            "feature-agent": {"provider": "features"},
        },
    }

    app = _make_app(tmp_path, config)

    assert [entry["id"] for entry in app.list_plugins_for_agent("tool-agent")] == [
        "dummy_provider",
        "dummy_calculator",
    ]
    assert [entry["id"] for entry in app.list_plugins_for_agent("feature-agent")] == [
        "dummy_provider",
        "dummy_feature",
    ]

    tool_core, _tool_cfg, _tool_session = app.create_session("tool-agent")
    assert _core_plugin_names(tool_core) == (["DummyProvider"], [], [], ["DummyCalculator"])

    feature_core, _feature_cfg, _feature_session = app.create_session("feature-agent")
    assert _core_plugin_names(feature_core) == (["DummyProvider"], [], ["DummyFeature"], [])


def test_agent_level_plugins_only_apply_to_that_agent(tmp_path: Path) -> None:
    config = {
        "providers": {
            "shared": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {
            "tool-agent": {
                "provider": "shared",
                "plugins": ["tests.dummy_tool.DummyCalculator"],
            },
            "feature-agent": {
                "provider": "shared",
                "plugins": ["tests.dummy_feature.DummyFeature"],
            },
        },
    }

    app = _make_app(tmp_path, config)

    assert [entry["id"] for entry in app.list_plugins_for_agent("tool-agent")] == [
        "dummy_provider",
        "dummy_calculator",
    ]
    assert [entry["id"] for entry in app.list_plugins_for_agent("feature-agent")] == [
        "dummy_provider",
        "dummy_feature",
    ]

    tool_core, _tool_cfg, _tool_session = app.create_session("tool-agent")
    assert _core_plugin_names(tool_core) == (["DummyProvider"], [], [], ["DummyCalculator"])

    feature_core, _feature_cfg, _feature_session = app.create_session("feature-agent")
    assert _core_plugin_names(feature_core) == (["DummyProvider"], [], ["DummyFeature"], [])


def test_disabled_plugins_shape_default_enabled_set_and_session_override_can_reenable(
    tmp_path: Path,
) -> None:
    config = {
        "providers": {
            "primary": {
                "provider": "dummy_provider",
                "model": "test-model",
                "disabled_plugins": ["dummy_feature"],
            }
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_feature.DummyFeature",
            "tests.dummy_tool.DummyCalculator",
        ],
        "agents": {
            "default": {
                "provider": "primary",
                "disabled_plugins": ["dummy_calculator"],
            }
        },
    }

    app = _make_app(tmp_path, config)

    assert app.get_agent_plugins("default") == ["dummy_provider"]
    assert [entry["id"] for entry in app.list_plugins_for_agent("default")] == [
        "dummy_provider",
        "dummy_feature",
        "dummy_calculator",
    ]

    core, _base_config, session = app.create_session("default")
    assert _core_plugin_names(core) == (["DummyProvider"], [], [], [])

    metadata = dict(session.metadata or {})
    metadata["plugins"] = ["dummy_provider", "dummy_feature", "dummy_calculator"]
    overridden = Session(
        session_id=session.session_id,
        messages=list(session.messages),
        metadata=metadata,
    )
    app.save_session(overridden)

    ctx = app.load_session(overridden.session_id)
    assert ctx is not None
    override_core, _override_cfg, loaded = ctx
    assert loaded.metadata["plugins"] == metadata["plugins"]
    assert _core_plugin_names(override_core) == (
        ["DummyProvider"],
        [],
        ["DummyFeature"],
        ["DummyCalculator"],
    )


def test_duplicate_plugin_ids_follow_first_registration_wins(tmp_path: Path) -> None:
    config = {
        "providers": {
            "primary": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_tool.DummyCalculator",
        ],
        "agents": {
            "default": {
                "provider": "primary",
                "plugins": ["tests.dummy_tool_same_id.AlternateDummyCalculator"],
            }
        },
    }

    app = _make_app(tmp_path, config)

    plugins = app.list_plugins_for_agent("default")
    by_id = {entry["id"]: entry for entry in plugins}
    assert by_id["dummy_calculator"]["class_path"] == "tests.dummy_tool.DummyCalculator"

    core, _base_config, _session = app.create_session("default")
    assert _core_plugin_names(core) == (["DummyProvider"], [], [], ["DummyCalculator"])


def test_load_session_raises_when_no_provider_enabled(tmp_path: Path) -> None:
    config = {
        "providers": {
            "primary": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_tool.DummyCalculator",
        ],
        "agents": {"default": {"provider": "primary"}},
    }

    app = _make_app(tmp_path, config)

    core, _base_config, session = app.create_session("default")
    metadata = dict(session.metadata or {})
    metadata["plugins"] = ["dummy_calculator"]
    providerless = Session(
        session_id=session.session_id,
        messages=list(session.messages),
        metadata=metadata,
    )

    with pytest.raises(RuntimeError) as exc:
        app.save_session(providerless)

    assert "No provider plugins enabled" in str(exc.value)