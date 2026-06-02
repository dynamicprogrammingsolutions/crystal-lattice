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
    assert "python" in layout["bundle_paths"]["python_executable"]
    launcher = (
        package_dir / "Scripts" / "crystal-lattice.cmd"
        if os.name == "nt"
        else package_dir / "bin" / "crystal-lattice"
    )
    assert launcher.is_file()
    assert runtime_builder.package_python(package_dir).is_file()
    assert (package_dir / "scripts" / "build_crystal_lattice_binary.py").is_file()
    assert (package_dir / "plugins" / "message-export-actions").is_dir()

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
