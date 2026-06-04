from __future__ import annotations

import json
from pathlib import Path

from agent_terminal_app.__main__ import _ensure_default_config
from agent_terminal_app.runtime_layout import load_runtime_layout


def test_source_runtime_layout_resolves_bundle_paths() -> None:
    layout = load_runtime_layout()
    repo_root = Path(__file__).resolve().parents[3]

    assert layout.layout == "source"
    assert layout.builtin_plugins == repo_root / "plugins"
    assert layout.cloud_runtime_build_context is None
    assert layout.cloud_runtime_dockerfile is None
    assert layout.default_config_template.name == "default_config"
    assert (layout.default_config_template / "config.json").is_file()


def test_runtime_layout_resolves_user_paths_from_current_working_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest = tmp_path / "runtime_layout.json"
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "layout": "test",
                "bundle_paths": {
                    "builtin_plugins": "plugins",
                    "default_config_template": "default_config",
                    "config_examples": ".",
                    "root_system_messages": "system_messages",
                },
                "user_paths": {
                    "local_config": "./.crystal/config.json",
                    "home_config": "${env:CRYSTAL_TEST_HOME}/config.json",
                    "default_config": "~/config.json",
                    "default_sessions_dir": "./.crystal/sessions",
                },
            }
        ),
        encoding="utf-8",
    )

    cwd = tmp_path / "cwd"
    cwd.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.chdir(cwd)
    monkeypatch.setenv("CRYSTAL_TEST_HOME", str(fake_home))
    monkeypatch.setenv("HOME", str(fake_home))

    layout = load_runtime_layout(manifest)

    assert layout.builtin_plugins == tmp_path / "plugins"
    assert layout.user_path("local_config") == cwd / ".crystal" / "config.json"
    assert layout.user_path("home_config") == fake_home / "config.json"
    assert layout.user_path("default_config") == fake_home / "config.json"
    assert layout.user_path("default_sessions_dir") == cwd / ".crystal" / "sessions"


def test_bundled_runtime_layout_exposes_bundled_plugin_root(tmp_path: Path) -> None:
    manifest = tmp_path / "agent_terminal_app" / "runtime_layout.json"
    manifest.parent.mkdir()
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "layout": "bundled",
                "bundle_paths": {
                    "builtin_plugins": "../bundled_plugins",
                    "cloud_runtime_build_context": "../cloud_runtime",
                    "cloud_runtime_dockerfile": "../cloud_runtime/Dockerfile",
                    "default_config_template": "default_config",
                    "config_examples": ".",
                    "root_system_messages": "system_messages",
                },
                "user_paths": {
                    "local_config": "./.crystal/config.json",
                    "home_config": "~/.crystal/config.json",
                    "default_config": "~/.crystal/config.json",
                    "default_sessions_dir": "./.crystal/sessions",
                },
            }
        ),
        encoding="utf-8",
    )

    layout = load_runtime_layout(manifest)

    assert layout.builtin_plugins == tmp_path / "bundled_plugins"
    assert layout.env_overrides()["BUILTIN_PLUGINS"] == str(
        tmp_path / "bundled_plugins"
    )
    assert layout.cloud_runtime_build_context == tmp_path / "cloud_runtime"
    assert layout.cloud_runtime_dockerfile == tmp_path / "cloud_runtime" / "Dockerfile"
    assert layout.user_path("default_sessions_dir") == (
        Path.cwd() / ".crystal" / "sessions"
    )


def test_default_config_bootstrap_excludes_generated_private_state(
    tmp_path: Path,
) -> None:
    layout = load_runtime_layout()
    config_path = _ensure_default_config(tmp_path / ".crystal" / "config.json", layout)

    assert config_path.is_file()
    assert (config_path.parent / "system_messages").is_dir()
    assert (config_path.parent / "cloud-agent" / "profiles").is_dir()
    assert not (config_path.parent / "auth").exists()
    assert not (config_path.parent / ".plugin_cache").exists()
