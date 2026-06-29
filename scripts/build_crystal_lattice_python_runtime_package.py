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
import tempfile
import venv
import zipfile
import xml.etree.ElementTree as ET

from build_plugin_packaging_support import copytree_sanitized
from build_plugin_packaging_support import (
    discover_selected_bundled_plugin_names,
    is_python_project,
    resolve_local_project_names,
)
from build_crystal_lattice_binary import (
    normalize_arch,
    normalize_platform,
    prepare_cloud_runtime_build_context,
    read_project_version,
)


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "application" / "python"
APP_PACKAGE_DIR = APP_DIR / "agent_terminal_app"
CORE_DIR = ROOT / "core" / "python"
PLUGINS_DIR = ROOT / "plugins"
SCRIPTS_DIR = ROOT / "scripts"
BUILD_DIR = ROOT / "build" / "crystal-lattice-python-runtime"
RELEASES_DIR = ROOT / "dist" / "crystal-lattice-python-runtime"
PREINSTALLED_PLUGIN_MANIFEST = "preinstalled-plugins.json"
WINDOWS_LONG_PATH_MANIFEST = "python-long-path-aware.manifest"
MANIFEST_NS = "urn:schemas-microsoft-com:asm.v1"
MANIFEST_V3_NS = "urn:schemas-microsoft-com:asm.v3"
WINDOWS_SETTINGS_NS = "http://schemas.microsoft.com/SMI/2016/WindowsSettings"
ET.register_namespace("", MANIFEST_NS)
ET.register_namespace("asmv3", MANIFEST_V3_NS)
ET.register_namespace("ws2", WINDOWS_SETTINGS_NS)


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
    make_windows_python_long_path_aware(package_dir / "python", platform_name)
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
        shutil.copytree(
            python_runtime.expanduser().resolve(),
            destination,
            symlinks=True,
            ignore_dangling_symlinks=True,
        )
        prepare_copied_python_runtime(destination)
        return

    builder = venv.EnvBuilder(with_pip=True, symlinks=False, clear=True)
    builder.create(destination)


def prepare_copied_python_runtime(destination: Path) -> None:
    ensure_runtime_python_aliases(destination)
    python = runtime_python(destination)
    for marker in destination.glob("lib/python*/EXTERNALLY-MANAGED"):
        marker.unlink()
    windows_marker = destination / "Lib" / "EXTERNALLY-MANAGED"
    if windows_marker.exists():
        windows_marker.unlink()
    subprocess.run([str(python), "-m", "ensurepip", "--upgrade"], check=True)
    subprocess.run(
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
        check=True,
    )


def make_windows_python_long_path_aware(runtime_dir: Path, platform_name: str) -> None:
    if platform_name != "windows":
        return
    python = runtime_python(runtime_dir)
    manifest = runtime_dir / WINDOWS_LONG_PATH_MANIFEST
    write_long_path_manifest(manifest, executable=python)
    embed_manifest(python, manifest)


def write_long_path_manifest(path: Path, *, executable: Path | None = None) -> None:
    root = extract_manifest_root(executable) if executable is not None else None
    if root is None:
        root = ET.Element(
            f"{{{MANIFEST_NS}}}assembly",
            {"manifestVersion": "1.0"},
        )
    ensure_long_path_aware(root)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n',
        encoding="utf-8",
    )
    with path.open("ab") as f:
        tree.write(f, encoding="utf-8", xml_declaration=False)


def extract_manifest_root(executable: Path | None) -> ET.Element | None:
    if executable is None:
        return None
    mt = find_manifest_tool()
    if mt is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        extracted = Path(tmp) / "existing.manifest"
        result = subprocess.run(
            [mt, f"-inputresource:{executable};#1", f"-out:{extracted}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0 or not extracted.is_file():
            return None
        return ET.parse(extracted).getroot()


def ensure_long_path_aware(root: ET.Element) -> None:
    application = root.find(f"{{{MANIFEST_V3_NS}}}application")
    if application is None:
        application = ET.SubElement(root, f"{{{MANIFEST_V3_NS}}}application")
    windows_settings = application.find(f"{{{MANIFEST_V3_NS}}}windowsSettings")
    if windows_settings is None:
        windows_settings = ET.SubElement(
            application, f"{{{MANIFEST_V3_NS}}}windowsSettings"
        )
    existing = windows_settings.find(f"{{{WINDOWS_SETTINGS_NS}}}longPathAware")
    if existing is not None:
        existing.text = "true"
        return
    long_path_aware = ET.SubElement(
        windows_settings,
        f"{{{WINDOWS_SETTINGS_NS}}}longPathAware",
    )
    long_path_aware.text = "true"


def embed_manifest(executable: Path, manifest: Path) -> None:
    mt = find_manifest_tool()
    if mt is None:
        raise RuntimeError(
            "Windows manifest tool 'mt' is required to mark packaged Python "
            "as longPathAware, but it was not found on PATH or under the "
            "standard Windows Kits / Visual Studio install directories."
        )
    subprocess.run(
        [mt, "-manifest", str(manifest), f"-outputresource:{executable};#1"],
        check=True,
    )


def find_manifest_tool(
    *, windows_roots: list[Path] | None = None, assume_windows: bool | None = None
) -> str | None:
    mt = shutil.which("mt")
    if mt is not None:
        return mt
    if assume_windows is None:
        assume_windows = os.name == "nt"
    if not assume_windows:
        return None
    candidates: list[Path] = []
    if windows_roots is None:
        windows_roots = [
            Path(root_raw)
            for root_env in ("ProgramFiles(x86)", "ProgramFiles")
            if (root_raw := os.environ.get(root_env))
        ]
    for root in windows_roots:
        candidates.extend((root / "Windows Kits" / "10" / "bin").glob("*/*/mt.exe"))
        candidates.extend((root / "Microsoft Visual Studio").glob("**/mt.exe"))
    for candidate in sorted(candidates, reverse=True):
        if candidate.is_file():
            return str(candidate)
    return None


def runtime_python(runtime_dir: Path) -> Path:
    candidates = [
        runtime_dir / "python.exe",
        runtime_dir / "Scripts" / "python.exe",
        runtime_dir / "bin" / "python",
        runtime_dir / "bin" / "python3",
    ]
    candidates.extend(sorted(iter_versioned_python_binaries(runtime_dir / "bin")))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(f"Could not find Python executable in runtime: {runtime_dir}")


def ensure_runtime_python_aliases(runtime_dir: Path) -> None:
    bin_dir = runtime_dir / "bin"
    if not bin_dir.is_dir():
        return
    versioned = sorted(iter_versioned_python_binaries(bin_dir))
    if not versioned:
        return
    target = versioned[-1]
    for alias_name in ("python", "python3"):
        alias = bin_dir / alias_name
        if not alias.exists():
            alias.symlink_to(target.name)


def iter_versioned_python_binaries(bin_dir: Path) -> list[Path]:
    return [
        path
        for path in bin_dir.glob("python3.*")
        if path.is_file()
        and os.access(path, os.X_OK)
        and path.name.removeprefix("python").replace(".", "").isdigit()
    ]


def stage_repo_like_runtime(package_dir: Path) -> None:
    copytree_sanitized(CORE_DIR, package_dir / "core" / "python")
    copytree_sanitized(APP_DIR, package_dir / "application" / "python")
    copytree_sanitized(PLUGINS_DIR, package_dir / "plugins")
    scripts_target = package_dir / "scripts"
    scripts_target.mkdir(parents=True, exist_ok=True)
    for script_name in (
        "build_plugin_packaging_support.py",
        "build_cloud_runtime_plugin_bundle.py",
        "build_crystal_lattice_binary.py",
        "prepare_cloud_runtime_build_context.py",
    ):
        shutil.copy2(SCRIPTS_DIR / script_name, scripts_target / script_name)

    prepare_cloud_runtime_build_context(package_dir / "cloud_runtime")

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
        "../../../" + package_python(package_dir).relative_to(package_dir).as_posix()
    )
    manifest = {
        "schema_version": 1,
        "layout": "python-runtime",
        "bundle_paths": {
            "builtin_plugins": "../../../plugins",
            "bundle_script": "../../../scripts/build_crystal_lattice_binary.py",
            "cloud_runtime_build_context": "../../../cloud_runtime",
            "cloud_runtime_dockerfile": "../../../cloud_runtime/Dockerfile",
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
        python_executable = str(
            package_python(package_dir).relative_to(package_dir)
        ).replace("/", "\\")
        scripts_dir = package_dir / "Scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (scripts_dir / "crystal-lattice.cmd").write_text(
            "@echo off\r\n"
            "set ROOT=%~dp0..\\\r\n"
            "set CRYSTAL_RUNTIME_LAYOUT=%ROOT%application\\python\\agent_terminal_app\\runtime_layout.json\r\n"
            f"set CRYSTAL_PLUGIN_PYTHON=%ROOT%{python_executable}\r\n"
            "set PYTHONPATH=%ROOT%core\\python;%ROOT%application\\python;%PYTHONPATH%\r\n"
            f'"%ROOT%{python_executable}" -m agent_terminal_app %*\r\n',
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
    dependency_project_names = local_project_names - selected_plugin_names
    install_project_groups = [
        [
            plugins_root / name
            for name in sorted(dependency_project_names)
            if is_python_project(plugins_root / name)
        ],
        [
            plugins_root / name
            for name in sorted(selected_plugin_names)
            if is_python_project(plugins_root / name)
        ],
    ]
    for projects in install_project_groups:
        if not projects:
            continue
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
    windows_venv_python = package_dir / "python" / "Scripts" / "python.exe"
    if windows_venv_python.is_file():
        return windows_venv_python
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
        package_dir / "scripts" / "build_plugin_packaging_support.py",
        package_dir / "scripts" / "prepare_cloud_runtime_build_context.py",
        package_dir / "cloud_runtime" / "Dockerfile",
        package_dir / "cloud_runtime" / "runtime.py",
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
