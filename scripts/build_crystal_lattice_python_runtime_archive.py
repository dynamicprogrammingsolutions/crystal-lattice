#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Iterator
import venv


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_BUILDER = ROOT / "scripts" / "build_crystal_lattice_python_runtime_package.py"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the current-platform bundled-Python archive with a "
            "relocatable Python runtime."
        )
    )
    parser.add_argument("--python-runtime", type=Path, default=None)
    parser.add_argument("--version", default=None)
    parser.add_argument("--platform", dest="platform_name", default=None)
    parser.add_argument("--arch", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    configured_runtime = args.python_runtime
    if configured_runtime is None:
        configured = os.environ.get("CRYSTAL_PYTHON_RUNTIME")
        configured_runtime = Path(configured) if configured else None

    if configured_runtime is not None:
        runtime = configured_runtime.expanduser().resolve()
        if not runtime.is_dir():
            raise RuntimeError(f"Python runtime is not a directory: {runtime}")
        with temporary_build_python() as (python, env):
            build_archive(runtime, args, python=python, env=env)
        return

    with tempfile.TemporaryDirectory(prefix="crystal-uv-python-") as tmp:
        temp_dir = Path(tmp)
        install_dir = temp_dir / "uv-python"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uv",
                "python",
                "install",
                "--install-dir",
                str(install_dir),
                "--python-preference",
                "only-managed",
                "--no-bin",
                "3.11",
            ],
            cwd=str(ROOT),
            check=True,
        )
        runtime = find_managed_runtime(install_dir)
        with temporary_build_python(temp_dir=temp_dir) as (python, env):
            build_archive(runtime, args, python=python, env=env)


def find_managed_runtime(install_dir: Path) -> Path:
    candidates = sorted(
        path
        for path in install_dir.iterdir()
        if path.is_dir() and not path.is_symlink() and not path.name.startswith(".")
    )
    if len(candidates) != 1:
        found = ", ".join(path.name for path in candidates) or "<none>"
        raise RuntimeError(
            f"Expected one uv-managed Python runtime under {install_dir}, "
            f"found: {found}"
        )
    return candidates[0]


@contextmanager
def temporary_build_python(
    *,
    temp_dir: Path | None = None,
) -> Iterator[tuple[Path, dict[str, str]]]:
    if temp_dir is None:
        with tempfile.TemporaryDirectory(
            prefix="crystal-runtime-build-environment-"
        ) as tmp:
            yield create_build_python(Path(tmp))
        return
    yield create_build_python(temp_dir)


def create_build_python(root: Path) -> tuple[Path, dict[str, str]]:
    environment_dir = root / "build-environment"
    home_dir = root / "build-home"
    home_dir.mkdir()
    venv.EnvBuilder(with_pip=True, clear=True).create(environment_dir)
    python = (
        environment_dir / "Scripts" / "python.exe"
        if os.name == "nt"
        else environment_dir / "bin" / "python"
    )
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    home = str(home_dir.resolve())
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["PIP_CACHE_DIR"] = str((home_dir / ".cache" / "pip").resolve())
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-e",
            str(ROOT / "core" / "python"),
            "-e",
            str(ROOT / "application" / "python"),
        ],
        cwd=str(ROOT),
        env=env,
        check=True,
    )
    return python, env


def build_archive(
    runtime: Path,
    args: argparse.Namespace,
    *,
    python: Path,
    env: dict[str, str],
) -> None:
    command = [
        str(python),
        str(PACKAGE_BUILDER),
        "--python-runtime",
        str(runtime),
    ]
    if args.version:
        command.extend(["--version", args.version])
    if args.platform_name:
        command.extend(["--platform", args.platform_name])
    if args.arch:
        command.extend(["--arch", args.arch])
    if args.output:
        command.extend(["--output", str(args.output.expanduser().resolve())])
    subprocess.run(command, cwd=str(ROOT), env=env, check=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
