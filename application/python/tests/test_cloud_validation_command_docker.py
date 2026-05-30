from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.docker]


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILES = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "cloud-agent"
    / "profiles"
)


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    expect_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env={**os.environ, **(env or {})},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"{result.stdout}"
        )
    return result


def _ensure_docker() -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker is not available")
    result = _run(["docker", "info"], cwd=ROOT, expect_success=False)
    if result.returncode != 0:
        pytest.skip(f"Docker daemon is not available\n{result.stdout}")


def _pythonpath_env() -> dict[str, str]:
    return {
        "PYTHONPATH": os.pathsep.join(
            [
                str(ROOT / "core" / "python"),
                str(ROOT / "application" / "python"),
                str(ROOT / "plugins" / "openrouter" / "src"),
                str(ROOT / "plugins" / "cloud-agent-app" / "src"),
            ]
        ),
        "BUILTIN_PLUGINS": str(ROOT / "plugins"),
    }


def _validation_config(
    workspace_dir: Path, *, runtime_image: str = "cloud-agent-runtime-validation:latest"
) -> dict[str, object]:
    transfer_up = DEFAULT_PROFILES / "transfer_up" / "working-tree-current-state"
    sync_down = DEFAULT_PROFILES / "sync_down" / "working-tree-patch"
    return {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools",
            "path:${env:BUILTIN_PLUGINS}/cloud-agent-app",
        ],
        "plugin_policy": {
            "install_deps": True,
        },
        "providers": {
            "dummy": {
                "provider": "openrouter",
                "model": "openai/gpt-5-mini",
                "api_key": "test-key",
                "base_url": "https://openrouter.ai/api/v1",
            }
        },
        "agents": {
            "default": {
                "provider": "dummy",
            }
        },
        "application": {
            "cloud_agent": {
                "workspace_dir": str(workspace_dir),
                "startup_poll_timeout_seconds": 180,
                "default_transfer_up_profile": "working-tree-current-state",
                "default_sync_down_profile": "working-tree-patch",
                "default_container_profile": "default-runtime",
                "transfer_up_profiles": {
                    "working-tree-current-state": {
                        "local_stage_script": str(workspace_dir / ".cloud-agent" / "local-stage"),
                        "local_transfer_script": str(transfer_up / "local_transfer_script"),
                        "cloud_setup_script": str(transfer_up / "cloud_setup_script"),
                        "install_script": str(workspace_dir / ".cloud-agent" / "install-cloud"),
                        "validation_script": str(workspace_dir / ".cloud-agent" / "validate-cloud"),
                        "compatible_sync_down_profiles": ["working-tree-patch"],
                    }
                },
                "sync_down_profiles": {
                    "working-tree-patch": {
                        "cloud_export_script": str(sync_down / "cloud_export_script"),
                        "cloud_mark_synced_script": str(sync_down / "cloud_mark_synced_script"),
                        "local_apply_script": str(sync_down / "local_apply_script"),
                        "compatible_transfer_up_profiles": ["working-tree-current-state"],
                    }
                },
                "container_profiles": {
                    "default-runtime": {
                        "image": runtime_image,
                    }
                },
                "config_assets": {
                    "include_config_dir": False,
                    "exclude": [],
                    "max_top_level_entry_bytes": 1_000_000,
                },
                "runtime_env": {
                    "include_config_env": False,
                    "include": [],
                    "exclude": [],
                    "env_files": [],
                },
            }
        },
    }


def _write_validation_config(
    tmp_path: Path, workspace_dir: Path, *, runtime_image: str
) -> Path:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(_validation_config(workspace_dir, runtime_image=runtime_image), indent=2),
        encoding="utf-8",
    )
    return config_path


def _initialize_git_workspace(workspace_dir: Path) -> None:
    _run(["git", "init"], cwd=workspace_dir)
    _run(["git", "config", "user.email", "cloud-validation@example.invalid"], cwd=workspace_dir)
    _run(["git", "config", "user.name", "Cloud Validation"], cwd=workspace_dir)


def _commit_all(workspace_dir: Path, message: str) -> None:
    _run(["git", "add", "."], cwd=workspace_dir)
    _run(["git", "commit", "-m", message], cwd=workspace_dir)


def _remove_docker_image(image_name: str) -> None:
    _run(["docker", "rmi", "-f", image_name], cwd=ROOT, expect_success=False)


def _write_script(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/usr/bin/env bash\nset -euo pipefail\n{body}", encoding="utf-8")
    path.chmod(0o755)


def _copy_repo_worktree(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "build",
            "dist",
            "node_modules",
            ".crystal",
            ".plugin_cache",
        ),
    )


def test_validate_cloud_command_succeeds_for_this_repository_hooks(tmp_path: Path) -> None:
    _ensure_docker()
    runtime_image = "cloud-agent-runtime:latest"
    _remove_docker_image(runtime_image)
    cache_dir = tmp_path / "cache"
    workspace = tmp_path / "workspace"
    _copy_repo_worktree(ROOT, workspace)
    _initialize_git_workspace(workspace)
    _commit_all(workspace, "snapshot")
    config_path = _write_validation_config(
        tmp_path, workspace, runtime_image=runtime_image
    )

    result = _run(
        [
            sys.executable,
            "-m",
            "agent_terminal_app",
            "--config",
            str(config_path),
            "validate-cloud",
            "--workspace-dir",
            str(workspace),
            "--cache-dir",
            str(cache_dir),
        ],
        cwd=ROOT,
        env=_pythonpath_env(),
    )

    assert "Cloud Validation Passed" in result.stdout
    assert "using local Docker" in result.stdout


def test_validate_cloud_command_fails_when_local_stage_does_not_stage_required_env(
    tmp_path: Path,
) -> None:
    _ensure_docker()
    runtime_image = "cloud-agent-runtime:latest"
    _remove_docker_image(runtime_image)
    cache_dir = tmp_path / "cache"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    (workspace / ".env").write_text("SECRET=value\n", encoding="utf-8")
    _write_script(
        workspace / ".cloud-agent" / "local-stage",
        'mkdir -p "${TRANSFER_STAGE_DIR}"\nprintf "skipped\\n" > "${TRANSFER_STAGE_DIR}/stage.txt"\n',
    )
    _write_script(
        workspace / ".cloud-agent" / "install-cloud",
        'test -f "${TRANSFER_STAGE_DIR}/.env"\nprintf "ok\\n" > "${CLOUD_WORKSPACE_DIR}/install.ok"\n',
    )
    _write_script(
        workspace / ".cloud-agent" / "validate-cloud",
        'test -f "${CLOUD_WORKSPACE_DIR}/install.ok"\n',
    )
    _initialize_git_workspace(workspace)
    _commit_all(workspace, "fixture")
    config_path = _write_validation_config(
        tmp_path, workspace, runtime_image=runtime_image
    )

    result = _run(
        [
            sys.executable,
            "-m",
            "agent_terminal_app",
            "--config",
            str(config_path),
            "validate-cloud",
            "--workspace-dir",
            str(workspace),
            "--cache-dir",
            str(cache_dir),
        ],
        cwd=ROOT,
        env=_pythonpath_env(),
        expect_success=False,
    )

    assert result.returncode == 1
    assert "cloud_install_running failed" in result.stdout


def test_validate_cloud_command_fails_when_validate_hook_exits_non_zero(
    tmp_path: Path,
) -> None:
    _ensure_docker()
    runtime_image = "cloud-agent-runtime:latest"
    _remove_docker_image(runtime_image)
    cache_dir = tmp_path / "cache"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _write_script(
        workspace / ".cloud-agent" / "local-stage",
        'mkdir -p "${TRANSFER_STAGE_DIR}"\n',
    )
    _write_script(
        workspace / ".cloud-agent" / "install-cloud",
        'printf "ok\\n" > "${CLOUD_WORKSPACE_DIR}/install.ok"\n',
    )
    _write_script(
        workspace / ".cloud-agent" / "validate-cloud",
        'echo "validate failed" >&2\nexit 9\n',
    )
    _initialize_git_workspace(workspace)
    _commit_all(workspace, "fixture")
    config_path = _write_validation_config(
        tmp_path, workspace, runtime_image=runtime_image
    )

    result = _run(
        [
            sys.executable,
            "-m",
            "agent_terminal_app",
            "--config",
            str(config_path),
            "validate-cloud",
            "--workspace-dir",
            str(workspace),
            "--cache-dir",
            str(cache_dir),
        ],
        cwd=ROOT,
        env=_pythonpath_env(),
        expect_success=False,
    )

    assert result.returncode == 1
    assert "cloud_validation_running failed" in result.stdout
    assert "validate failed" in result.stdout