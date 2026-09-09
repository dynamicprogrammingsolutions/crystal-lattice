from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import venv

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.slow_integration]

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from crystal_lattice_cli_boot import (  # type: ignore[import-not-found]  # noqa: E402
    assert_default_config_boot,
)
from smoke_test_crystal_lattice_python_runtime_archive import (  # type: ignore[import-not-found]  # noqa: E402
    smoke_test_archive,
)


ARCHIVE_ENV = "CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE"


def test_level_1_clean_python_environment_boots_default_config(
    tmp_path: Path,
) -> None:
    environment_dir = tmp_path / "python-environment"
    venv.EnvBuilder(with_pip=True, clear=True).create(environment_dir)
    python = _venv_python(environment_dir)
    install_env = _lean_subprocess_environment()

    _run(
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
        env=install_env,
        timeout=900,
    )

    installed_distributions = _installed_distribution_names(
        python,
        env=install_env,
    )
    assert "agent-core" in installed_distributions
    assert "crystal-lattice-cli" in installed_distributions
    assert "pytest" not in installed_distributions
    assert "openrouter-plugins" not in installed_distributions
    assert "openai-responses" not in installed_distributions
    assert "cloud-agent-app" not in installed_distributions

    command = _venv_command(environment_dir)
    assert command.is_file()
    result = assert_default_config_boot(
        [command],
        default_config_template=(
            ROOT
            / "application"
            / "python"
            / "agent_terminal_app"
            / "default_config"
            / "config.json"
        ),
        workspace=tmp_path / "workspace",
        home_dir=tmp_path / "home",
        plugin_cache_expectation="populated",
        timeout_seconds=1200,
    )

    assert result.plugin_cache.is_dir()
    assert list(result.plugin_cache.rglob("plugin_metadata.json"))


def test_level_2_bundled_python_archive_boots_default_config() -> None:
    smoke_test_archive(_required_archive())


def test_level_3_installed_wrapper_boots_default_config(
    tmp_path: Path,
) -> None:
    archive = _required_archive()
    package_stem = _archive_package_stem(archive)
    install_root = tmp_path / "install"
    bin_dir = tmp_path / "bin"
    installed_bundle = install_root / package_stem
    staging_bundle = install_root / f".{package_stem}.staging"
    installed_bundle.mkdir(parents=True)
    staging_bundle.mkdir()
    (installed_bundle / "stale-target").write_text("stale", encoding="utf-8")
    (staging_bundle / "stale-staging").write_text("stale", encoding="utf-8")
    command_name = "crystal-lattice-distribution-test"

    _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "install_crystal_lattice_archive.py"),
            str(archive),
            "--install-root",
            str(install_root),
            "--bin-dir",
            str(bin_dir),
            "--command-name",
            command_name,
            "--skip-smoke-test",
        ],
        cwd=ROOT,
        env=_lean_subprocess_environment(),
        timeout=300,
    )

    assert installed_bundle.is_dir()
    assert not (installed_bundle / "stale-target").exists()
    assert not staging_bundle.exists()
    command = bin_dir / (f"{command_name}.cmd" if os.name == "nt" else command_name)
    assert command.is_file()

    assert_default_config_boot(
        [command],
        default_config_template=(
            installed_bundle
            / "application"
            / "python"
            / "agent_terminal_app"
            / "default_config"
            / "config.json"
        ),
        workspace=tmp_path / "workspace",
        home_dir=tmp_path / "home",
        plugin_cache_expectation="empty",
        timeout_seconds=300,
    )


def _venv_python(environment_dir: Path) -> Path:
    if os.name == "nt":
        return environment_dir / "Scripts" / "python.exe"
    return environment_dir / "bin" / "python"


def _venv_command(environment_dir: Path) -> Path:
    if os.name == "nt":
        return environment_dir / "Scripts" / "crystal-lattice.exe"
    return environment_dir / "bin" / "crystal-lattice"


def _lean_subprocess_environment() -> dict[str, str]:
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    return env


def _required_archive() -> Path:
    configured = os.environ.get(ARCHIVE_ENV)
    if not configured:
        raise AssertionError(
            f"{ARCHIVE_ENV} is required; use the root distribution test runner"
        )
    archive = Path(configured).expanduser().resolve()
    if not archive.is_file():
        raise AssertionError(f"{ARCHIVE_ENV} is not a file: {archive}")
    return archive


def _archive_package_stem(archive: Path) -> str:
    if archive.name.endswith(".tar.gz"):
        return archive.name.removesuffix(".tar.gz")
    if archive.suffix == ".zip":
        return archive.stem
    raise AssertionError(f"Unsupported archive format: {archive}")


def _installed_distribution_names(
    python: Path,
    *,
    env: dict[str, str],
) -> set[str]:
    result = _run(
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
        cwd=ROOT,
        env=env,
        timeout=60,
    )
    names = json.loads(result.stdout)
    return {str(name).lower().replace("_", "-") for name in names}


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command failed with status {result.returncode}: "
            f"{subprocess.list2cmdline(command)}\n{result.stdout}"
        )
    return result
