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
from typing import Iterable
import zipfile

from build_plugin_packaging_support import (
    copy_local_project_sources,
    copytree_sanitized,
    discover_builtin_plugin_resource_paths as discover_builtin_plugin_resource_paths_for_config,
    discover_selected_bundled_plugin_names as discover_selected_bundled_plugin_names_for_config,
    resolve_local_project_names,
    stage_cloud_runtime_plugin_bundle,
    stage_preinstalled_plugin_metadata,
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "application" / "python"
APP_PACKAGE_DIR = APP_DIR / "agent_terminal_app"
CORE_DIR = ROOT / "core" / "python"
PLUGINS_DIR = ROOT / "plugins"
BUNDLED_PLUGINS_DIRNAME = "bundled_plugins"
CLOUD_RUNTIME_DIRNAME = "cloud_runtime"
PYPROJECT = APP_DIR / "pyproject.toml"
BUILD_DIR = ROOT / "build" / "crystal-lattice-binary"
PYINSTALLER_WORK_DIR = BUILD_DIR / "pyinstaller-work"
PYINSTALLER_SPEC_DIR = BUILD_DIR / "pyinstaller-spec"
ASSET_STAGE_DIR = BUILD_DIR / "assets"
RELEASES_DIR = ROOT / "dist" / "crystal-lattice"


APP_DEFAULT_CONFIG_EXCLUDED_DIRS = {
    ".plugin_cache",
    "auth",
    "__pycache__",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a PyInstaller onedir binary archive for Crystal Lattice."
    )
    parser.add_argument(
        "--version", default=None, help="override version used in artifact names"
    )
    parser.add_argument(
        "--platform", dest="platform_name", default=None, help="override platform name"
    )
    parser.add_argument("--arch", default=None, help="override architecture name")
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="prepare assets and archive an existing PyInstaller output",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="build the onedir output but do not create a release archive",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=(
            "config file used to select preinstalled plugins and bundled "
            "config template files"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="directory where release archives are written",
    )
    args = parser.parse_args()

    build_crystal_lattice_binary(
        version=args.version,
        platform_name=args.platform_name,
        arch=args.arch,
        skip_pyinstaller=args.skip_pyinstaller,
        no_archive=args.no_archive,
        config_path=args.config,
        release_dir=args.output,
    )


def build_crystal_lattice_binary(
    *,
    version: str | None = None,
    platform_name: str | None = None,
    arch: str | None = None,
    skip_pyinstaller: bool = False,
    no_archive: bool = False,
    config_path: Path | None = None,
    release_dir: Path | None = None,
) -> Path:
    version = version or read_project_version()
    platform_name = normalize_platform(platform_name or platform.system())
    arch = normalize_arch(arch or platform.machine())
    target_id = f"{platform_name}-{arch}"
    archive_stem = f"crystal-lattice-cli-v{version}-{target_id}"
    selected_config = (config_path or default_config_path()).expanduser().resolve()

    selected_plugin_names = discover_selected_bundled_plugin_names(selected_config)
    builtin_resource_paths = discover_builtin_plugin_resource_paths(selected_config)
    prepare_staged_assets(
        selected_plugin_names,
        builtin_resource_paths,
        selected_config=selected_config,
    )

    if not skip_pyinstaller:
        install_selected_bundled_plugins(selected_plugin_names)
        run_pyinstaller()

    output_dir = APP_DIR / "dist" / "crystal-lattice"
    verify_output_tree(output_dir)

    if not no_archive:
        archive_path = create_archive(
            output_dir,
            archive_stem,
            platform_name,
            release_dir=release_dir,
        )
        print(f"Created release archive: {archive_path}")
        return archive_path
    else:
        print(f"Built PyInstaller output: {output_dir}")
        return output_dir


def read_project_version() -> str:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = metadata["project"]["version"]
    if not isinstance(version, str) or not version:
        raise RuntimeError(
            "Could not read project.version from application/python/pyproject.toml"
        )
    return version


def normalize_platform(raw: str) -> str:
    value = raw.lower()
    if value.startswith("darwin") or value.startswith("mac"):
        return "darwin"
    if value.startswith("linux"):
        return "linux"
    if value.startswith("win"):
        return "windows"
    raise RuntimeError(f"Unsupported platform: {raw}")


def normalize_arch(raw: str) -> str:
    value = raw.lower()
    if value in {"x86_64", "amd64"}:
        return "amd64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    raise RuntimeError(f"Unsupported architecture: {raw}")


def default_config_path() -> Path:
    return APP_PACKAGE_DIR / "default_config" / "config.json"


def discover_selected_bundled_plugin_names(
    config_path: Path | None = None,
    *,
    cloud_disabled_plugin_specs: Iterable[str] | None = None,
) -> set[str]:
    return discover_selected_bundled_plugin_names_for_config(
        config_path or default_config_path(),
        PLUGINS_DIR,
        cloud_disabled_plugin_specs=cloud_disabled_plugin_specs,
    )


def discover_builtin_plugin_resource_paths(
    config_path: Path | None = None,
    *,
    cloud_disabled_plugin_specs: Iterable[str] | None = None,
) -> set[Path]:
    return discover_builtin_plugin_resource_paths_for_config(
        config_path or default_config_path(),
        PLUGINS_DIR,
        cloud_disabled_plugin_specs=cloud_disabled_plugin_specs,
    )


def prepare_staged_assets(
    selected_plugin_names: set[str],
    builtin_resource_paths: set[Path],
    *,
    selected_config: Path | None = None,
) -> None:
    if ASSET_STAGE_DIR.exists():
        shutil.rmtree(ASSET_STAGE_DIR)
    ASSET_STAGE_DIR.mkdir(parents=True, exist_ok=True)

    staged_app = ASSET_STAGE_DIR / "agent_terminal_app"
    staged_app.mkdir(parents=True, exist_ok=True)

    config_template_dir = (
        selected_config.expanduser().resolve().parent
        if selected_config is not None
        else APP_PACKAGE_DIR / "default_config"
    )
    copytree_sanitized(
        config_template_dir,
        staged_app / "default_config",
        excluded_dir_names=APP_DEFAULT_CONFIG_EXCLUDED_DIRS,
    )
    copytree_sanitized(
        APP_PACKAGE_DIR / "system_messages", staged_app / "system_messages"
    )

    for source in APP_PACKAGE_DIR.glob("*.json"):
        if source.name == "runtime_layout.json":
            continue
        shutil.copy2(source, staged_app / source.name)

    bundled_plugins_dir = ASSET_STAGE_DIR / BUNDLED_PLUGINS_DIRNAME
    stage_bundled_plugins(
        bundled_plugins_dir,
        selected_plugin_names=selected_plugin_names,
        builtin_resource_paths=builtin_resource_paths,
    )
    prepare_cloud_runtime_build_context(
        ASSET_STAGE_DIR / CLOUD_RUNTIME_DIRNAME,
        selected_config=selected_config,
    )

    bundled_manifest = {
        "schema_version": 1,
        "layout": "bundled",
        "bundle_paths": {
            "builtin_plugins": f"../{BUNDLED_PLUGINS_DIRNAME}",
            "cloud_runtime_build_context": f"../{CLOUD_RUNTIME_DIRNAME}",
            "cloud_runtime_dockerfile": f"../{CLOUD_RUNTIME_DIRNAME}/Dockerfile",
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
    (staged_app / "runtime_layout.json").write_text(
        json.dumps(bundled_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    entrypoint = ASSET_STAGE_DIR / "crystal_lattice_pyinstaller_entry.py"
    entrypoint.write_text(
        "from agent_terminal_app.__main__ import main\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )


def stage_bundled_plugins(
    destination: Path,
    *,
    selected_plugin_names: set[str],
    builtin_resource_paths: set[Path],
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted(PLUGINS_DIR.iterdir()):
        if not source.is_dir():
            continue
        target = destination / source.name
        if source.name not in selected_plugin_names:
            copytree_sanitized(source, target)
            continue
        stage_preinstalled_plugin_metadata(
            source,
            target,
            builtin_resource_paths=builtin_resource_paths,
        )

    manifest = {
        "schema_version": 1,
        "preinstalled_plugins": sorted(selected_plugin_names),
    }
    (destination / "bundled_plugins.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def install_selected_bundled_plugins(selected_plugin_names: set[str]) -> None:
    for plugin_name in sorted(
        resolve_local_project_names(selected_plugin_names, PLUGINS_DIR)
    ):
        plugin_dir = PLUGINS_DIR / plugin_name
        if (plugin_dir / "pyproject.toml").is_file() or (
            plugin_dir / "setup.py"
        ).is_file():
            run_pip_install(plugin_dir)


def run_pip_install(project_dir: Path) -> None:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", str(project_dir)],
        cwd=str(ROOT),
        check=True,
    )


def prepare_cloud_runtime_build_context(
    destination: Path,
    *,
    selected_config: Path | None = None,
    cloud_disabled_plugin_specs: Iterable[str] | None = None,
) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    runtime_assets = (
        PLUGINS_DIR
        / "cloud-agent-app"
        / "src"
        / "cloud_agent_app"
        / "bundled_runtime"
        / "python"
    )
    shutil.copy2(runtime_assets / "Dockerfile", destination / "Dockerfile")
    shutil.copy2(runtime_assets / "runtime.py", destination / "runtime.py")

    python_lib = destination / "python_lib"
    copytree_sanitized(CORE_DIR / "agent_core", python_lib / "agent_core")
    copytree_sanitized(CORE_DIR / "agent_app", python_lib / "agent_app")
    copytree_sanitized(CORE_DIR / "plugins", python_lib / "plugins")
    shutil.copy2(CORE_DIR / "sitecustomize.py", python_lib / "sitecustomize.py")
    copytree_sanitized(APP_PACKAGE_DIR, python_lib / "agent_terminal_app")
    stage_cloud_runtime_plugin_bundle(
        plugins_root=PLUGINS_DIR,
        selected_config=selected_config or default_config_path(),
        output=destination / "cloud-runtime-plugin-bundle",
        local_project_prefix="./plugin_sources",
        cloud_disabled_plugin_specs=cloud_disabled_plugin_specs,
    )
    local_project_names = resolve_local_project_names(
        discover_selected_bundled_plugin_names(
            selected_config or default_config_path(),
            cloud_disabled_plugin_specs=cloud_disabled_plugin_specs,
        ),
        PLUGINS_DIR,
    )
    copy_local_project_sources(
        destination / "plugin_sources",
        plugins_root=PLUGINS_DIR,
        local_project_names=local_project_names,
    )


def run_pyinstaller() -> None:
    entrypoint = ASSET_STAGE_DIR / "crystal_lattice_pyinstaller_entry.py"
    bundled_python_paths = discover_plugin_python_paths(
        ASSET_STAGE_DIR / BUNDLED_PLUGINS_DIRNAME
    )
    hidden_imports = sorted(
        {
            *discover_core_plugin_hidden_imports(CORE_DIR / "plugins"),
            *discover_plugin_hidden_imports(ASSET_STAGE_DIR / BUNDLED_PLUGINS_DIRNAME),
        }
    )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        "crystal-lattice",
        "--workpath",
        str(PYINSTALLER_WORK_DIR),
        "--specpath",
        str(PYINSTALLER_SPEC_DIR),
        "--distpath",
        str(APP_DIR / "dist"),
        "--paths",
        str(CORE_DIR),
        "--paths",
        str(APP_DIR),
        "--add-data",
        add_data_arg(ASSET_STAGE_DIR / "agent_terminal_app", "agent_terminal_app"),
        "--add-data",
        add_data_arg(
            ASSET_STAGE_DIR / BUNDLED_PLUGINS_DIRNAME, BUNDLED_PLUGINS_DIRNAME
        ),
        "--add-data",
        add_data_arg(ASSET_STAGE_DIR / CLOUD_RUNTIME_DIRNAME, CLOUD_RUNTIME_DIRNAME),
    ]
    for path in bundled_python_paths:
        command.extend(["--paths", str(path)])
    for module in discover_plugin_data_modules(
        ASSET_STAGE_DIR / BUNDLED_PLUGINS_DIRNAME
    ):
        command.extend(["--collect-data", module])
    for module in hidden_imports:
        command.extend(["--hidden-import", module])
    command.append(str(entrypoint))
    subprocess.run(command, cwd=str(ROOT), check=True)


def discover_plugin_python_paths(plugin_root: Path) -> list[Path]:
    paths: list[Path] = []
    for project in sorted(plugin_root.iterdir()):
        if not project.is_dir():
            continue
        src = project / "src"
        if src.is_dir():
            paths.append(src)
        elif (project / "pyproject.toml").is_file() or (project / "setup.py").is_file():
            paths.append(project)
    return paths


def discover_core_plugin_hidden_imports(plugin_package_dir: Path) -> list[str]:
    modules = ["plugins"]
    for module_path in sorted(plugin_package_dir.glob("*.py")):
        if module_path.name == "__init__.py":
            continue
        modules.append(f"plugins.{module_path.stem}")
    return modules


def discover_plugin_hidden_imports(plugin_root: Path) -> list[str]:
    modules: set[str] = set()
    for descriptor_path in sorted(plugin_root.glob("*/agent_plugin.json")):
        try:
            descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not descriptor.get("preinstalled"):
            continue
        module = descriptor.get("module")
        if isinstance(module, str) and module.strip():
            modules.add(module.strip())
        entries = descriptor.get("entries")
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, str) or "." not in entry:
                    continue
                modules.add(entry.rsplit(".", 1)[0])
    return sorted(modules)


def discover_plugin_data_modules(plugin_root: Path) -> list[str]:
    modules: set[str] = set()
    for descriptor_path in sorted(plugin_root.glob("*/agent_plugin.json")):
        try:
            descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not descriptor.get("preinstalled"):
            continue
        module = descriptor.get("module")
        if isinstance(module, str) and module.strip():
            modules.add(module.strip())
    return sorted(modules)


def add_data_arg(source: Path, destination: str) -> str:
    return f"{source}{os.pathsep}{destination}"


def verify_output_tree(output_dir: Path) -> None:
    executable = output_dir / executable_name()
    if not executable.is_file():
        raise RuntimeError(f"Expected executable was not created: {executable}")

    internal_dir = output_dir / "_internal"
    if not internal_dir.is_dir():
        raise RuntimeError(
            f"Expected PyInstaller _internal directory was not created: {internal_dir}"
        )

    required_paths = [
        internal_dir / "agent_terminal_app" / "runtime_layout.json",
        internal_dir / "agent_terminal_app" / "default_config" / "config.json",
        internal_dir / CLOUD_RUNTIME_DIRNAME / "Dockerfile",
        internal_dir / CLOUD_RUNTIME_DIRNAME / "runtime.py",
        internal_dir / CLOUD_RUNTIME_DIRNAME / "python_lib" / "agent_core",
        internal_dir / CLOUD_RUNTIME_DIRNAME / "python_lib" / "agent_app",
        internal_dir / CLOUD_RUNTIME_DIRNAME / "python_lib" / "agent_terminal_app",
        internal_dir / CLOUD_RUNTIME_DIRNAME / "python_lib" / "plugins",
        internal_dir
        / CLOUD_RUNTIME_DIRNAME
        / "cloud-runtime-plugin-bundle"
        / "bundled_plugins"
        / "cloud-agent-app"
        / "agent_plugin.json",
        internal_dir
        / CLOUD_RUNTIME_DIRNAME
        / "cloud-runtime-plugin-bundle"
        / "bundled_plugins"
        / "cloud-agent-app"
        / "docs"
        / "cloud-script-authoring.md",
        internal_dir / CLOUD_RUNTIME_DIRNAME / "plugin_sources" / "cloud-agent-app",
        internal_dir
        / CLOUD_RUNTIME_DIRNAME
        / "cloud-runtime-plugin-bundle"
        / "local-projects.txt",
        internal_dir
        / BUNDLED_PLUGINS_DIRNAME
        / "cloud-agent-app"
        / "docs"
        / "cloud-script-authoring.md",
        internal_dir / BUNDLED_PLUGINS_DIRNAME / "openrouter" / "agent_plugin.json",
        internal_dir / BUNDLED_PLUGINS_DIRNAME / "codex-tools" / "agent_plugin.json",
        internal_dir
        / BUNDLED_PLUGINS_DIRNAME
        / "feature-system-message"
        / "agent_plugin.json",
    ]
    for path in required_paths:
        if not path.exists():
            raise RuntimeError(f"Expected bundled path is missing: {path}")

    forbidden_paths = [
        internal_dir / "agent_terminal_app" / "default_config" / "auth",
        internal_dir / "agent_terminal_app" / "default_config" / ".plugin_cache",
    ]
    for path in forbidden_paths:
        if path.exists():
            raise RuntimeError(f"Forbidden generated/private path was bundled: {path}")


def executable_name() -> str:
    return (
        "crystal-lattice.exe"
        if platform.system().lower().startswith("win")
        else "crystal-lattice"
    )


def create_archive(
    output_dir: Path,
    archive_stem: str,
    platform_name: str,
    *,
    release_dir: Path | None = None,
) -> Path:
    releases_dir = (release_dir or RELEASES_DIR).expanduser().resolve()
    releases_dir.mkdir(parents=True, exist_ok=True)
    if platform_name == "windows":
        archive_path = releases_dir / f"{archive_stem}.zip"
        if archive_path.exists():
            archive_path.unlink()
        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in sorted(output_dir.rglob("*")):
                archive.write(path, Path(archive_stem) / path.relative_to(output_dir))
        return archive_path

    archive_path = releases_dir / f"{archive_stem}.tar.gz"
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(output_dir, arcname=archive_stem)
    return archive_path


if __name__ == "__main__":
    main()
