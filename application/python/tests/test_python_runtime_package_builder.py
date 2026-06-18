from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_crystal_lattice_python_runtime_package as runtime_builder


def test_python_runtime_package_stages_launcher_layout_and_bundle_script(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(runtime_builder, "BUILD_DIR", tmp_path / "build")

    package_dir = runtime_builder.build_python_runtime_package(
        version="0.0.0-test",
        release_dir=tmp_path / "dist",
        install_dependencies=False,
        create_release_archive=False,
    )

    layout_path = (
        package_dir
        / "application"
        / "python"
        / "agent_terminal_app"
        / "runtime_layout.json"
    )
    layout = json.loads(layout_path.read_text(encoding="utf-8"))

    assert layout["layout"] == "python-runtime"
    assert layout["bundle_paths"]["builtin_plugins"] == "../../../plugins"
    assert layout["bundle_paths"]["bundle_script"] == (
        "../../../scripts/build_crystal_lattice_binary.py"
    )
    assert layout["bundle_paths"]["preinstalled_plugin_manifest"] == (
        "../../../preinstalled-plugins.json"
    )
    assert "python" in layout["bundle_paths"]["python_executable"]
    launcher = (
        package_dir / "Scripts" / "crystal-lattice.cmd"
        if os.name == "nt"
        else package_dir / "bin" / "crystal-lattice"
    )
    assert launcher.is_file()
    assert runtime_builder.package_python(package_dir).is_file()
    assert (package_dir / "scripts" / "build_crystal_lattice_binary.py").is_file()
    assert (package_dir / "scripts" / "build_plugin_packaging_support.py").is_file()
    assert (package_dir / "plugins" / "message-export-actions").is_dir()
    assert (package_dir / "preinstalled-plugins.json").is_file()

    output = subprocess.check_output(
        [str(launcher), "--runtime-layout-json"],
        cwd=str(tmp_path),
        text=True,
    )
    resolved = json.loads(output)
    assert resolved["layout"] == "python-runtime"
    assert resolved["env_overrides"]["BUILTIN_PLUGINS"] == str(package_dir / "plugins")
    assert resolved["env_overrides"]["CRYSTAL_PLUGIN_PYTHON"] == str(
        runtime_builder.package_python(package_dir)
    )
    assert resolved["env_overrides"]["CRYSTAL_PREINSTALLED_PLUGIN_MANIFEST"] == str(
        package_dir / "preinstalled-plugins.json"
    )


def test_optimized_bundle_layout_rejects_bundle_command(tmp_path: Path) -> None:
    manifest = tmp_path / "agent_terminal_app" / "runtime_layout.json"
    manifest.parent.mkdir()
    for directory in ("bundled_plugins", "default_config", "system_messages"):
        (tmp_path / directory).mkdir()
    (tmp_path / "default_config" / "config.json").write_text("{}", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "layout": "bundled",
                "bundle_paths": {
                    "builtin_plugins": "../bundled_plugins",
                    "config_examples": "../default_config",
                    "default_config_template": "../default_config",
                    "root_system_messages": "../system_messages",
                },
                "user_paths": {
                    "default_config": "~/.crystal/config.json",
                    "default_sessions_dir": "./.crystal/sessions",
                    "home_config": "~/.crystal/config.json",
                    "local_config": "./.crystal/config.json",
                },
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_terminal_app",
            "bundle",
            "--config",
            str(config),
        ],
        cwd=str(tmp_path),
        env={
            **os.environ,
            "CRYSTAL_RUNTIME_LAYOUT": str(manifest),
            "PYTHONPATH": os.pathsep.join(
                [str(ROOT / "application" / "python"), str(ROOT / "core" / "python")]
            ),
        },
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 2
    assert "only supported from the full bundled-Python" in result.stderr


def test_python_runtime_preinstalled_default_plugins_manifest_and_install(
    tmp_path: Path, monkeypatch
) -> None:
    package_dir = tmp_path / "package"
    plugins = package_dir / "plugins"
    for name in ("selected", "shared", "non-default"):
        plugin_dir = plugins / name
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "pyproject.toml").write_text(
            "[build-system]\nrequires = []\n", encoding="utf-8"
        )
    default_config = (
        package_dir / "application" / "python" / "agent_terminal_app" / "default_config"
    )
    default_config.mkdir(parents=True)
    (default_config / "config.json").write_text("{}", encoding="utf-8")
    python = package_dir / "python" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")

    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append([str(value) for value in command])
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(
        runtime_builder,
        "discover_selected_bundled_plugin_names",
        lambda _config, _plugins_root: {"selected"},
    )
    monkeypatch.setattr(
        runtime_builder,
        "resolve_local_project_names",
        lambda _selected, _plugins_root: {"selected", "shared"},
    )
    monkeypatch.setattr(runtime_builder.subprocess, "run", fake_run)

    runtime_builder.install_preinstalled_default_plugins(package_dir)

    assert calls == [
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            str(plugins / "shared"),
        ],
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            str(plugins / "selected"),
        ],
    ]
    manifest = json.loads(
        (package_dir / "preinstalled-plugins.json").read_text(encoding="utf-8")
    )
    assert manifest["plugin_paths"] == ["plugins/selected", "plugins/shared"]
    assert "plugins/non-default" not in manifest["plugin_paths"]


def test_prepare_copied_python_runtime_removes_external_management_marker(
    tmp_path: Path, monkeypatch
) -> None:
    runtime_dir = tmp_path / "python"
    python = runtime_dir / "bin" / "python"
    marker = runtime_dir / "lib" / "python3.11" / "EXTERNALLY-MANAGED"
    python.parent.mkdir(parents=True)
    marker.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    marker.write_text("managed by uv\n", encoding="utf-8")

    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append([str(value) for value in command])
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runtime_builder.subprocess, "run", fake_run)

    runtime_builder.prepare_copied_python_runtime(runtime_dir)

    assert not marker.exists()
    assert calls == [
        [str(python), "-m", "ensurepip", "--upgrade"],
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools",
            "wheel",
        ],
    ]


def test_prepare_copied_python_runtime_creates_posix_python_aliases(
    tmp_path: Path, monkeypatch
) -> None:
    runtime_dir = tmp_path / "python"
    versioned_python = runtime_dir / "bin" / "python3.11"
    config_script = runtime_dir / "bin" / "python3.11-config"
    versioned_python.parent.mkdir(parents=True)
    versioned_python.write_text("", encoding="utf-8")
    versioned_python.chmod(0o755)
    config_script.write_text("", encoding="utf-8")
    config_script.chmod(0o755)

    monkeypatch.setattr(
        runtime_builder.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0),
    )

    runtime_builder.prepare_copied_python_runtime(runtime_dir)

    assert (runtime_dir / "bin" / "python").resolve() == versioned_python
    assert (runtime_dir / "bin" / "python3").resolve() == versioned_python


def test_stage_python_runtime_copies_runtime_build_directories(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source-python"
    destination = tmp_path / "destination-python"
    python = source / "bin" / "python"
    pip_build = (
        source
        / "lib"
        / "python3.11"
        / "site-packages"
        / "pip"
        / "_internal"
        / "operations"
        / "build"
        / "__init__.py"
    )
    python.parent.mkdir(parents=True)
    pip_build.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    python.chmod(0o755)
    pip_build.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        runtime_builder.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0),
    )

    runtime_builder.stage_python_runtime(destination, python_runtime=source)

    assert (destination / pip_build.relative_to(source)).is_file()
