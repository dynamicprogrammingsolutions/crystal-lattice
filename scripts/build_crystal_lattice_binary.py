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


EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "tests",
}
EXCLUDED_FILE_SUFFIXES = {
    ".log",
    ".pyc",
    ".pyo",
}
EXCLUDED_FILE_NAMES = {
    ".coverage",
}
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
    args = parser.parse_args()

    version = args.version or read_project_version()
    platform_name = normalize_platform(args.platform_name or platform.system())
    arch = normalize_arch(args.arch or platform.machine())
    target_id = f"{platform_name}-{arch}"
    archive_stem = f"crystal-lattice-cli-v{version}-{target_id}"

    prepare_staged_assets()

    if not args.skip_pyinstaller:
        run_pyinstaller()

    output_dir = APP_DIR / "dist" / "crystal-lattice"
    verify_output_tree(output_dir)

    if not args.no_archive:
        archive_path = create_archive(output_dir, archive_stem, platform_name)
        print(f"Created release archive: {archive_path}")
    else:
        print(f"Built PyInstaller output: {output_dir}")


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


def prepare_staged_assets() -> None:
    if ASSET_STAGE_DIR.exists():
        shutil.rmtree(ASSET_STAGE_DIR)
    ASSET_STAGE_DIR.mkdir(parents=True, exist_ok=True)

    staged_app = ASSET_STAGE_DIR / "agent_terminal_app"
    staged_app.mkdir(parents=True, exist_ok=True)

    copytree_sanitized(
        APP_PACKAGE_DIR / "default_config",
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
    copytree_sanitized(PLUGINS_DIR, bundled_plugins_dir)
    prepare_cloud_runtime_build_context(ASSET_STAGE_DIR / CLOUD_RUNTIME_DIRNAME)

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


def prepare_cloud_runtime_build_context(destination: Path) -> None:
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
    copytree_sanitized(PLUGINS_DIR, destination / "plugins")


def copytree_sanitized(
    source: Path,
    destination: Path,
    *,
    excluded_dir_names: Iterable[str] = (),
) -> None:
    excluded_dirs = set(excluded_dir_names).union(EXCLUDED_DIR_NAMES)

    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            path = Path(name)
            if name in excluded_dirs or name.endswith(".egg-info"):
                ignored.add(name)
            elif name in EXCLUDED_FILE_NAMES:
                ignored.add(name)
            elif path.suffix in EXCLUDED_FILE_SUFFIXES:
                ignored.add(name)
        return ignored

    shutil.copytree(source, destination, ignore=ignore)


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
        internal_dir / CLOUD_RUNTIME_DIRNAME / "plugins" / "cloud-agent-app",
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


def create_archive(output_dir: Path, archive_stem: str, platform_name: str) -> Path:
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    if platform_name == "windows":
        archive_path = RELEASES_DIR / f"{archive_stem}.zip"
        if archive_path.exists():
            archive_path.unlink()
        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in sorted(output_dir.rglob("*")):
                archive.write(path, Path(archive_stem) / path.relative_to(output_dir))
        return archive_path

    archive_path = RELEASES_DIR / f"{archive_stem}.tar.gz"
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(output_dir, arcname=archive_stem)
    return archive_path


if __name__ == "__main__":
    main()
