from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest

from agent_core import Message, Session


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "application" / "python" / "scripts"
POWERSHELL_SMOKE = SCRIPTS_DIR / "smoke_powershell_install.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import distribution_support as distribution  # type: ignore[import-not-found]  # noqa: E402
import build_runtime_archive as runtime_builder  # type: ignore[import-not-found]  # noqa: E402
import install_current_archive as local_installer  # type: ignore[import-not-found]  # noqa: E402
import run_distribution_smoke as distribution_runner  # type: ignore[import-not-found]  # noqa: E402
import headless_access_smoke  # type: ignore[import-not-found]  # noqa: E402
import smoke_agent_access  # type: ignore[import-not-found]  # noqa: E402
import smoke_powershell_install  # type: ignore[import-not-found]  # noqa: E402


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


def test_windows_bash_resolution_avoids_wsl_launcher(tmp_path: Path) -> None:
    system_dir = tmp_path / "Windows" / "System32"
    git_root = tmp_path / "Git"
    system_dir.mkdir(parents=True)
    (system_dir / "bash.exe").touch()
    (git_root / "cmd").mkdir(parents=True)
    (git_root / "cmd" / "git.exe").touch()
    (git_root / "bin").mkdir()
    git_bash = git_root / "bin" / "bash.exe"
    git_bash.touch()

    resolved = distribution.resolve_bash(
        env={"PATH": f"{system_dir};{git_root / 'cmd'}"},
        windows=True,
    )

    assert resolved == str(git_bash)


def test_local_installer_builds_then_delegates_to_public_installer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / "crystal-lattice-python-runtime-v9.8.7-darwin-arm64.tar.gz"
    archive.touch()
    calls: list[tuple[list[str], dict[str, str] | None]] = []

    monkeypatch.delenv(distribution.ARCHIVE_ENV, raising=False)
    monkeypatch.setattr(local_installer, "current_platform_archive", lambda: archive)
    monkeypatch.setattr(local_installer, "resolve_bash", lambda **_kwargs: "/bin/bash")

    def fake_run_visible(
        _self: object,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        **_kwargs: object,
    ) -> None:
        assert cwd == ROOT
        calls.append((command, env))

    monkeypatch.setattr(
        local_installer.StepLogger,
        "run_visible",
        fake_run_visible,
    )

    local_installer.main()

    assert calls[0][0] == [
        sys.executable,
        str(SCRIPTS_DIR / "build_runtime_archive.py"),
    ]
    assert calls[1][0] == [
        "/bin/bash",
        str(SCRIPTS_DIR / "install.sh"),
    ]
    assert calls[1][1] is not None
    assert calls[1][1][distribution.ARCHIVE_ENV] == str(archive)


def test_local_installer_accepts_prebuilt_archive_without_rebuilding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / "crystal-lattice-python-runtime-v9.8.7-darwin-arm64.tar.gz"
    archive.touch()
    calls: list[tuple[list[str], dict[str, str] | None]] = []

    monkeypatch.setattr(distribution.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(distribution.platform, "machine", lambda: "arm64")
    monkeypatch.setenv(distribution.ARCHIVE_ENV, str(archive))
    monkeypatch.setattr(local_installer, "resolve_bash", lambda **_kwargs: "/bin/bash")

    def fake_run_visible(
        _self: object,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        **_kwargs: object,
    ) -> None:
        assert cwd == ROOT
        calls.append((command, env))

    monkeypatch.setattr(
        local_installer.StepLogger,
        "run_visible",
        fake_run_visible,
    )

    local_installer.main()

    assert len(calls) == 1
    assert calls[0][0] == ["/bin/bash", str(SCRIPTS_DIR / "install.sh")]
    assert calls[0][1] is not None
    assert calls[0][1][distribution.ARCHIVE_ENV] == str(archive)


def test_local_installer_uses_native_powershell_on_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        local_installer,
        "resolve_powershell",
        lambda **_kwargs: r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    )

    assert local_installer.public_installer_command(
        env={"PATH": r"C:\Windows\System32"},
        windows=True,
    ) == [
        r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPTS_DIR / "install.ps1"),
    ]


def test_application_owned_cli_scripts_are_package_local() -> None:
    moved_names = {
        "build_optimized_archive.py",
        "build_runtime_archive.py",
        "bump_version.py",
        "boot_smoke.py",
        "download_server.py",
        "distribution_support.py",
        "install.ps1",
        "install.sh",
        "install_dev.py",
        "install_current_archive.py",
        "headless_access_smoke.py",
        "progress.py",
        "run_distribution_smoke.py",
        "smoke_default_install.py",
        "smoke_agent_access.py",
        "smoke_optimized_archive.py",
        "smoke_powershell_install.py",
        "smoke_runtime_archive.py",
        "smoke_source_install.py",
    }

    assert moved_names <= {
        path.name for path in SCRIPTS_DIR.iterdir() if path.is_file()
    }
    legacy_root_names = {
        "build_crystal_lattice_optimized_archive.py",
        "build_crystal_lattice_python_runtime_archive.py",
        "bump_cli_version.py",
        "crystal_lattice_cli_boot.py",
        "crystal_lattice_distribution.py",
        "install.sh",
        "install_crystal_lattice_cli_dev.py",
        "install_current_crystal_lattice_archive.py",
        "run_cli_distribution_test.py",
        "smoke_test_crystal_lattice_archive.py",
        "smoke_test_crystal_lattice_default_install.py",
        "smoke_test_crystal_lattice_python_runtime_archive.py",
        "smoke_test_crystal_lattice_source_install.py",
    }
    assert not any((ROOT / "scripts" / name).exists() for name in legacy_root_names)


def test_headless_access_configs_are_minimal_and_never_store_provider_key(
    tmp_path: Path,
) -> None:
    default_config_dir = (
        ROOT / "application" / "python" / "agent_terminal_app" / "default_config"
    )
    source_config_dir = tmp_path / "source config"
    shutil.copytree(default_config_dir, source_config_dir)

    deterministic = headless_access_smoke.prepare_headless_access_config(
        source_config_dir / "config.json"
    )
    deterministic_config = json.loads(deterministic.read_text(encoding="utf-8"))
    assert set(deterministic_config["agents"]) == {
        headless_access_smoke.ACCESS_AGENT_ID
    }
    assert (
        deterministic_config["agents"][headless_access_smoke.ACCESS_AGENT_ID][
            "provider"
        ]
        == headless_access_smoke.ACCESS_PROVIDER_ID
    )

    real_config = smoke_agent_access.write_real_access_config(
        default_config_dir=default_config_dir,
        config_dir=tmp_path / "real config",
        workspace=tmp_path / "workspace",
    )
    real_text = real_config.read_text(encoding="utf-8")
    real = json.loads(real_text)
    assert real["providers"]["outer"]["api_key"] == "${env:OPENROUTER_API_KEY}"
    assert set(real["agents"]) == {
        smoke_agent_access.OUTER_AGENT,
        smoke_agent_access.CLI_WORKER,
        smoke_agent_access.SDK_WORKER,
    }
    assert "test-secret-must-not-appear" not in real_text


def test_real_access_acceptance_requires_method_evidence_in_tool_calls() -> None:
    marker = smoke_agent_access.CLI_MARKER
    worker = Session(
        session_id="worker-session",
        messages=[Message(role="assistant", content=marker)],
        metadata={"agent_id": smoke_agent_access.CLI_WORKER},
    )
    outer = Session(
        session_id="outer-session",
        messages=[
            Message(
                role="assistant",
                content="Using the requested method",
                metadata={
                    "tool_calls": [
                        {
                            "function": {
                                "name": "Bash",
                                "arguments": (
                                    "python -m agent_terminal_app run "
                                    "--agent cli-worker"
                                ),
                            }
                        }
                    ]
                },
            ),
            Message(role="assistant", content=marker),
        ],
    )
    result = SimpleNamespace(
        status="succeeded",
        output_text=marker,
        session_id=outer.session_id,
        to_dict=lambda: {},
    )

    smoke_agent_access._assert_method_result(
        result=result,
        records=[outer, worker],
        worker_id=smoke_agent_access.CLI_WORKER,
        marker=marker,
        method_evidence=('"name": "Bash"', "agent_terminal_app", "cli-worker"),
        secret="not-present",
    )

    with pytest.raises(RuntimeError, match="tool calls lack method evidence"):
        smoke_agent_access._assert_method_result(
            result=result,
            records=[outer, worker],
            worker_id=smoke_agent_access.CLI_WORKER,
            marker=marker,
            method_evidence=("open_runtime",),
            secret="not-present",
        )


def test_powershell_smoke_executes_the_public_alias_command_shape() -> None:
    script = POWERSHELL_SMOKE.read_text(encoding="utf-8")

    assert '"irm "' in script
    assert '"| iex; "' in script
    assert '"Invoke-RestMethod -Uri "' not in script
    assert '"| Invoke-Expression; "' not in script


def test_powershell_smoke_wraps_exact_installed_command_with_forwarded_args(
    tmp_path: Path,
) -> None:
    installed = tmp_path / "Crystal Lattice" / "crystal-lattice.cmd"
    installed.parent.mkdir()
    installed.touch()
    wrapper = tmp_path / "invoke installed.ps1"

    command = smoke_powershell_install.installed_command_invocation(
        powershell="powershell.exe",
        installed_command=installed,
        wrapper_path=wrapper,
    )

    assert command == [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(wrapper),
    ]
    assert wrapper.read_text(encoding="utf-8") == (
        f"& '{installed.resolve()}' @args\nexit $LASTEXITCODE\n"
    )
