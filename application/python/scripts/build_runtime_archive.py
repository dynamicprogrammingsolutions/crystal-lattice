#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile
import venv

from progress import StepLogger


ROOT = Path(__file__).resolve().parents[3]
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

    progress = StepLogger(total_steps=4)
    if configured_runtime is not None:
        progress.step("Resolving the supplied relocatable Python runtime")
        runtime = configured_runtime.expanduser().resolve()
        if not runtime.is_dir():
            raise RuntimeError(f"Python runtime is not a directory: {runtime}")
        progress.detail(f"runtime: {runtime}")
        with tempfile.TemporaryDirectory(
            prefix="crystal-runtime-build-environment-"
        ) as tmp:
            build_with_runtime(
                runtime,
                args,
                temp_dir=Path(tmp),
                progress=progress,
            )
        return

    with tempfile.TemporaryDirectory(prefix="crystal-uv-python-") as tmp:
        temp_dir = Path(tmp)
        install_dir = temp_dir / "uv-python"
        progress.step("Provisioning an uv-managed Python 3.11 runtime")
        progress.run_visible(
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
            cwd=ROOT,
        )
        runtime = find_managed_runtime(install_dir)
        progress.detail(f"runtime: {runtime}")
        build_with_runtime(
            runtime,
            args,
            temp_dir=temp_dir,
            progress=progress,
        )


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


def build_with_runtime(
    runtime: Path,
    args: argparse.Namespace,
    *,
    temp_dir: Path,
    progress: StepLogger,
) -> None:
    progress.step("Creating an isolated archive-build environment")
    python, env = create_build_python(temp_dir)

    progress.step("Installing archive-build dependencies")
    progress.run_visible(
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
        cwd=ROOT,
        env=env,
    )

    progress.step("Building the bundled-Python runtime archive")
    build_archive(runtime, args, python=python, env=env, progress=progress)


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
    return python, env


def build_archive(
    runtime: Path,
    args: argparse.Namespace,
    *,
    python: Path,
    env: dict[str, str],
    progress: StepLogger,
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
    progress.run_visible(command, cwd=ROOT, env=env)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
