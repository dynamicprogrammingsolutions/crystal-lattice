"""Config resolution tests for the application layer."""

from __future__ import annotations

from pathlib import Path

from agent_app.application_future import AgentApplication
from agent_app.config import (
    build_config_resolution_env,
    build_runtime_overlay_env,
    load_raw_config,
    resolve_config_mixins,
    resolve_placeholders,
    build_agent_config,
)
from agent_core import AgentCore


def test_resolve_placeholders_collects_errors(tmp_path, monkeypatch):
    cfg = {
        "providers": {
            "openai": {
                "api_key": "${env:NON_EXISTENT}",
                "prompt": "${file:./no_such_file.txt}",
            }
        }
    }
    path = tmp_path / "config.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")

    raw = load_raw_config(path)
    resolved, errors = resolve_placeholders(raw, env={})

    provider = resolved["providers"]["openai"]
    assert provider["api_key"] == ""
    assert provider["prompt"] == ""
    assert errors
    kinds = {e["type"] for e in errors}
    assert "env_missing" in kinds or "file_missing" in kinds


def test_build_agent_config_merges_provider_and_agent():
    resolved = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "base"}},
        "agents": {"default": {"provider": "dummy", "model": "override"}},
    }

    cfg = build_agent_config(resolved, "default")
    assert cfg["provider"] == "dummy_provider"
    assert cfg["model"] == "override"


def test_build_agent_config_excludes_agent_display_metadata():
    resolved = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "base"}
        },
        "agents": {
            "default": {
                "provider": "dummy",
                "display": {
                    "title": "Default Agent",
                    "description": "Visible only to application clients.",
                    "order": 10,
                },
            }
        },
    }

    cfg = build_agent_config(resolved, "default")

    assert "display" not in cfg


def test_resolve_config_mixins_applies_ordered_mixins_and_local_override():
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "base": {"model": "first", "temperature": 0.1},
                "second": {"model": "second", "top_p": 0.9},
            },
            "providers": {
                "dummy": {
                    "provider": "dummy_provider",
                    "mixin_refs": ["base", "second"],
                    "model": "local",
                }
            },
            "agents": {"default": {"provider": "dummy"}},
        }
    )

    assert errors == []
    provider = resolved["providers"]["dummy"]
    assert provider["model"] == "local"
    assert provider["temperature"] == 0.1
    assert provider["top_p"] == 0.9
    assert "mixin_refs" not in provider


def test_resolve_config_mixins_supports_deep_merge():
    resolved, errors = resolve_config_mixins(
        {
            "mixin_policy": {"default_merge": "deep"},
            "mixins": {
                "system-base": {
                    "system_message": {
                        "variables": {
                            "A": {"text": "alpha"},
                        }
                    }
                }
            },
            "providers": {
                "dummy": {
                    "provider": "dummy_provider",
                    "mixin_refs": ["system-base"],
                }
            },
            "agents": {
                "default": {
                    "provider": "dummy",
                    "system_message": {
                        "template": "{{A}} {{B}}",
                        "variables": {
                            "B": {"text": "beta"},
                        },
                    },
                }
            },
        }
    )

    assert errors == []
    cfg = build_agent_config(resolved, "default")
    assert cfg["system_message"]["variables"]["A"]["text"] == "alpha"
    assert cfg["system_message"]["variables"]["B"]["text"] == "beta"
    assert cfg["system_message"]["template"] == "{{A}} {{B}}"


def test_resolve_config_mixins_recursive_mixins_and_plugin_fields():
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "plugin-base": {"plugins": ["tests.dummy_provider.DummyProvider"]},
                "provider-base": {
                    "mixin_refs": ["plugin-base"],
                    "provider": "dummy_provider",
                    "model": "base-model",
                },
            },
            "providers": {"dummy": {"mixin_refs": ["provider-base"]}},
            "agents": {"default": {"provider": "dummy"}},
        }
    )

    assert errors == []
    provider = resolved["providers"]["dummy"]
    assert provider["provider"] == "dummy_provider"
    assert provider["model"] == "base-model"
    assert provider["plugins"] == ["tests.dummy_provider.DummyProvider"]


def test_resolve_config_mixins_reports_cycles():
    _resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "a": {"mixin_refs": ["b"], "model": "a"},
                "b": {"mixin_refs": ["a"], "model": "b"},
            },
            "providers": {"dummy": {"mixin_refs": ["a"], "provider": "dummy_provider"}},
            "agents": {"default": {"provider": "dummy"}},
        }
    )

    assert any(err["type"] == "mixin_cycle" for err in errors)


def test_resolve_config_mixins_reports_depth_limit():
    _resolved, errors = resolve_config_mixins(
        {
            "mixin_policy": {"max_depth": 2},
            "mixins": {
                "a": {"mixin_refs": ["b"]},
                "b": {"mixin_refs": ["c"]},
                "c": {"model": "deep"},
            },
            "providers": {"dummy": {"mixin_refs": ["a"], "provider": "dummy_provider"}},
            "agents": {"default": {"provider": "dummy"}},
        }
    )

    assert any(err["type"] == "mixin_depth_exceeded" for err in errors)


def test_resolve_config_mixins_shallow_merge_replaces_nested_dicts_by_default():
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "base": {
                    "system_message": {
                        "variables": {
                            "A": {"text": "alpha"},
                        }
                    }
                }
            },
            "providers": {"dummy": {"provider": "dummy_provider"}},
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_refs": ["base"],
                    "system_message": {
                        "template": "{{B}}",
                        "variables": {
                            "B": {"text": "beta"},
                        },
                    },
                }
            },
        }
    )

    assert errors == []
    cfg = build_agent_config(resolved, "default")
    assert cfg["system_message"]["template"] == "{{B}}"
    assert "A" not in cfg["system_message"]["variables"]
    assert cfg["system_message"]["variables"]["B"]["text"] == "beta"


def test_build_config_resolution_env_sets_derived_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "nested" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    env = build_config_resolution_env(config_path, env={})

    assert env["CONFIG_DIR"] == str(config_path.parent.resolve())
    assert env["WORKING_DIR"] == str(tmp_path.resolve())
    assert env["BUILTIN_PLUGINS"].endswith("plugins")
    assert env["CRYSTAL_DATA_DIR"] == str(Path.home() / ".crystal")


def test_build_config_resolution_env_allows_explicit_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"
    custom_plugins = tmp_path / "portable-plugins"
    custom_working_dir = tmp_path / "workspace"
    custom_config_dir = tmp_path / "portable-config"
    custom_data_dir = tmp_path / "portable-data"

    env = build_config_resolution_env(
        config_path,
        env={"WORKING_DIR": "ignored-process-env"},
        env_overrides={
            "CONFIG_DIR": str(custom_config_dir),
            "WORKING_DIR": str(custom_working_dir),
            "BUILTIN_PLUGINS": str(custom_plugins),
            "CRYSTAL_DATA_DIR": str(custom_data_dir),
        },
    )

    assert env["CONFIG_DIR"] == str(custom_config_dir)
    assert env["WORKING_DIR"] == str(custom_working_dir)
    assert env["BUILTIN_PLUGINS"] == str(custom_plugins)
    assert env["CRYSTAL_DATA_DIR"] == str(custom_data_dir)


def test_build_config_resolution_env_data_dir_overrides_config_dir(
    tmp_path, monkeypatch
):
    """CRYSTAL_DATA_DIR stays independent of the active config file location."""

    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "portable-config" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    env = build_config_resolution_env(config_path, env={})

    assert env["CONFIG_DIR"] == str(config_path.parent.resolve())
    assert env["CRYSTAL_DATA_DIR"] == str(Path.home() / ".crystal")


def test_build_runtime_overlay_env_installs_derived_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"

    overlay = build_runtime_overlay_env(config_path)

    assert overlay["CONFIG_DIR"] == str(config_path.resolve().parent)
    assert overlay["WORKING_DIR"] == str(tmp_path.resolve())
    assert overlay["BUILTIN_PLUGINS"].endswith("plugins")
    assert overlay["CRYSTAL_DATA_DIR"] == str(Path.home() / ".crystal")


def test_build_runtime_overlay_env_honors_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"
    custom_data_dir = tmp_path / "portable-data"

    overlay = build_runtime_overlay_env(
        config_path, env_overrides={"CRYSTAL_DATA_DIR": str(custom_data_dir)}
    )

    assert overlay["CRYSTAL_DATA_DIR"] == str(custom_data_dir)


def test_resolve_placeholders_supports_crystal_data_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"
    data_dir = tmp_path / "portable-data"

    env = build_config_resolution_env(
        config_path,
        env={},
        env_overrides={"CRYSTAL_DATA_DIR": str(data_dir)},
    )

    resolved, errors = resolve_placeholders(
        {"journal_path": "${env:CRYSTAL_DATA_DIR}/auth/usage-journal.ndjson"},
        env=env,
    )

    assert errors == []
    assert resolved["journal_path"] == f"{data_dir}/auth/usage-journal.ndjson"


def test_build_config_resolution_env_uses_config_env_below_process_env(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"

    env = build_config_resolution_env(
        config_path,
        env={"FROM_PROCESS": "process", "SHARED": "process"},
        config_env={"FROM_CONFIG_ENV": "config", "SHARED": "config"},
        env_overrides={"FROM_OVERRIDE": "override"},
    )

    assert env["FROM_CONFIG_ENV"] == "config"
    assert env["FROM_PROCESS"] == "process"
    assert env["FROM_OVERRIDE"] == "override"
    assert env["SHARED"] == "process"


def test_resolve_placeholders_supports_config_env_locations(tmp_path, monkeypatch):
    config_dir = tmp_path / "config-dir"
    workspace_dir = tmp_path / "workspace"
    plugins_dir = tmp_path / "plugins-dir"
    config_dir.mkdir()
    workspace_dir.mkdir()
    plugins_dir.mkdir()
    (config_dir / "system.txt").write_text("config file", encoding="utf-8")
    (workspace_dir / "AGENTS.md").write_text("workspace file", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    config_path = config_dir / "config.json"
    env = build_config_resolution_env(
        config_path,
        env={},
        env_overrides={
            "CONFIG_DIR": str(config_dir),
            "WORKING_DIR": str(workspace_dir),
            "BUILTIN_PLUGINS": str(plugins_dir),
        },
    )

    resolved, errors = resolve_placeholders(
        {
            "plugin_path": "path:${env:BUILTIN_PLUGINS}/codex-tools",
            "system": "${file:${env:CONFIG_DIR}/system.txt}",
            "agents": "${file:${env:WORKING_DIR}/AGENTS.md}",
        },
        env=env,
    )

    assert errors == []
    assert resolved["plugin_path"] == f"path:{plugins_dir}/codex-tools"
    assert resolved["system"] == "config file"
    assert resolved["agents"] == "workspace file"


def test_agent_application_accepts_env_overrides(tmp_path):
    config_dir = tmp_path / "config-dir"
    workspace_dir = tmp_path / "workspace"
    config_dir.mkdir()
    workspace_dir.mkdir()

    cfg = {
        "plugin_cache_dir": "${env:CONFIG_DIR}/plugin-cache",
        "providers": {
            "dummy": {
                "provider": "dummy_provider",
                "model": "base-model",
                "working_directory": "${env:WORKING_DIR}",
            }
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    config_path = config_dir / "config.json"
    config_path.write_text(__import__("json").dumps(cfg), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        env_overrides={
            "CONFIG_DIR": str(config_dir),
            "WORKING_DIR": str(workspace_dir),
        },
    )

    assert app._config["plugin_cache_dir"] == str(config_dir / "plugin-cache")
    assert app._agent_base_configs["default"]["working_directory"] == str(workspace_dir)


def test_agent_application_rejects_invalid_mixin_configs(tmp_path):
    cfg = {
        "mixins": {"broken": {"mixin_refs": ["missing"], "model": "base"}},
        "providers": {
            "dummy": {"mixin_refs": ["broken"], "provider": "dummy_provider"}
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {"default": {"provider": "dummy"}},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(__import__("json").dumps(cfg), encoding="utf-8")

    try:
        AgentApplication(
            str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore
        )
    except RuntimeError as exc:
        assert "Configuration resolution failed" in str(exc)
        assert "mixin_missing" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected AgentApplication to reject invalid mixin config")


def test_agent_application_resolves_system_message_config_values(tmp_path):
    config_dir = tmp_path / "config-dir"
    workspace_dir = tmp_path / "workspace"
    config_dir.mkdir()
    workspace_dir.mkdir()

    template_file = config_dir / "template.md"
    template_file.write_text("Template {{SECTION}}", encoding="utf-8")

    section_file = config_dir / "section.md"
    section_file.write_text("Rendered section", encoding="utf-8")

    runtime_file = config_dir / "runtime.py"
    runtime_file.write_text("cwd = 'runtime-cwd'\n", encoding="utf-8")

    cfg = {
        "providers": {
            "dummy": {
                "provider": "dummy_provider",
                "model": "base-model",
                "working_directory": "${env:WORKING_DIR}",
            }
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {
            "default": {
                "provider": "dummy",
                "system_message": {
                    "template": "${file:${env:CONFIG_DIR}/template.md}",
                    "runtime_code": "${env:CONFIG_DIR}/runtime.py",
                    "variables": {
                        "SECTION": {"text": "${file:${env:CONFIG_DIR}/section.md}"},
                        "SECTION_FILE": {"files": ["${env:CONFIG_DIR}/section.md"]},
                    },
                },
            }
        },
    }
    config_path = config_dir / "config.json"
    config_path.write_text(__import__("json").dumps(cfg), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        env_overrides={
            "CONFIG_DIR": str(config_dir),
            "WORKING_DIR": str(workspace_dir),
        },
    )

    system_message = app._agent_base_configs["default"]["system_message"]
    assert system_message["template"] == "Template {{SECTION}}"
    assert system_message["runtime_code"] == str(runtime_file)
    assert system_message["variables"]["SECTION"]["text"] == "Rendered section"
    assert system_message["variables"]["SECTION_FILE"]["files"] == [str(section_file)]
