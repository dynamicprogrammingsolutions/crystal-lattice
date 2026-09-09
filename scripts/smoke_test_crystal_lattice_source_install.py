#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

from crystal_lattice_cli_boot import assert_config_boot


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    smoke_test_source_install()
    print("Source-installation smoke test passed")


def smoke_test_source_install() -> None:
    with tempfile.TemporaryDirectory(prefix="crystal-source-install-smoke-") as tmp:
        temp_dir = Path(tmp)
        environment_dir = temp_dir / "python-environment"
        home_dir = temp_dir / "home"
        home_dir.mkdir()
        venv.EnvBuilder(with_pip=True, clear=True).create(environment_dir)
        python = venv_python(environment_dir)
        install_env = lean_subprocess_environment(home_dir)

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
                str(ROOT / "application" / "python"),
            ],
            env=install_env,
            timeout=900,
        )

        installed_distributions = installed_distribution_names(
            python,
            env=install_env,
        )
        required = {"agent-core", "crystal-lattice-cli"}
        missing = sorted(required - installed_distributions)
        if missing:
            raise RuntimeError(
                f"Source environment is missing distributions: {missing}"
            )
        unexpected = {
            "pytest",
            "openrouter-plugins",
            "openai-responses",
            "cloud-agent-app",
        } & installed_distributions
        if unexpected:
            raise RuntimeError(
                "Source environment unexpectedly contains development/default "
                f"plugin distributions: {sorted(unexpected)}"
            )

        command = venv_command(environment_dir)
        if not command.is_file():
            raise RuntimeError(f"Installed source command does not exist: {command}")

        config_path = (
            ROOT
            / "application"
            / "python"
            / "agent_terminal_app"
            / "default_config"
            / "config.json"
        )
        result = assert_config_boot(
            [command],
            config_path=config_path,
            workspace=temp_dir / "workspace",
            home_dir=home_dir,
            plugin_cache_expectation="populated",
            config_mode="local-default",
            base_env=install_env,
            timeout_seconds=1200,
        )
        if not result.plugin_metadata_ids:
            raise RuntimeError("Default plugins were not dynamically installed")


def venv_python(environment_dir: Path) -> Path:
    if os.name == "nt":
        return environment_dir / "Scripts" / "python.exe"
    return environment_dir / "bin" / "python"


def venv_command(environment_dir: Path) -> Path:
    if os.name == "nt":
        return environment_dir / "Scripts" / "crystal-lattice.exe"
    return environment_dir / "bin" / "crystal-lattice"


def lean_subprocess_environment(home_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    home = str(home_dir.resolve())
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["PIP_CACHE_DIR"] = str((home_dir / ".cache" / "pip").resolve())
    return env


def installed_distribution_names(
    python: Path,
    *,
    env: dict[str, str],
) -> set[str]:
    result = run(
        [
            str(python),
            "-c",
            (
                "import importlib.metadata as metadata, json; "
                "print(json.dumps(sorted("
                "distribution.metadata['Name'] "
                "for distribution in metadata.distributions() "
                "if distribution.metadata['Name'])))"
            ),
        ],
        env=env,
        timeout=60,
    )
    names = json.loads(result.stdout)
    return {str(name).lower().replace("_", "-") for name in names}


def run(
    command: list[str],
    *,
    env: dict[str, str],
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with status {result.returncode}: "
            f"{subprocess.list2cmdline(command)}\n{result.stdout}"
        )
    return result


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
