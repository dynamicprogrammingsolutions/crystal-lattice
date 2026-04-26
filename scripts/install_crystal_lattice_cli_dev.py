#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VENV_DIR = Path.home() / ".crystal" / "dev-cli-venv"
DEFAULT_BIN_DIR = Path.home() / ".local" / "bin"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install an editable Crystal Lattice dev command."
    )
    parser.add_argument(
        "--venv-dir",
        type=Path,
        default=DEFAULT_VENV_DIR,
        help=f"editable install venv directory (default: {DEFAULT_VENV_DIR})",
    )
    parser.add_argument(
        "--bin-dir",
        type=Path,
        default=DEFAULT_BIN_DIR,
        help=f"command wrapper/symlink directory (default: {DEFAULT_BIN_DIR})",
    )
    parser.add_argument(
        "--command-name",
        default="crystal-lattice-cli-dev",
        help="installed dev command name",
    )
    args = parser.parse_args()

    venv_dir = args.venv_dir.expanduser().resolve()
    bin_dir = args.bin_dir.expanduser().resolve()

    ensure_venv(venv_dir)
    python = venv_python(venv_dir)
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-e",
            "core/python",
            "-e",
            "application/python",
            "-e",
            "plugins/openai_responses",
        ]
    )

    command_path = install_dev_command(venv_dir, bin_dir, args.command_name)
    verify_dev_command(command_path)

    print(f"Installed dev venv: {venv_dir}")
    print(f"Installed dev command: {command_path}")
    if not path_contains(bin_dir):
        print(f"Add this directory to PATH if needed: {bin_dir}")


def ensure_venv(venv_dir: Path) -> None:
    if not venv_dir.exists():
        venv.EnvBuilder(with_pip=True).create(venv_dir)


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_crystal_lattice(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "crystal-lattice.exe"
    return venv_dir / "bin" / "crystal-lattice"


def install_dev_command(venv_dir: Path, bin_dir: Path, command_name: str) -> Path:
    executable = venv_crystal_lattice(venv_dir)
    if not executable.is_file():
        raise RuntimeError(f"Editable crystal-lattice command is missing: {executable}")

    bin_dir.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        command_path = bin_dir / f"{command_name}.cmd"
        command_path.write_text(f'@"{executable}" %*\n', encoding="utf-8")
        return command_path

    command_path = bin_dir / command_name
    command_path.write_text(
        "#!/usr/bin/env sh\n" f'exec "{executable}" "$@"\n',
        encoding="utf-8",
    )
    command_path.chmod(0o755)
    return command_path


def verify_dev_command(command_path: Path) -> None:
    layout = json.loads(run([str(command_path), "--runtime-layout-json"]).stdout)
    if layout.get("layout") != "source":
        raise RuntimeError(
            f"Dev command must use source layout, got {layout.get('layout')!r}"
        )
    run([str(command_path), "--help"])


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
