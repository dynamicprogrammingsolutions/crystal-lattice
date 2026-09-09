from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import install_crystal_lattice_archive as archive_installer  # type: ignore[import-not-found]  # noqa: E402
import run_cli_distribution_test as distribution_runner  # type: ignore[import-not-found]  # noqa: E402


def test_current_platform_archive_uses_version_platform_and_arch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(archive_installer, "read_project_version", lambda: "9.8.7")
    monkeypatch.setattr(archive_installer.platform, "system", lambda: "Linux")
    monkeypatch.setattr(archive_installer.platform, "machine", lambda: "x86_64")

    assert archive_installer.current_platform_archive() == (
        archive_installer.PYTHON_RUNTIME_RELEASES_DIR
        / "crystal-lattice-python-runtime-v9.8.7-linux-amd64.tar.gz"
    )


def test_runner_accepts_matching_current_platform_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(distribution_runner.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(distribution_runner.platform, "machine", lambda: "arm64")
    archive = tmp_path / "crystal-lattice-python-runtime-v9.8.7-darwin-arm64.tar.gz"
    archive.touch()
    monkeypatch.setenv(distribution_runner.ARCHIVE_ENV, str(archive))

    assert distribution_runner.resolve_archive() == archive


def test_runner_rejects_archive_for_another_platform(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(distribution_runner.platform, "system", lambda: "Windows")
    monkeypatch.setattr(distribution_runner.platform, "machine", lambda: "AMD64")
    archive = tmp_path / "crystal-lattice-python-runtime-v9.8.7-linux-amd64.tar.gz"
    archive.touch()

    with pytest.raises(RuntimeError, match="does not match current platform"):
        distribution_runner.assert_archive_matches_current_platform(archive)
