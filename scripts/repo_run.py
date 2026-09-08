#!/usr/bin/env python3
"""Run a command inside the repository Python environment.

Resolution order:

1. If ``VIRTUAL_ENV`` is set, an environment is already active; the command
   runs as-is so the active environment wins.
2. Else if ``<repo>/.venv`` contains a Python executable, its scripts
   directory (``bin`` on macOS/Linux, ``Scripts`` on Windows) is prepended
   to ``PATH`` and the command runs with ``VIRTUAL_ENV`` pointing at it.
3. Else the command fails with setup instructions.

Usage:

    python scripts/repo_run.py [--repo-root ROOT] <command> [args ...]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str]) -> tuple[Path, list[str]]:
    parser = argparse.ArgumentParser(
        prog="repo_run.py",
        description="Run a command inside the repository Python environment.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=DEFAULT_REPO_ROOT,
        help="Repository root used to locate the .venv directory (default: this script's repo).",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command and arguments to run.",
    )
    args = parser.parse_args(argv)
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("a command is required")
    return args.repo_root, command


def venv_scripts_dir(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts" if os.name == "nt" else "bin")


def venv_python_name() -> str:
    return "python.exe" if os.name == "nt" else "python"


def build_child_env(repo_root: Path) -> dict[str, str] | None:
    """Build the child environment, or return None after printing why."""
    env = os.environ.copy()
    if env.get("VIRTUAL_ENV"):
        return env

    venv_dir = repo_root / ".venv"
    if not (venv_scripts_dir(venv_dir) / venv_python_name()).exists():
        if venv_dir.exists():
            print(
                f"error: the virtualenv at {venv_dir} is missing a Python executable; "
                "recreate it with:\n  npm run install:venv",
                file=sys.stderr,
            )
        else:
            print(
                "error: no Python environment found; create the repository virtualenv "
                "with:\n  npm run install:venv\n"
                "or activate an existing virtualenv and re-run the command.",
                file=sys.stderr,
            )
        return None

    env["PATH"] = str(venv_scripts_dir(venv_dir)) + os.pathsep + env.get("PATH", "")
    env["VIRTUAL_ENV"] = str(venv_dir)
    return env


def main(argv: list[str]) -> int:
    repo_root, command = parse_args(argv)
    env = build_child_env(repo_root)
    if env is None:
        return 1

    resolved = shutil.which(command[0], path=env.get("PATH", ""))
    if resolved is None:
        print(f"error: command not found: {command[0]}", file=sys.stderr)
        return 127

    completed = subprocess.run([resolved, *command[1:]], env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
