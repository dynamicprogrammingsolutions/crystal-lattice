#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


ROOT = Path(__file__).resolve().parents[1]
OPTIMIZED_BUILDER = ROOT / "scripts" / "build_crystal_lattice_binary.py"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="crystal-optimized-build-") as tmp:
        temp_dir = Path(tmp)
        environment_dir = temp_dir / "python-environment"
        home_dir = temp_dir / "home"
        home_dir.mkdir()
        venv.EnvBuilder(with_pip=True, clear=True).create(environment_dir)
        python = venv_python(environment_dir)
        env = isolated_environment(home_dir)

        run(
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
            env=env,
        )
        run(
            [str(python), str(OPTIMIZED_BUILDER), *sys.argv[1:]],
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


def run(command: list[str], *, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=str(ROOT), env=env, check=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
