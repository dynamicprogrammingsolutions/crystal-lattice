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

import build_crystal_lattice_python_runtime_package as runtime_builder  # type: ignore[import-not-found]  # noqa: E402
import build_crystal_lattice_binary as binary_builder  # type: ignore[import-not-found]  # noqa: E402
from agent_terminal_app.runtime_layout import load_runtime_layout  # noqa: E402


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
    assert layout["bundle_paths"]["application_docs"] == "../docs"
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
    assert not (package_dir / "application" / "python" / "scripts").exists()
    assert (package_dir / "plugins" / "message-export-actions").is_dir()
    assert (package_dir / "preinstalled-plugins.json").is_file()
    assert (
        package_dir / "application" / "python" / "docs" / "headless-agent-runs.md"
    ).is_file()

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

    runtime_layout = load_runtime_layout(layout_path)
    access = runtime_layout.application_env_overrides(
        config_path=tmp_path / "config.json",
        session_root=tmp_path / "sessions",
    )
    cli_argv = json.loads(access["CRYSTAL_LATTICE_CLI_ARGV_JSON"])
    assert cli_argv[:3] == [
        str(runtime_builder.package_python(package_dir)),
        "-m",
        "agent_terminal_app",
    ]
    assert cli_argv[-4:] == [
        "--config",
        str((tmp_path / "config.json").resolve()),
        "--sessions-dir",
        str((tmp_path / "sessions").resolve()),
    ]
    assert access["CRYSTAL_LATTICE_PYTHON"] == str(
        runtime_builder.package_python(package_dir)
    )
    assert (
        str(runtime_builder.package_python(package_dir))
        in access["CRYSTAL_LATTICE_CLI_COMMAND"]
    )
    assert access["CRYSTAL_LATTICE_PYTHON_API_MODULE"] == "agent_terminal_app"
    assert access["CRYSTAL_LATTICE_DOCS"] == str(
        package_dir / "application" / "python" / "docs"
    )


def test_runtime_application_staging_excludes_maintainer_and_cache_directories(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app_dir = tmp_path / "application" / "python"
    app_package_dir = app_dir / "agent_terminal_app"
    (app_package_dir / "cache" / "session-list").mkdir(parents=True)
    (app_package_dir / "cache" / "session-list" / "state.sqlite3").write_text(
        "generated",
        encoding="utf-8",
    )
    (app_dir / "scripts").mkdir()
    (app_dir / "scripts" / "maintainer.py").write_text(
        "raise SystemExit\n",
        encoding="utf-8",
    )
    (app_package_dir / "__main__.py").write_text("", encoding="utf-8")

    core_dir = tmp_path / "core" / "python"
    plugins_dir = tmp_path / "plugins"
    core_dir.mkdir(parents=True)
    plugins_dir.mkdir()
    package_dir = tmp_path / "package"

    monkeypatch.setattr(runtime_builder, "APP_DIR", app_dir)
    monkeypatch.setattr(runtime_builder, "CORE_DIR", core_dir)
    monkeypatch.setattr(runtime_builder, "PLUGINS_DIR", plugins_dir)
    monkeypatch.setattr(
        runtime_builder,
        "prepare_cloud_runtime_build_context",
        lambda _destination: None,
    )

    runtime_builder.stage_repo_like_runtime(package_dir)

    staged_application = package_dir / "application" / "python"
    assert not (staged_application / "scripts").exists()
    assert not (staged_application / "agent_terminal_app" / "cache").exists()
    assert (staged_application / "agent_terminal_app" / "__main__.py").is_file()


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


def test_intel_macos_runtime_pins_last_supported_cryptography_wheel(
    tmp_path: Path,
) -> None:
    package_dir = tmp_path / "package"

    constraints = runtime_builder.write_runtime_pip_constraints(
        package_dir,
        platform_name="darwin",
        arch="amd64",
    )

    assert constraints == package_dir / runtime_builder.PIP_CONSTRAINTS
    assert constraints.read_text(encoding="utf-8") == "cryptography==48.0.1\n"
    assert runtime_builder.package_pip_constraint_args(package_dir) == [
        "--constraint",
        str(constraints.resolve()),
    ]


def test_non_intel_runtime_does_not_write_crypto_constraint(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"

    assert (
        runtime_builder.write_runtime_pip_constraints(
            package_dir,
            platform_name="darwin",
            arch="arm64",
        )
        is None
    )
    assert runtime_builder.package_pip_constraint_args(package_dir) == []


def test_preinstalled_plugins_use_runtime_pip_constraint(
    tmp_path: Path, monkeypatch
) -> None:
    package_dir = tmp_path / "package"
    plugins = package_dir / "plugins"
    selected = plugins / "selected"
    selected.mkdir(parents=True)
    (selected / "pyproject.toml").write_text(
        "[build-system]\nrequires = []\n",
        encoding="utf-8",
    )
    default_config = (
        package_dir / "application" / "python" / "agent_terminal_app" / "default_config"
    )
    default_config.mkdir(parents=True)
    (default_config / "config.json").write_text("{}", encoding="utf-8")
    python = package_dir / "python" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    constraints = package_dir / runtime_builder.PIP_CONSTRAINTS
    constraints.write_text("cryptography==48.0.1\n", encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(
        runtime_builder,
        "discover_selected_bundled_plugin_names",
        lambda _config, _plugins_root: {"selected"},
    )
    monkeypatch.setattr(
        runtime_builder,
        "resolve_local_project_names",
        lambda _selected, _plugins_root: {"selected"},
    )
    monkeypatch.setattr(
        runtime_builder.subprocess,
        "run",
        lambda command, **_kwargs: (
            calls.append([str(value) for value in command])
            or subprocess.CompletedProcess(command, 0)
        ),
    )

    runtime_builder.install_preinstalled_default_plugins(package_dir)

    assert calls == [
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--constraint",
            str(constraints.resolve()),
            str(selected),
        ]
    ]


def test_application_dependencies_use_runtime_pip_constraint(
    tmp_path: Path, monkeypatch
) -> None:
    package_dir = tmp_path / "package"
    python = package_dir / "python" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    constraints = package_dir / runtime_builder.PIP_CONSTRAINTS
    constraints.write_text("cryptography==48.0.1\n", encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(
        runtime_builder.subprocess,
        "run",
        lambda command, **_kwargs: (
            calls.append([str(value) for value in command])
            or subprocess.CompletedProcess(command, 0)
        ),
    )

    runtime_builder.install_app_dependencies(package_dir)

    expected_prefix = [
        str(python),
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--constraint",
        str(constraints.resolve()),
    ]
    assert calls == [
        [*expected_prefix, str(runtime_builder.CORE_DIR), str(runtime_builder.APP_DIR)],
        [*expected_prefix, "pyinstaller>=6.0"],
    ]


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


def test_windows_launcher_uses_actual_packaged_python_path(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    manifest_dir = package_dir / "application" / "python" / "agent_terminal_app"
    manifest_dir.mkdir(parents=True)
    python = package_dir / "python" / "python.exe"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")

    runtime_builder.write_runtime_layout(package_dir)
    runtime_builder.write_launchers(package_dir, platform_name="windows")

    layout = json.loads((manifest_dir / "runtime_layout.json").read_text())
    assert layout["bundle_paths"]["python_executable"] == "../../../python/python.exe"
    assert layout["bundle_paths"]["application_docs"] == "../docs"

    launcher = (package_dir / "Scripts" / "crystal-lattice.cmd").read_text(
        encoding="utf-8"
    )
    assert "set CRYSTAL_PLUGIN_PYTHON=%ROOT%python\\python.exe" in launcher
    assert '"%ROOT%python\\python.exe" -m agent_terminal_app %*' in launcher


def test_optimized_layout_stages_docs_without_advertising_python_api(
    tmp_path: Path,
    monkeypatch,
) -> None:
    asset_root = tmp_path / "assets"
    monkeypatch.setattr(binary_builder, "ASSET_STAGE_DIR", asset_root)
    monkeypatch.setattr(
        binary_builder,
        "stage_bundled_plugins",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        binary_builder,
        "prepare_cloud_runtime_build_context",
        lambda *_args, **_kwargs: None,
    )

    binary_builder.prepare_staged_assets(set(), set())

    manifest = asset_root / "agent_terminal_app" / "runtime_layout.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["layout"] == "bundled"
    assert data["bundle_paths"]["application_docs"] == "docs"
    assert (
        asset_root / "agent_terminal_app" / "docs" / "headless-agent-runs.md"
    ).is_file()

    layout = load_runtime_layout(manifest)
    access = layout.application_env_overrides(
        config_path=tmp_path / "config.json",
        session_root=tmp_path / "sessions",
    )
    assert json.loads(access["CRYSTAL_LATTICE_CLI_ARGV_JSON"])[0] == str(
        Path(sys.executable).resolve()
    )
    assert str(Path(sys.executable).resolve()) in access["CRYSTAL_LATTICE_CLI_COMMAND"]
    assert "CRYSTAL_LATTICE_PYTHON" not in access
    assert "CRYSTAL_LATTICE_PYTHON_API_MODULE" not in access
    assert access["CRYSTAL_LATTICE_DOCS"] == str(
        asset_root / "agent_terminal_app" / "docs"
    )


def test_windows_long_path_manifest_preserves_existing_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "python.manifest"
    root = runtime_builder.ET.Element(
        f"{{{runtime_builder.MANIFEST_NS}}}assembly",
        {"manifestVersion": "1.0"},
    )
    runtime_builder.ET.SubElement(root, f"{{{runtime_builder.MANIFEST_NS}}}dependency")

    runtime_builder.ensure_long_path_aware(root)
    runtime_builder.ET.ElementTree(root).write(manifest, encoding="utf-8")
    text = manifest.read_text(encoding="utf-8")

    assert "dependency" in text
    assert "longPathAware" in text
    assert "true" in text


def test_windows_runtime_build_embeds_long_path_manifest(
    tmp_path: Path, monkeypatch
) -> None:
    runtime_dir = tmp_path / "python"
    python = runtime_dir / "python.exe"
    python.parent.mkdir()
    python.write_text("", encoding="utf-8")
    calls: list[tuple[Path, Path]] = []

    monkeypatch.setattr(
        runtime_builder,
        "embed_manifest",
        lambda exe, manifest: calls.append((exe, manifest)),
    )

    runtime_builder.make_windows_python_long_path_aware(runtime_dir, "windows")

    assert calls == [(python, runtime_dir / runtime_builder.WINDOWS_LONG_PATH_MANIFEST)]
    assert "longPathAware" in calls[0][1].read_text(encoding="utf-8")


def test_find_manifest_tool_checks_windows_kits(tmp_path: Path, monkeypatch) -> None:
    mt = tmp_path / "Windows Kits" / "10" / "bin" / "10.0.26100.0" / "x64" / "mt.exe"
    mt.parent.mkdir(parents=True)
    mt.write_text("", encoding="utf-8")

    monkeypatch.setattr(runtime_builder.shutil, "which", lambda _name: None)

    assert runtime_builder.find_manifest_tool(
        windows_roots=[tmp_path], assume_windows=True
    ) == str(mt)


def test_core_declares_colorama_for_windows_structlog_colors() -> None:
    """The Windows runtime must ship colorama for structlog's ConsoleRenderer.

    ``agent_core.utils.configure_logging`` renders colored output by default;
    structlog raises ``SystemError`` on Windows when colors are enabled and
    colorama is missing. The dependency marker keeps macOS/Linux installs
    unchanged while covering both the release build job and the packaged
    runtime, which install ``core/python`` with pip.
    """
    import tomllib

    pyproject = tomllib.loads(
        (ROOT / "core" / "python" / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = pyproject["project"]["dependencies"]

    matching = [
        dep
        for dep in dependencies
        if dep.startswith("colorama") and "sys_platform == 'win32'" in dep
    ]
    assert matching, (
        "core/python must declare a Windows colorama dependency "
        f"(e.g. \"colorama>=0.4.6; sys_platform == 'win32'\"), found: {dependencies}"
    )
