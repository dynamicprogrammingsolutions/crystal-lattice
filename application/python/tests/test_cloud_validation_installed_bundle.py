from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.docker]


ROOT = Path(__file__).resolve().parents[3]


def test_installed_bundle_validate_cloud_builds_runtime_from_bundle(
    tmp_path: Path,
) -> None:
    archive_raw = os.environ.get("CRYSTAL_LATTICE_BUNDLE_ARCHIVE")
    if not archive_raw:
        pytest.skip("CRYSTAL_LATTICE_BUNDLE_ARCHIVE not set")
    archive_path = Path(archive_raw).expanduser().resolve()
    if not archive_path.is_file():
        pytest.skip(f"CRYSTAL_LATTICE_BUNDLE_ARCHIVE is not a file: {archive_path}")
    if not _archive_matches_current_platform(archive_path):
        pytest.skip(f"Bundle archive does not match current platform: {archive_path.name}")
    _ensure_docker()

    bundle_dir = _extract_bundle_archive(archive_path, tmp_path / "bundle")
    executable = bundle_dir / ("crystal-lattice.exe" if os.name == "nt" else "crystal-lattice")
    assert executable.is_file()

    layout_result = _run([str(executable), "--runtime-layout-json"], cwd=tmp_path)
    layout = json.loads(layout_result.stdout)
    assert layout["layout"] == "bundled"
    env_overrides = layout["env_overrides"]
    assert "/_internal/bundled_plugins" in env_overrides["BUILTIN_PLUGINS"]
    bundle_paths = layout["bundle_paths"]
    runtime_context = Path(bundle_paths["cloud_runtime_build_context"])
    runtime_dockerfile = Path(bundle_paths["cloud_runtime_dockerfile"])
    assert "_internal/cloud_runtime" in str(runtime_context)
    assert runtime_context.is_dir()
    assert runtime_dockerfile.is_file()

    workspace = tmp_path / "workspace"
    _write_validation_fixture(workspace)
    runtime_image = f"cloud-agent-runtime-validation-{os.getpid()}:01215"
    _write_project_cloud_config(workspace, runtime_image=runtime_image)
    _initialize_git_workspace(workspace)

    try:
        result = _run(
            [
                str(executable),
                "--config-local",
                "validate-cloud",
                "--workspace-dir",
                str(workspace),
                "--cache-dir",
                str(tmp_path / "cloud-cache"),
                "--runtime-build-context",
                str(runtime_context),
                "--runtime-dockerfile",
                str(runtime_dockerfile),
            ],
            cwd=workspace,
            env={
                **_bundle_env(),
                **_docker_env(),
                "BUILTIN_PLUGINS": env_overrides["BUILTIN_PLUGINS"],
                "CONFIG_DIR": str(workspace / ".crystal"),
                "HOME": str(tmp_path / "home"),
                "PLUGIN_CACHE_DIR": str(workspace / ".crystal" / ".plugin_cache"),
                "WORKING_DIR": str(workspace),
            },
            timeout=900,
        )
        assert "Cloud Validation Passed" in result.stdout

        inspect = _run(
            [
                "docker",
                "image",
                "inspect",
                runtime_image,
                "--format",
                "{{ index .Config.Labels \"org.crystal-lattice.cloud-runtime.digest\" }}",
            ],
            cwd=ROOT,
        )
        digest = inspect.stdout.strip()
        assert digest
        assert digest != "<no value>"
    finally:
        _run(["docker", "rmi", "-f", runtime_image], cwd=ROOT, expect_success=False)


def _write_validation_fixture(workspace: Path) -> None:
    (workspace / ".cloud-agent").mkdir(parents=True)
    (workspace / "AGENTS.md").write_text(
        """# Agent Guidelines

This is a small Python fixture. From a fresh checkout, keep the local `.env`
available for validation and run the Python standard-library smoke check.
""",
        encoding="utf-8",
    )
    (workspace / "fixture.py").write_text(
        "def value() -> str:\n    return 'bundle-cloud-validation'\n",
        encoding="utf-8",
    )
    (workspace / ".gitignore").write_text(".env\n", encoding="utf-8")
    (workspace / ".env").write_text(
        "FIXTURE_SECRET=bundle-cloud-validation\n",
        encoding="utf-8",
    )
    (workspace / ".cloud-agent" / "local-stage").write_text(
        """#!/usr/bin/env bash
set -euo pipefail
: "${LOCAL_WORKSPACE_DIR:?}"
: "${TRANSFER_STAGE_DIR:?}"
mkdir -p "${TRANSFER_STAGE_DIR}"
cp "${LOCAL_WORKSPACE_DIR}/.env" "${TRANSFER_STAGE_DIR}/.env"
""",
        encoding="utf-8",
    )
    (workspace / ".cloud-agent" / "install-cloud").write_text(
        """#!/usr/bin/env bash
set -euo pipefail
: "${CLOUD_WORKSPACE_DIR:?}"
cd "${CLOUD_WORKSPACE_DIR}"
test -f .env
python3 - <<'PY'
import fixture
assert fixture.value() == "bundle-cloud-validation"
PY
printf 'installed\n' > .cloud-agent-install-ok
""",
        encoding="utf-8",
    )
    (workspace / ".cloud-agent" / "validate-cloud").write_text(
        """#!/usr/bin/env bash
set -euo pipefail
: "${CLOUD_WORKSPACE_DIR:?}"
cd "${CLOUD_WORKSPACE_DIR}"
test -f .env
test -f .cloud-agent-install-ok
. ./.env
test "${FIXTURE_SECRET}" = "bundle-cloud-validation"
python3 - <<'PY'
import fixture
assert fixture.value() == "bundle-cloud-validation"
PY
""",
        encoding="utf-8",
    )
    for name in ("local-stage", "install-cloud", "validate-cloud"):
        (workspace / ".cloud-agent" / name).chmod(0o755)


def _write_project_cloud_config(workspace: Path, *, runtime_image: str) -> None:
    (workspace / ".cloud-agent" / "cloud-agent.json").write_text(
        json.dumps(
            {
                "container_profiles": {
                    "default-runtime": {
                        "image": runtime_image,
                    }
                }
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _initialize_git_workspace(workspace: Path) -> None:
    _run(["git", "init"], cwd=workspace)
    _run(["git", "config", "user.email", "bundle-cloud@example.invalid"], cwd=workspace)
    _run(["git", "config", "user.name", "Bundle Cloud"], cwd=workspace)
    _run(
        ["git", "add", ".gitignore", "AGENTS.md", "fixture.py", ".cloud-agent"],
        cwd=workspace,
    )
    _run(["git", "commit", "-m", "fixture"], cwd=workspace)


def _archive_matches_current_platform(path: Path) -> bool:
    name = path.name.lower()
    system = platform.system().lower()
    machine = platform.machine().lower()
    expected_platform = "darwin" if system == "darwin" else "windows" if system == "windows" else "linux"
    expected_arch = "arm64" if machine in {"arm64", "aarch64"} else "amd64"
    return f"-{expected_platform}-{expected_arch}" in name


def _extract_bundle_archive(archive_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True)
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(target_dir)
    else:
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(target_dir)
    directories = [path for path in target_dir.iterdir() if path.is_dir()]
    assert len(directories) == 1, directories
    return directories[0]


def _bundle_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in ("CONFIG_DIR", "BUILTIN_PLUGINS", "PLUGIN_CACHE_DIR"):
        env.pop(key, None)
    return {
        **env,
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY", "test-openrouter-key"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "test-openai-key"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "test-gemini-key"),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", "test-tavily-key"),
        "FIREWORKS_API_KEY": os.environ.get("FIREWORKS_API_KEY", "test-fireworks-key"),
        "ZAI_API_KEY": os.environ.get("ZAI_API_KEY", "test-zai-key"),
    }


def _ensure_docker() -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker is not available")
    result = _run(["docker", "info"], cwd=ROOT, expect_success=False)
    if result.returncode != 0:
        pytest.skip(f"Docker daemon is not available\n{result.stdout}")


def _docker_env() -> dict[str, str]:
    if os.environ.get("DOCKER_HOST"):
        return {"DOCKER_HOST": os.environ["DOCKER_HOST"]}
    result = _run(
        ["docker", "context", "inspect", "--format", "{{json .Endpoints.docker.Host}}"],
        cwd=ROOT,
        expect_success=False,
    )
    if result.returncode != 0:
        return {}
    try:
        host = json.loads(result.stdout.strip())
    except Exception:
        return {}
    return {"DOCKER_HOST": host} if isinstance(host, str) and host else {}


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 120,
    expect_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env={**os.environ, **(env or {})},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"{result.stdout}"
        )
    return result