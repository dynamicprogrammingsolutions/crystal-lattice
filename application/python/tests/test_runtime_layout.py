from __future__ import annotations

import json
from pathlib import Path
import sys

from agent_terminal_app.__main__ import _ensure_default_config
from agent_terminal_app.runtime_layout import (
    _packaged_runtime_manifest,
    _render_shell_command,
    load_runtime_layout,
)


def test_source_runtime_layout_resolves_bundle_paths() -> None:
    layout = load_runtime_layout()
    repo_root = Path(__file__).resolve().parents[3]

    assert layout.layout == "source"
    assert layout.builtin_plugins == repo_root / "plugins"
    assert layout.cloud_runtime_build_context is None
    assert layout.cloud_runtime_dockerfile is None
    assert layout.env_overrides()["CLOUD_RUNTIME_BUILD_CONTEXT"].startswith(
        str(repo_root / "build" / "cloud-runtime-source-context-")
    )
    assert layout.default_config_template.name == "default_config"
    assert (layout.default_config_template / "config.json").is_file()
    assert layout.application_docs == repo_root / "application" / "python" / "docs"

    access = layout.application_env_overrides(
        config_path=repo_root / ".crystal" / "config.json",
        session_root=repo_root / ".crystal" / "sessions",
    )
    cli_argv = json.loads(access["CRYSTAL_LATTICE_CLI_ARGV_JSON"])
    assert cli_argv == [
        str(Path(sys.executable).resolve()),
        "-m",
        "agent_terminal_app",
        "--config",
        str((repo_root / ".crystal" / "config.json").resolve()),
        "--sessions-dir",
        str((repo_root / ".crystal" / "sessions").resolve()),
    ]
    assert access["CRYSTAL_LATTICE_PYTHON"] == str(Path(sys.executable).resolve())
    assert access["CRYSTAL_LATTICE_PYTHON_API_MODULE"] == "agent_terminal_app"
    assert access["CRYSTAL_LATTICE_CLI_COMMAND"] == " ".join(
        [
            str(Path(sys.executable).resolve()),
            "-m",
            "agent_terminal_app",
            "--config",
            str((repo_root / ".crystal" / "config.json").resolve()),
            "--sessions-dir",
            str((repo_root / ".crystal" / "sessions").resolve()),
        ]
    )
    assert access["CRYSTAL_LATTICE_DOCS"] == str(layout.application_docs)
    assert access["CRYSTAL_LATTICE_SYSTEM_MESSAGES"] == str(layout.root_system_messages)


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
    (manifest.parent / "docs").mkdir()
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "layout": "bundled",
                "bundle_paths": {
                    "application_docs": "docs",
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
    assert layout.env_overrides()["CLOUD_RUNTIME_BUILD_CONTEXT"] == str(
        tmp_path / "cloud_runtime"
    )
    assert layout.cloud_runtime_build_context == tmp_path / "cloud_runtime"
    assert layout.cloud_runtime_dockerfile == tmp_path / "cloud_runtime" / "Dockerfile"
    assert layout.user_path("default_sessions_dir") == (
        Path.cwd() / ".crystal" / "sessions"
    )
    access = layout.application_env_overrides(
        config_path=tmp_path / "config.json",
        session_root=tmp_path / "sessions",
        env_overrides={
            "CONFIG_DIR": "/must-not-win",
            "CRYSTAL_LATTICE_CONFIG": "/must-not-win",
            "CUSTOM_RUNTIME_VALUE": "preserved",
        },
    )
    cli_argv = json.loads(access["CRYSTAL_LATTICE_CLI_ARGV_JSON"])
    assert cli_argv == [
        str(Path(sys.executable).resolve()),
        "--config",
        str((tmp_path / "config.json").resolve()),
        "--sessions-dir",
        str((tmp_path / "sessions").resolve()),
    ]
    assert "CRYSTAL_LATTICE_PYTHON" not in access
    assert "CRYSTAL_LATTICE_PYTHON_API_MODULE" not in access
    assert access["CRYSTAL_LATTICE_CONFIG"] == str((tmp_path / "config.json").resolve())
    assert access["CONFIG_DIR"] == str(tmp_path.resolve())
    assert access["CRYSTAL_LATTICE_DOCS"] == str(manifest.parent / "docs")
    assert access["CRYSTAL_LATTICE_SYSTEM_MESSAGES"] == str(
        manifest.parent / "system_messages"
    )
    assert access["CUSTOM_RUNTIME_VALUE"] == "preserved"


def test_windows_shell_command_uses_powershell_call_operator() -> None:
    rendered = _render_shell_command(
        [r"C:\Program Files\Crystal Lattice\python.exe", "-m", "agent_terminal_app"],
        windows=True,
    )

    assert rendered == (
        "& 'C:\\Program Files\\Crystal Lattice\\python.exe' "
        "'-m' 'agent_terminal_app'"
    )


def test_packaged_runtime_manifest_is_found_from_posix_and_windows_python(
    tmp_path: Path,
) -> None:
    manifest = (
        tmp_path
        / "runtime"
        / "application"
        / "python"
        / "agent_terminal_app"
        / "runtime_layout.json"
    )
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}", encoding="utf-8")

    assert (
        _packaged_runtime_manifest(tmp_path / "runtime" / "python" / "bin" / "python")
        == manifest.resolve()
    )
    assert (
        _packaged_runtime_manifest(tmp_path / "runtime" / "python" / "python.exe")
        == manifest.resolve()
    )
    assert (
        _packaged_runtime_manifest(
            tmp_path / "runtime" / "python" / "Scripts" / "python.exe"
        )
        == manifest.resolve()
    )


def test_default_config_bootstrap_excludes_generated_private_state(
    tmp_path: Path,
) -> None:
    layout = load_runtime_layout()
    config_path = _ensure_default_config(tmp_path / ".crystal" / "config.json", layout)

    assert config_path.is_file()
    assert (config_path.parent / "system_messages").is_dir()
    assert (
        config_path.parent / "system_messages" / "helpers" / "crystal_lattice_access.py"
    ).is_file()
    assert (config_path.parent / "cloud-agent" / "profiles").is_dir()
    assert not (config_path.parent / "auth").exists()
    assert not (config_path.parent / ".plugin_cache").exists()
