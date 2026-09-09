from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import crystal_lattice_distribution as distribution  # type: ignore[import-not-found]  # noqa: E402
import build_crystal_lattice_python_runtime_archive as runtime_builder  # type: ignore[import-not-found]  # noqa: E402
import install_current_crystal_lattice_archive as local_installer  # type: ignore[import-not-found]  # noqa: E402
import run_cli_distribution_test as distribution_runner  # type: ignore[import-not-found]  # noqa: E402


def test_current_platform_archive_uses_version_platform_and_arch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(distribution, "read_project_version", lambda: "9.8.7")
    monkeypatch.setattr(distribution.platform, "system", lambda: "Linux")
    monkeypatch.setattr(distribution.platform, "machine", lambda: "x86_64")

    assert distribution.current_platform_archive() == (
        distribution.PYTHON_RUNTIME_RELEASES_DIR
        / "crystal-lattice-python-runtime-v9.8.7-linux-amd64.tar.gz"
    )


def test_runner_accepts_matching_current_platform_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(distribution.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(distribution.platform, "machine", lambda: "arm64")
    archive = tmp_path / "crystal-lattice-python-runtime-v9.8.7-darwin-arm64.tar.gz"
    archive.touch()
    monkeypatch.setenv(distribution.ARCHIVE_ENV, str(archive))

    assert distribution_runner.resolve_archive() == archive


def test_runner_rejects_archive_for_another_platform(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(distribution.platform, "system", lambda: "Windows")
    monkeypatch.setattr(distribution.platform, "machine", lambda: "AMD64")
    archive = tmp_path / "crystal-lattice-python-runtime-v9.8.7-linux-amd64.tar.gz"
    archive.touch()

    with pytest.raises(RuntimeError, match="does not match current platform"):
        distribution.assert_archive_matches_current_platform(archive)


def test_managed_runtime_selection_ignores_hidden_and_symlink_directories(
    tmp_path: Path,
) -> None:
    install_dir = tmp_path / "uv-python"
    runtime = install_dir / "cpython-3.11"
    hidden = install_dir / ".temp"
    runtime.mkdir(parents=True)
    hidden.mkdir()
    (install_dir / "python").symlink_to(runtime, target_is_directory=True)

    assert runtime_builder.find_managed_runtime(install_dir) == runtime


def test_local_installer_builds_then_delegates_to_public_installer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / "crystal-lattice-python-runtime-v9.8.7-darwin-arm64.tar.gz"
    archive.touch()
    calls: list[tuple[list[str], dict[str, str] | None]] = []

    monkeypatch.setattr(local_installer, "current_platform_archive", lambda: archive)

    def fake_run(
        command: list[str],
        *,
        cwd: str,
        check: bool,
        env: dict[str, str] | None = None,
    ) -> None:
        assert cwd == str(ROOT)
        assert check is True
        calls.append((command, env))

    monkeypatch.setattr(local_installer.subprocess, "run", fake_run)

    local_installer.main()

    assert calls[0][0][0] == sys.executable
    assert calls[0][0][1].endswith(
        "scripts/build_crystal_lattice_python_runtime_archive.py"
    )
    assert calls[1][0] == ["bash", str(ROOT / "scripts" / "install.sh")]
    assert calls[1][1] is not None
    assert calls[1][1][distribution.ARCHIVE_ENV] == str(archive)
