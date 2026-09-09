#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
from typing import Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
APP_PYPROJECT = ROOT / "application" / "python" / "pyproject.toml"
PYTHON_RUNTIME_RELEASES_DIR = ROOT / "dist" / "crystal-lattice-python-runtime"
ARCHIVE_ENV = "CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE"


def read_project_version() -> str:
    metadata = tomllib.loads(APP_PYPROJECT.read_text(encoding="utf-8"))
    version = metadata["project"]["version"]
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"Could not read project.version from {APP_PYPROJECT}")
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


def current_target_id() -> str:
    return (
        f"{normalize_platform(platform.system())}-"
        f"{normalize_arch(platform.machine())}"
    )


def current_platform_archive() -> Path:
    target_id = current_target_id()
    suffix = ".zip" if target_id.startswith("windows-") else ".tar.gz"
    return (
        PYTHON_RUNTIME_RELEASES_DIR
        / f"crystal-lattice-python-runtime-v{read_project_version()}-"
        f"{target_id}{suffix}"
    )


def assert_archive_matches_current_platform(archive: Path) -> None:
    target = current_target_id()
    if f"-{target}." not in archive.name:
        raise RuntimeError(
            f"Archive {archive.name!r} does not match current platform {target!r}"
        )


def archive_package_stem(archive: Path) -> str:
    if archive.name.endswith(".tar.gz"):
        return archive.name.removesuffix(".tar.gz")
    if archive.suffix == ".zip":
        return archive.stem
    raise RuntimeError(f"Unsupported archive format: {archive}")


def resolve_configured_archive() -> Path | None:
    configured = os.environ.get(ARCHIVE_ENV)
    if not configured:
        return None
    archive = Path(configured).expanduser().resolve()
    if not archive.is_file():
        raise RuntimeError(f"{ARCHIVE_ENV} is not a file: {archive}")
    assert_archive_matches_current_platform(archive)
    return archive


def resolve_bash(
    *,
    env: Mapping[str, str] | None = None,
    windows: bool | None = None,
) -> str:
    environment = os.environ if env is None else env
    if windows is None:
        windows = os.name == "nt"
    path_value = environment.get("PATH", "")
    if not windows:
        bash = shutil.which("bash", path=path_value)
        if bash is None:
            raise RuntimeError("Could not find bash on PATH")
        return bash

    candidates: list[Path] = []
    path_entries = [
        Path(entry)
        for entry in path_value.split(";")
        if entry and Path(entry).is_absolute()
    ]
    for entry in path_entries:
        for parent in (entry, *entry.parents):
            if parent.name.lower() == "git":
                candidates.extend(
                    [
                        parent / "bin" / "bash.exe",
                        parent / "usr" / "bin" / "bash.exe",
                    ]
                )
                break

    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        root = environment.get(variable)
        if root:
            candidates.append(Path(root) / "Git" / "bin" / "bash.exe")

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(
        "Could not find Git Bash. Install Git for Windows or run with "
        "an explicit Bash-compatible environment."
    )


__all__ = [
    "APP_PYPROJECT",
    "ARCHIVE_ENV",
    "PYTHON_RUNTIME_RELEASES_DIR",
    "ROOT",
    "archive_package_stem",
    "assert_archive_matches_current_platform",
    "current_platform_archive",
    "current_target_id",
    "normalize_arch",
    "normalize_platform",
    "read_project_version",
    "resolve_bash",
    "resolve_configured_archive",
]
