#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import venv
import zipfile

from build_cloud_runtime_plugin_bundle import copytree_sanitized
from build_cloud_runtime_plugin_bundle import (
    discover_selected_bundled_plugin_names,
    is_python_project,
    resolve_local_project_names,
)
from build_crystal_lattice_binary import (
    normalize_arch,
    normalize_platform,
    read_project_version,
)


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "application" / "python"
APP_PACKAGE_DIR = APP_DIR / "agent_terminal_app"
CORE_DIR = ROOT / "core" / "python"
PLUGINS_DIR = ROOT / "plugins"
SCRIPTS_DIR = ROOT / "scripts"
CLOUD_RUNTIME_DOCKERFILE = ROOT / "cloud-orchestrator" / "runtime" / "python"
BUILD_DIR = ROOT / "build" / "crystal-lattice-python-runtime"
RELEASES_DIR = ROOT / "dist" / "crystal-lattice-python-runtime"
PREINSTALLED_PLUGIN_MANIFEST = "preinstalled-plugins.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the full bundled-Python Crystal Lattice package."
    )
    parser.add_argument(
        "--version", default=None, help="override version used in artifact names"
    )
    parser.add_argument(
        "--platform", dest="platform_name", default=None, help="override platform name"
    )
    parser.add_argument("--arch", default=None, help="override architecture name")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="directory where release archives are written",
    )
    parser.add_argument(
        "--python-runtime",
        type=Path,
        default=None,
        help=(
            "existing Python runtime directory to copy into the package. When "
            "omitted, a local venv-style runtime is created for the current "
            "platform."
        ),
    )
    parser.add_argument(
        "--skip-dependency-install",
        action="store_true",
        help="stage files and launchers but do not pip-install app dependencies",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="build the package directory but do not create a release archive",
    )
    args = parser.parse_args()

    path = build_python_runtime_package(
        version=args.version,
        platform_name=args.platform_name,
        arch=args.arch,
        release_dir=args.output,
        python_runtime=args.python_runtime,
        install_dependencies=not args.skip_dependency_install,
        create_release_archive=not args.no_archive,
    )
    print(f"Created bundled-Python package: {path}")


def build_python_runtime_package(
    *,
    version: str | None = None,
    platform_name: str | None = None,
    arch: str | None = None,
    release_dir: Path | None = None,
    python_runtime: Path | None = None,
    install_dependencies: bool = True,
    create_release_archive: bool = True,
) -> Path:
    version = version or read_project_version()
    platform_name = normalize_platform(platform_name or platform.system())
    arch = normalize_arch(arch or platform.machine())
    target_id = f"{platform_name}-{arch}"
    package_stem = f"crystal-lattice-python-runtime-v{version}-{target_id}"

    package_dir = BUILD_DIR / package_stem
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    stage_python_runtime(package_dir / "python", python_runtime=python_runtime)
    stage_repo_like_runtime(package_dir)
    write_preinstalled_plugins_manifest(package_dir, set())
    write_launchers(package_dir, platform_name=platform_name)
    write_manifest(package_dir, platform_name=platform_name, arch=arch, version=version)

    if install_dependencies:
        install_app_dependencies(package_dir)
        install_preinstalled_default_plugins(package_dir)

    verify_package_tree(package_dir)

    if not create_release_archive:
        return package_dir
    return create_archive(package_dir, package_stem, platform_name, release_dir)


def stage_python_runtime(destination: Path, *, python_runtime: Path | None) -> None:
    if python_runtime is not None:
        copytree_sanitized(python_runtime.expanduser().resolve(), destination)
        return

    builder = venv.EnvBuilder(with_pip=True, symlinks=False, clear=True)
    builder.create(destination)


def stage_repo_like_runtime(package_dir: Path) -> None:
    copytree_sanitized(CORE_DIR, package_dir / "core" / "python")
    copytree_sanitized(APP_DIR, package_dir / "application" / "python")
    copytree_sanitized(PLUGINS_DIR, package_dir / "plugins")
    scripts_target = package_dir / "scripts"
    scripts_target.mkdir(parents=True, exist_ok=True)
    for script_name in (
        "build_cloud_runtime_plugin_bundle.py",
        "build_crystal_lattice_binary.py",
    ):
        shutil.copy2(SCRIPTS_DIR / script_name, scripts_target / script_name)

    dockerfile_target = package_dir / "cloud-orchestrator" / "runtime" / "python"
    dockerfile_target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        CLOUD_RUNTIME_DOCKERFILE / "Dockerfile", dockerfile_target / "Dockerfile"
    )

    write_runtime_layout(package_dir)


def write_runtime_layout(package_dir: Path) -> None:
    manifest_path = (
        package_dir
        / "application"
        / "python"
        / "agent_terminal_app"
        / "runtime_layout.json"
    )
    python_executable = (
        "../../../python/python.exe"
        if os.name == "nt"
        else "../../../python/bin/python"
    )
    manifest = {
        "schema_version": 1,
        "layout": "python-runtime",
        "bundle_paths": {
            "builtin_plugins": "../../../plugins",
            "bundle_script": "../../../scripts/build_crystal_lattice_binary.py",
            "cloud_runtime_build_context": "../../..",
            "cloud_runtime_dockerfile": "../../../cloud-orchestrator/runtime/python/Dockerfile",
            "config_examples": ".",
            "default_config_template": "default_config",
            "preinstalled_plugin_manifest": f"../../../{PREINSTALLED_PLUGIN_MANIFEST}",
            "python_executable": python_executable,
            "root_system_messages": "system_messages",
        },
        "user_paths": {
            "default_config": "~/.crystal/config.json",
            "default_sessions_dir": "./.crystal/sessions",
            "home_config": "~/.crystal/config.json",
            "local_config": "./.crystal/config.json",
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_launchers(package_dir: Path, *, platform_name: str) -> None:
    bin_dir = package_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    if platform_name == "windows":
        scripts_dir = package_dir / "Scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (scripts_dir / "crystal-lattice.cmd").write_text(
            "@echo off\r\n"
            "set ROOT=%~dp0..\\\r\n"
            "set CRYSTAL_RUNTIME_LAYOUT=%ROOT%application\\python\\agent_terminal_app\\runtime_layout.json\r\n"
            "set CRYSTAL_PLUGIN_PYTHON=%ROOT%python\\python.exe\r\n"
            "set PYTHONPATH=%ROOT%core\\python;%ROOT%application\\python;%PYTHONPATH%\r\n"
            '"%ROOT%python\\python.exe" -m agent_terminal_app %*\r\n',
            encoding="utf-8",
        )
        return

    launcher = bin_dir / "crystal-lattice"
    launcher.write_text(
        "#!/usr/bin/env sh\n"
        "set -eu\n"
        'ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)\n'
        'export CRYSTAL_RUNTIME_LAYOUT="$ROOT/application/python/agent_terminal_app/runtime_layout.json"\n'
        'export CRYSTAL_PLUGIN_PYTHON="$ROOT/python/bin/python"\n'
        'export PYTHONPATH="$ROOT/core/python:$ROOT/application/python${PYTHONPATH:+:$PYTHONPATH}"\n'
        'exec "$ROOT/python/bin/python" -m agent_terminal_app "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)


def install_app_dependencies(package_dir: Path) -> None:
    python = package_python(package_dir)
    subprocess.run(
        [str(python), "-m", "pip", "install", "--upgrade", str(CORE_DIR), str(APP_DIR)],
        cwd=str(ROOT),
        check=True,
    )
    subprocess.run(
        [str(python), "-m", "pip", "install", "--upgrade", "pyinstaller>=6.0"],
        cwd=str(ROOT),
        check=True,
    )


def install_preinstalled_default_plugins(package_dir: Path) -> None:
    plugins_root = package_dir / "plugins"
    default_config = (
        package_dir
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    selected_plugin_names = discover_selected_bundled_plugin_names(
        default_config, plugins_root
    )
    local_project_names = resolve_local_project_names(
        selected_plugin_names, plugins_root
    )
    projects = [
        plugins_root / name
        for name in sorted(local_project_names)
        if is_python_project(plugins_root / name)
    ]
    if projects:
        subprocess.run(
            [
                str(package_python(package_dir)),
                "-m",
                "pip",
                "install",
                "--upgrade",
                *map(str, projects),
            ],
            cwd=str(package_dir),
            check=True,
        )
    write_preinstalled_plugins_manifest(package_dir, local_project_names)


def write_preinstalled_plugins_manifest(
    package_dir: Path, plugin_names: set[str]
) -> Path:
    plugins = [
        {"name": name, "path": f"plugins/{name}"}
        for name in sorted(plugin_names)
        if (package_dir / "plugins" / name).is_dir()
    ]
    manifest = {
        "schema_version": 1,
        "plugin_paths": [plugin["path"] for plugin in plugins],
        "plugins": plugins,
    }
    path = package_dir / PREINSTALLED_PLUGIN_MANIFEST
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def package_python(package_dir: Path) -> Path:
    windows_python = package_dir / "python" / "python.exe"
    if windows_python.is_file():
        return windows_python
    return package_dir / "python" / "bin" / "python"


def write_manifest(
    package_dir: Path, *, platform_name: str, arch: str, version: str
) -> None:
    manifest = {
        "schema_version": 1,
        "layout": "python-runtime",
        "platform": platform_name,
        "arch": arch,
        "version": version,
        "supports_dynamic_plugin_install": True,
        "supports_optimized_bundle_build": True,
    }
    (package_dir / "runtime-package.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def verify_package_tree(package_dir: Path) -> None:
    required = [
        package_python(package_dir),
        package_dir / "application" / "python" / "agent_terminal_app" / "__main__.py",
        package_dir
        / "application"
        / "python"
        / "agent_terminal_app"
        / "runtime_layout.json",
        package_dir / "core" / "python" / "agent_app",
        package_dir / "core" / "python" / "agent_core",
        package_dir / "plugins" / "message-export-actions" / "agent_plugin.json",
        package_dir / PREINSTALLED_PLUGIN_MANIFEST,
        package_dir / "scripts" / "build_crystal_lattice_binary.py",
        package_dir / "scripts" / "build_cloud_runtime_plugin_bundle.py",
        package_dir / "runtime-package.json",
    ]
    if os.name == "nt":
        required.append(package_dir / "Scripts" / "crystal-lattice.cmd")
    else:
        required.append(package_dir / "bin" / "crystal-lattice")
    for path in required:
        if not path.exists():
            raise RuntimeError(f"Expected package path is missing: {path}")


def create_archive(
    package_dir: Path, package_stem: str, platform_name: str, release_dir: Path | None
) -> Path:
    releases_dir = (release_dir or RELEASES_DIR).expanduser().resolve()
    releases_dir.mkdir(parents=True, exist_ok=True)
    if platform_name == "windows":
        archive_path = releases_dir / f"{package_stem}.zip"
        if archive_path.exists():
            archive_path.unlink()
        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in sorted(package_dir.rglob("*")):
                archive.write(path, Path(package_stem) / path.relative_to(package_dir))
        return archive_path

    archive_path = releases_dir / f"{package_stem}.tar.gz"
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(package_dir, arcname=package_stem)
    return archive_path


if __name__ == "__main__":
    main()
