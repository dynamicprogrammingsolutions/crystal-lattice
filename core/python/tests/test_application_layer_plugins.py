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
from .dummy_tool import CancellableBlockingTool  # noqa: F401
from .dummy_tool import DummyCalculator  # noqa: F401
from .dummy_tool_same_id import AlternateDummyCalculator  # noqa: F401


def _write_config(
    tmp_path: Path, config: Dict[str, Any], name: str = "config_plugins.json"
) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _make_app(
    tmp_path: Path, config: Dict[str, Any], name: str = "config_plugins.json"
) -> AgentApplication:
    config_path = _write_config(tmp_path, config, name=name)
    session_root = tmp_path / f"sessions-{name}"
    return AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)


def _core_plugin_names(
    core: AgentCore,
) -> Tuple[List[str], List[str], List[str], List[str]]:
    providers = [
        wrapper.plugin_class.__name__ for wrapper in getattr(core, "_providers")
    ]
    extensions: List[str] = []
    for wrapper in getattr(core, "_providers"):
        extensions.extend(ext.plugin_class.__name__ for ext in wrapper.extensions)
    features = [wrapper.plugin_class.__name__ for wrapper in getattr(core, "_features")]
    tools = [wrapper.plugin_class.__name__ for wrapper in getattr(core, "_tools")]
    return providers, extensions, features, tools


def _tool_schema_names(core: AgentCore, config: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for schema in core.get_tool_schemas(config):
        if not isinstance(schema, dict):
            continue
        function = schema.get("function")
        if not isinstance(function, dict):
            continue
        name = function.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return names


def test_list_plugins_for_agent_uses_global_provider_and_agent_package_specs(
    tmp_path: Path,
) -> None:
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


def test_runtime_pip_constraint_is_added_to_plugin_install_policy(
    tmp_path: Path,
) -> None:
    config = {
        "providers": {
            "primary": {
                "provider": "dummy_provider",
                "model": "test-model",
            }
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {"default": {"provider": "primary"}},
    }
    constraint = tmp_path / "pip-constraints.txt"
    constraint.write_text("cryptography==48.0.1\n", encoding="utf-8")
    config_path = _write_config(tmp_path, config)

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        env_overrides={"CRYSTAL_PIP_CONSTRAINT": str(constraint)},
    )

    assert app._plugin_manager.policy["pip_args"] == [
        "--constraint",
        str(constraint),
    ]


def test_explicit_plugin_constraint_policy_wins_over_runtime_default(
    tmp_path: Path,
) -> None:
    explicit_constraint = tmp_path / "explicit-constraints.txt"
    explicit_constraint.write_text("cryptography==47.0.0\n", encoding="utf-8")
    runtime_constraint = tmp_path / "runtime-constraints.txt"
    runtime_constraint.write_text("cryptography==48.0.1\n", encoding="utf-8")
    config = {
        "plugin_policy": {
            "pip_args": ["--constraint", str(explicit_constraint)],
        },
        "providers": {
            "primary": {
                "provider": "dummy_provider",
                "model": "test-model",
            }
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {"default": {"provider": "primary"}},
    }
    config_path = _write_config(tmp_path, config)

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        env_overrides={"CRYSTAL_PIP_CONSTRAINT": str(runtime_constraint)},
    )

    assert app._plugin_manager.policy["pip_args"] == [
        "--constraint",
        str(explicit_constraint),
    ]


def test_provider_level_plugins_only_apply_to_agents_using_that_provider(
    tmp_path: Path,
) -> None:
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
    assert _core_plugin_names(tool_core) == (
        ["DummyProvider"],
        [],
        [],
        ["DummyCalculator"],
    )

    feature_core, _feature_cfg, _feature_session = app.create_session("feature-agent")
    assert _core_plugin_names(feature_core) == (
        ["DummyProvider"],
        [],
        ["DummyFeature"],
        [],
    )


def test_agent_level_plugins_only_apply_to_that_agent(tmp_path: Path) -> None:
    config = {
        "providers": {"shared": {"provider": "dummy_provider", "model": "test-model"}},
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
    assert _core_plugin_names(tool_core) == (
        ["DummyProvider"],
        [],
        [],
        ["DummyCalculator"],
    )

    feature_core, _feature_cfg, _feature_session = app.create_session("feature-agent")
    assert _core_plugin_names(feature_core) == (
        ["DummyProvider"],
        [],
        ["DummyFeature"],
        [],
    )


def test_create_session_exposes_only_agent_specific_tool_schemas_to_model(
    tmp_path: Path,
) -> None:
    config = {
        "providers": {"shared": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {
            "math-agent": {
                "provider": "shared",
                "plugins": ["tests.dummy_tool.DummyCalculator"],
            },
            "blocking-agent": {
                "provider": "shared",
                "plugins": ["tests.dummy_tool.CancellableBlockingTool"],
            },
        },
    }

    app = _make_app(tmp_path, config)

    math_core, math_base_config, _math_session = app.create_session("math-agent")
    assert _core_plugin_names(math_core) == (
        ["DummyProvider"],
        [],
        [],
        ["DummyCalculator"],
    )
    assert _tool_schema_names(math_core, math_base_config) == ["add"]

    blocking_core, blocking_base_config, _blocking_session = app.create_session(
        "blocking-agent"
    )
    assert _core_plugin_names(blocking_core) == (
        ["DummyProvider"],
        [],
        [],
        ["CancellableBlockingTool"],
    )
    assert _tool_schema_names(blocking_core, blocking_base_config) == [
        "block_until_cancel"
    ]


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


def test_agent_profile_plugins_report_safe_effective_defaults(tmp_path: Path) -> None:
    config = {
        "providers": {
            "primary": {
                "provider": "dummy_provider",
                "model": "test-model",
                "api_key": "must-not-be-exposed",
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
                "private_setting": "also-must-not-be-exposed",
            }
        },
    }

    app = _make_app(tmp_path, config)
    plugins = app.list_agent_profile_plugins("default")
    by_id = {entry["id"]: entry for entry in plugins}

    assert by_id["dummy_provider"]["enabled"] is True
    assert by_id["dummy_provider"]["active"] is True
    assert by_id["dummy_provider"]["source"] == "agent"
    assert by_id["dummy_feature"]["enabled"] is True
    assert by_id["dummy_calculator"]["enabled"] is False
    assert by_id["dummy_calculator"]["active"] is False
    assert by_id["dummy_calculator"]["source"] == "agent"

    allowed_keys = {
        "id",
        "kind",
        "name",
        "class_path",
        "class_name",
        "enabled",
        "active",
        "source",
    }
    assert all(set(entry).issubset(allowed_keys) for entry in plugins)
    assert "must-not-be-exposed" not in repr(plugins)


def test_agent_run_descriptor_exposes_safe_defaults_and_schema(tmp_path: Path) -> None:
    config = {
        "providers": {
            "primary": {
                "provider": "dummy_provider",
                "model": "test-model",
                "api_key": "must-not-be-exposed",
            }
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {
            "default": {
                "provider": "primary",
                "reasoning_effort": "high",
                "display": {
                    "title": "Default agent",
                    "description": "Safe descriptor",
                },
            }
        },
    }

    app = _make_app(tmp_path, config)
    descriptor = app.describe_agent_run("default")

    assert descriptor["id"] == "default"
    assert descriptor["title"] == "Default agent"
    assert descriptor["provider_route"] == "primary"
    assert descriptor["provider_plugin"] == "dummy_provider"
    assert descriptor["effective_settings"] == {
        "model": "test-model",
        "reasoning_effort": "high",
    }
    schema_keys = {
        entry.get("key")
        for entry in descriptor["config_schema"]
        if isinstance(entry, dict)
    }
    assert "model" in schema_keys
    assert "api_key" not in schema_keys
    assert "must-not-be-exposed" not in repr(descriptor)


def test_duplicate_plugin_ids_follow_first_registration_wins(tmp_path: Path) -> None:
    config = {
        "providers": {"primary": {"provider": "dummy_provider", "model": "test-model"}},
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


def test_update_agent_recovers_when_previous_agent_is_missing(tmp_path: Path) -> None:
    config = {
        "providers": {"primary": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_feature.DummyFeature",
            "tests.dummy_tool.DummyCalculator",
        ],
        "agents": {
            "default": {
                "provider": "primary",
                "disabled_plugins": ["dummy_calculator"],
            },
            "other": {
                "provider": "primary",
                "disabled_plugins": ["dummy_feature"],
            },
        },
    }

    app = _make_app(tmp_path, config)

    _core, _base_config, session = app.create_session("default")
    broken_session = Session(
        session_id=session.session_id,
        messages=list(session.messages),
        metadata={
            **(session.metadata or {}),
            "agent_id": "missing-agent",
            "plugins": ["dummy_provider", "dummy_feature"],
        },
    )

    switched_core, switched_base_config, switched_session = app.update_agent(
        "other", broken_session
    )

    assert switched_base_config["provider"] == "dummy_provider"
    assert switched_session.metadata["agent_id"] == "other"
    assert switched_session.metadata["plugins"] == [
        "dummy_provider",
        "dummy_calculator",
    ]
    assert _core_plugin_names(switched_core) == (
        ["DummyProvider"],
        [],
        [],
        ["DummyCalculator"],
    )


def test_load_session_raises_when_no_provider_enabled(tmp_path: Path) -> None:
    config = {
        "providers": {"primary": {"provider": "dummy_provider", "model": "test-model"}},
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
