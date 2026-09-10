#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import venv

from progress import StepLogger


ROOT = Path(__file__).resolve().parents[3]
OPTIMIZED_BUILDER = ROOT / "scripts" / "build_crystal_lattice_binary.py"


def main() -> None:
    progress = StepLogger(total_steps=3)
    with tempfile.TemporaryDirectory(prefix="crystal-optimized-build-") as tmp:
        temp_dir = Path(tmp)
        environment_dir = temp_dir / "python-environment"
        home_dir = temp_dir / "home"
        home_dir.mkdir()

        progress.step("Creating an isolated optimized-build environment")
        venv.EnvBuilder(with_pip=True, clear=True).create(environment_dir)
        python = venv_python(environment_dir)
        env = isolated_environment(home_dir)

        progress.step("Installing optimized-build dependencies")
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
                f"{ROOT / 'application' / 'python'}[binary]",
            ],
            cwd=ROOT,
            env=env,
        )

        progress.step("Building the optimized CLI archive")
        progress.run_visible(
            [str(python), str(OPTIMIZED_BUILDER), *sys.argv[1:]],
            cwd=ROOT,
            env=env,
        )


def venv_python(environment_dir: Path) -> Path:
    if os.name == "nt":
        return environment_dir / "Scripts" / "python.exe"
    return environment_dir / "bin" / "python"


def isolated_environment(home_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    home = str(home_dir.resolve())
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["PIP_CACHE_DIR"] = str((home_dir / ".cache" / "pip").resolve())
    return env


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
