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
import zipfile

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
APP_PYPROJECT = ROOT / "application" / "python" / "pyproject.toml"
RELEASES_DIR = ROOT / "dist" / "crystal-lattice"
DEFAULT_INSTALL_ROOT = Path.home() / ".local" / "opt" / "crystal-lattice-cli"
DEFAULT_BIN_DIR = Path.home() / ".local" / "bin"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install Crystal Lattice from a local release archive."
    )
    parser.add_argument(
        "archive",
        nargs="?",
        type=Path,
        help="release archive to install; defaults to the current platform archive",
    )
    parser.add_argument(
        "--install-root",
        type=Path,
        default=DEFAULT_INSTALL_ROOT,
        help=f"bundle install root (default: {DEFAULT_INSTALL_ROOT})",
    )
    parser.add_argument(
        "--bin-dir",
        type=Path,
        default=DEFAULT_BIN_DIR,
        help=f"command wrapper/symlink directory (default: {DEFAULT_BIN_DIR})",
    )
    parser.add_argument(
        "--command-name",
        default="crystal-lattice",
        help="installed command name",
    )
    parser.add_argument(
        "--skip-smoke-test",
        action="store_true",
        help="skip bundle validation before installation",
    )
    args = parser.parse_args()

    archive = (args.archive or current_platform_archive()).expanduser().resolve()
    if not archive.is_file():
        raise RuntimeError(f"Archive does not exist: {archive}")

    if not args.skip_smoke_test:
        run(
            [
                sys.executable,
                "scripts/smoke_test_crystal_lattice_archive.py",
                str(archive),
            ]
        )

    install_root = args.install_root.expanduser().resolve()
    bin_dir = args.bin_dir.expanduser().resolve()
    installed_bundle = install_archive(archive, install_root)
    command_path = install_command(installed_bundle, bin_dir, args.command_name)
    verify_installed_command(command_path)

    print(f"Installed bundle: {installed_bundle}")
    print(f"Installed command: {command_path}")
    if not path_contains(bin_dir):
        print(f"Add this directory to PATH if needed: {bin_dir}")


def current_platform_archive() -> Path:
    version = read_project_version()
    target_id = (
        f"{normalize_platform(platform.system())}-{normalize_arch(platform.machine())}"
    )
    suffix = ".zip" if target_id.startswith("windows-") else ".tar.gz"
    return RELEASES_DIR / f"crystal-lattice-cli-v{version}-{target_id}{suffix}"


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


def install_archive(archive: Path, install_root: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix="crystal-lattice-install-") as temp_dir:
        extract_dir = Path(temp_dir)
        extract_archive(archive, extract_dir)
        extracted_bundle = find_bundle_dir(extract_dir)
        target_bundle = install_root / extracted_bundle.name
        staging_bundle = install_root / f".{extracted_bundle.name}.staging"

        install_root.mkdir(parents=True, exist_ok=True)
        if staging_bundle.exists():
            remove_path(staging_bundle)
        shutil.move(str(extracted_bundle), str(staging_bundle))
        if target_bundle.exists():
            remove_path(target_bundle)
        staging_bundle.rename(target_bundle)
        return target_bundle


def extract_archive(archive: Path, extract_dir: Path) -> None:
    if archive.name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as tar:
            safe_extract_tar(tar, extract_dir)
        return
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zip_file:
            safe_extract_zip(zip_file, extract_dir)
        return
    raise RuntimeError(f"Unsupported archive format: {archive}")


def safe_extract_tar(tar: tarfile.TarFile, extract_dir: Path) -> None:
    base = extract_dir.resolve()
    for member in tar.getmembers():
        target = (extract_dir / member.name).resolve()
        if not is_relative_to(target, base):
            raise RuntimeError(
                f"Archive member escapes extraction directory: {member.name}"
            )
    tar.extractall(extract_dir)


def safe_extract_zip(zip_file: zipfile.ZipFile, extract_dir: Path) -> None:
    base = extract_dir.resolve()
    for member in zip_file.namelist():
        target = (extract_dir / member).resolve()
        if not is_relative_to(target, base):
            raise RuntimeError(f"Archive member escapes extraction directory: {member}")
    zip_file.extractall(extract_dir)


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def find_bundle_dir(extract_dir: Path) -> Path:
    directories = [path for path in extract_dir.iterdir() if path.is_dir()]
    if len(directories) != 1:
        names = ", ".join(sorted(path.name for path in directories))
        raise RuntimeError(
            f"Expected exactly one extracted bundle directory, found: {names}"
        )
    return directories[0]


def install_command(bundle_dir: Path, bin_dir: Path, command_name: str) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    executable = bundle_dir / executable_name()
    if not executable.is_file():
        raise RuntimeError(f"Bundle executable is missing: {executable}")

    if os.name == "nt":
        command_path = bin_dir / f"{command_name}.cmd"
        command_path.write_text(f'@"{executable}" %*\n', encoding="utf-8")
        return command_path

    command_path = bin_dir / command_name
    if command_path.exists() or command_path.is_symlink():
        command_path.unlink()
    command_path.symlink_to(executable)
    return command_path


def verify_installed_command(command_path: Path) -> None:
    layout = json.loads(run([str(command_path), "--runtime-layout-json"]).stdout)
    if layout.get("layout") != "bundled":
        raise RuntimeError(
            f"Installed command must use bundled layout, got {layout.get('layout')!r}"
        )
    run([str(command_path), "--help"])


def executable_name() -> str:
    return "crystal-lattice.exe" if os.name == "nt" else "crystal-lattice"


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def path_contains(directory: Path) -> bool:
    paths = [
        Path(value).expanduser()
        for value in os.environ.get("PATH", "").split(os.pathsep)
        if value
    ]
    resolved = directory.resolve()
    return any(path.resolve() == resolved for path in paths)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(ROOT),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
