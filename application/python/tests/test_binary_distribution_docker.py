from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.docker]


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "binary_distribution"
IMAGE_NAME = "crystal-lattice-linux-bundle-test:local"


def test_linux_bundle_builds_and_runs_in_clean_runtime_container(
    tmp_path: Path,
) -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker is not available")

    _run(["docker", "info"], cwd=ROOT, skip_on_failure="Docker daemon is not available")

    snapshot_dir = tmp_path / "repo"
    snapshot_dir.mkdir()
    _run(["git", "checkout-index", "-a", f"--prefix={snapshot_dir}/"], cwd=ROOT)

    dockerfile = (
        snapshot_dir
        / "application"
        / "python"
        / "tests"
        / "fixtures"
        / "binary_distribution"
        / "linux-bundle.Dockerfile"
    )
    smoke_script = (
        snapshot_dir
        / "application"
        / "python"
        / "tests"
        / "fixtures"
        / "binary_distribution"
        / "smoke_test_bundle.sh"
    )
    assert dockerfile.is_file()
    assert smoke_script.is_file()

    _run(
        [
            "docker",
            "build",
            "-f",
            str(dockerfile),
            "-t",
            IMAGE_NAME,
            str(snapshot_dir),
        ],
        cwd=ROOT,
    )

    _run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{snapshot_dir}:/repo",
            "-w",
            "/repo",
            IMAGE_NAME,
            "bash",
            "-lc",
            (
                "python -m pip install -e core/python -e 'application/python[binary]' "
                "&& python scripts/build_crystal_lattice_binary.py"
            ),
        ],
        cwd=ROOT,
    )

    archives = sorted((snapshot_dir / "dist" / "crystal-lattice").glob("*.tar.gz"))
    linux_archives = [path for path in archives if "-linux-" in path.name]
    assert (
        linux_archives
    ), f"No Linux release archive found under {snapshot_dir / 'dist'}"
    archive = linux_archives[-1]
    _run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{archive.parent}:/artifacts:ro",
            "-v",
            f"{smoke_script}:/smoke_test_bundle.sh:ro",
            "ubuntu:22.04",
            "bash",
            "/smoke_test_bundle.sh",
            f"/artifacts/{archive.name}",
        ],
        cwd=ROOT,
    )


def _run(
    command: list[str],
    *,
    cwd: Path,
    skip_on_failure: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        if skip_on_failure is not None:
            pytest.skip(f"{skip_on_failure}\n{result.stdout}")
        raise AssertionError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"{result.stdout}"
        )
    return result
