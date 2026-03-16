"""Config resolution tests for the application layer."""

from __future__ import annotations

from agent_app.application_future import AgentApplication
from agent_app.config import (
    build_config_resolution_env,
    load_raw_config,
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


def test_build_config_resolution_env_sets_derived_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "nested" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    env = build_config_resolution_env(config_path, env={})

    assert env["CONFIG_DIR"] == str(config_path.parent.resolve())
    assert env["WORKING_DIR"] == str(tmp_path.resolve())
    assert env["BUILTIN_PLUGINS"].endswith("plugins")


def test_build_config_resolution_env_allows_explicit_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.json"
    custom_plugins = tmp_path / "portable-plugins"
    custom_working_dir = tmp_path / "workspace"
    custom_config_dir = tmp_path / "portable-config"

    env = build_config_resolution_env(
        config_path,
        env={"WORKING_DIR": "ignored-process-env"},
        env_overrides={
            "CONFIG_DIR": str(custom_config_dir),
            "WORKING_DIR": str(custom_working_dir),
            "BUILTIN_PLUGINS": str(custom_plugins),
        },
    )

    assert env["CONFIG_DIR"] == str(custom_config_dir)
    assert env["WORKING_DIR"] == str(custom_working_dir)
    assert env["BUILTIN_PLUGINS"] == str(custom_plugins)


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
