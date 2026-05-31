from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.docker]


ROOT = Path(__file__).resolve().parents[3]


def test_installed_bundle_cloud_script_author_generates_valid_hooks(
    tmp_path: Path,
) -> None:
    executable, builtin_plugins, cloud_agent_plugin = _prepare_authoring_bundle(
        tmp_path
    )

    workspace = tmp_path / "workspace"
    _write_authoring_fixture(workspace)
    _initialize_git_workspace(workspace)
    _commit_paths(
        workspace,
        [
            ".gitignore",
            "AGENTS.md",
            "pyproject.toml",
            "src/fixture_app/__init__.py",
            "tests/test_fixture.py",
        ],
        "fixture baseline",
    )

    env = _authoring_env(tmp_path, workspace, builtin_plugins)
    _run_cloud_script_author(
        executable,
        workspace=workspace,
        env=env,
        cloud_agent_plugin=cloud_agent_plugin,
        allowed_project_paths=[workspace],
    )

    _assert_standard_hooks_exist(workspace)

    validation = _run_validate_cloud(
        executable,
        workspace=workspace,
        cache_dir=tmp_path / "cloud-validation-cache",
        env=env,
    )
    assert "Cloud Validation Passed" in validation.stdout


def test_installed_bundle_cloud_script_author_generates_multi_repo_transfer(
    tmp_path: Path,
) -> None:
    executable, builtin_plugins, cloud_agent_plugin = _prepare_authoring_bundle(
        tmp_path
    )

    fixture_root = tmp_path / "multi-repo"
    workspace, shared_repo = _write_multi_repo_authoring_fixture(fixture_root)
    _initialize_git_workspace(shared_repo)
    _commit_paths(
        shared_repo,
        ["pyproject.toml", "src/shared_lib/__init__.py"],
        "shared baseline",
    )
    (shared_repo / "src" / "shared_lib" / "__init__.py").write_text(
        "def shared_value() -> str:\n    return 'shared-working-tree'\n",
        encoding="utf-8",
    )
    _initialize_git_workspace(workspace)
    _commit_paths(
        workspace,
        [
            ".gitignore",
            "AGENTS.md",
            "pyproject.toml",
            "src/main_app/__init__.py",
            "tests/test_multi_repo.py",
        ],
        "main baseline",
    )

    env = _authoring_env(tmp_path, workspace, builtin_plugins)
    _run_cloud_script_author(
        executable,
        workspace=workspace,
        env=env,
        cloud_agent_plugin=cloud_agent_plugin,
        allowed_project_paths=[workspace, shared_repo],
        prompt=(
            "Create cloud installation scripts for this project, including any "
            "project cloud-agent config needed for its checkout layout."
        ),
        wait_timeout_seconds=600,
    )

    _assert_standard_hooks_exist(workspace)
    _assert_custom_multi_repo_profile(workspace)

    validation = _run_validate_cloud(
        executable,
        workspace=workspace,
        cache_dir=tmp_path / "multi-repo-cloud-validation-cache",
        env=env,
    )
    assert "Cloud Validation Passed" in validation.stdout


def _prepare_authoring_bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    if os.environ.get("RUN_CLOUD_SCRIPT_AUTHOR_BUNDLE_E2E") != "1":
        pytest.skip("RUN_CLOUD_SCRIPT_AUTHOR_BUNDLE_E2E != '1'")
    if shutil.which("docker") is None:
        pytest.skip("Docker is not available")

    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")

    archive_raw = os.environ.get("CRYSTAL_LATTICE_BUNDLE_ARCHIVE")
    if not archive_raw:
        pytest.skip("CRYSTAL_LATTICE_BUNDLE_ARCHIVE not set")
    archive_path = Path(archive_raw).expanduser().resolve()
    if not archive_path.is_file():
        pytest.skip(f"CRYSTAL_LATTICE_BUNDLE_ARCHIVE is not a file: {archive_path}")
    if not _archive_matches_current_platform(archive_path):
        pytest.skip(
            f"Bundle archive does not match current platform: {archive_path.name}"
        )

    _run(["docker", "info"], cwd=ROOT, skip_on_failure="Docker daemon is not available")

    bundle_dir = _extract_bundle_archive(archive_path, tmp_path / "bundle")
    executable = bundle_dir / (
        "crystal-lattice.exe" if os.name == "nt" else "crystal-lattice"
    )
    assert executable.is_file()
    layout = json.loads(
        _run([str(executable), "--runtime-layout-json"], cwd=tmp_path).stdout
    )
    builtin_plugins = Path(layout["env_overrides"]["BUILTIN_PLUGINS"])
    cloud_agent_plugin = builtin_plugins / "cloud-agent-app"
    assert (cloud_agent_plugin / "docs" / "cloud-script-authoring.md").is_file()
    return executable, builtin_plugins, cloud_agent_plugin


def _authoring_env(
    tmp_path: Path, workspace: Path, builtin_plugins: Path
) -> dict[str, str]:
    return {
        **_bundle_env(),
        **_docker_env(),
        "OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"],
        "HOME": str(tmp_path / "home"),
        "BUILTIN_PLUGINS": str(builtin_plugins),
        "CONFIG_DIR": str(workspace / ".crystal"),
        "PLUGIN_CACHE_DIR": str(workspace / ".crystal" / ".plugin_cache"),
        "WORKING_DIR": str(workspace),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "test-openai-key"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "test-gemini-key"),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", "test-tavily-key"),
        "FIREWORKS_API_KEY": os.environ.get("FIREWORKS_API_KEY", "test-fireworks-key"),
        "ZAI_API_KEY": os.environ.get("ZAI_API_KEY", "test-zai-key"),
        "CLOUD_ORCHESTRATOR_URL": "http://cloud-orchestrator.invalid",
        "CLOUD_ORCHESTRATOR_TOKEN": "test-cloud-token",
    }


def _run_cloud_script_author(
    executable: Path,
    *,
    workspace: Path,
    env: dict[str, str],
    cloud_agent_plugin: Path,
    allowed_project_paths: list[Path],
    prompt: str = "Create cloud installation scripts for this project.",
    wait_timeout_seconds: int = 240,
) -> None:
    port = _reserve_port()
    server = subprocess.Popen(
        [
            str(executable),
            "--config-local",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(workspace),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        _wait_for_server(base_url, server)
        created = _json_request(
            "POST",
            f"{base_url}/sessions",
            {"agent_id": "cloud-script-author"},
        )
        session_id = created["session"]["session_id"]
        model = (
            os.environ.get("CLOUD_SCRIPT_AUTHOR_TEST_MODEL") or "openai/gpt-5.4-mini"
        )
        _json_request(
            "POST",
            f"{base_url}/sessions/{session_id}/send_message",
            {
                "message": {
                    "role": "user",
                    "content": prompt,
                },
                "config_overrides": {
                    "model": model,
                    "reasoning_effort": "high",
                    "timeout": 600,
                    "working_directory": str(workspace),
                    "allowed_paths": [
                        *(str(path) for path in allowed_project_paths),
                        str(cloud_agent_plugin),
                    ],
                    "max_output_chars": 20000,
                },
            },
        )
        _wait_for_generated_hooks(workspace, timeout_seconds=wait_timeout_seconds)
    finally:
        server.terminate()
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=20)


def _assert_standard_hooks_exist(workspace: Path) -> None:
    for name in ("local-stage", "install-cloud", "validate-cloud"):
        path = workspace / ".cloud-agent" / name
        assert path.is_file(), name
        assert os.access(path, os.X_OK), name


def _run_validate_cloud(
    executable: Path, *, workspace: Path, cache_dir: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            str(executable),
            "--config-local",
            "validate-cloud",
            "--workspace-dir",
            str(workspace),
            "--cache-dir",
            str(cache_dir),
        ],
        cwd=workspace,
        env=env,
        timeout=900,
    )


def _write_authoring_fixture(workspace: Path) -> None:
    (workspace / "src" / "fixture_app").mkdir(parents=True)
    (workspace / "tests").mkdir()
    (workspace / ".gitignore").write_text(".env\n.venv\n", encoding="utf-8")
    (workspace / "AGENTS.md").write_text(
        """# Agent Guidelines

This project is a tiny Python package used as a fresh-checkout setup fixture.

From a clean checkout:
- keep the local `.env` available when running integration-style checks
- create a Python virtual environment in `.venv`
- upgrade `pip`, `setuptools`, and `wheel`
- install the package with `python -m pip install --no-build-isolation -e .`
- before tests, load values from `.env` into the process environment
- run `python -m unittest discover -s tests -q`
""",
        encoding="utf-8",
    )
    (workspace / "pyproject.toml").write_text(
        """[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "cloud-authoring-fixture"
version = "0.1.0"

[tool.setuptools.packages.find]
where = ["src"]
""",
        encoding="utf-8",
    )
    (workspace / "src" / "fixture_app" / "__init__.py").write_text(
        "def answer() -> int:\n    return 42\n",
        encoding="utf-8",
    )
    (workspace / "tests" / "test_fixture.py").write_text(
        """import os
import unittest

from fixture_app import answer


class FixtureTest(unittest.TestCase):
    def test_answer_and_env(self) -> None:
        self.assertEqual(answer(), 42)
        self.assertEqual(os.getenv("FIXTURE_SECRET"), "authoring")


if __name__ == "__main__":
    unittest.main()
""",
        encoding="utf-8",
    )
    (workspace / ".env").write_text("FIXTURE_SECRET=authoring\n", encoding="utf-8")


def _write_multi_repo_authoring_fixture(root: Path) -> tuple[Path, Path]:
    workspace = root / "app-service"
    shared_repo = root / "shared-lib"
    (workspace / "src" / "main_app").mkdir(parents=True)
    (workspace / "tests").mkdir(parents=True)
    (shared_repo / "src" / "shared_lib").mkdir(parents=True)
    (workspace / ".gitignore").write_text(".venv\n", encoding="utf-8")
    (workspace / "AGENTS.md").write_text(
        """# Agent Guidelines

This project is a two-repository Python fixture.

Repository layout from a fresh local checkout:
- `app-service/` is this main application repository.
- `shared-lib/` is a separate sibling git repository at `../shared-lib`.

Both repositories are ordinary git worktrees. When preparing any isolated
fresh-checkout environment, preserve the current working-tree state of both
repositories, including uncommitted local edits.

Fresh-checkout setup:
- keep `app-service` and `shared-lib` as sibling directories
- create a Python virtual environment in `app-service/.venv`
- upgrade `pip`, `setuptools`, and `wheel`
- install `../shared-lib` with `python -m pip install --no-build-isolation -e ../shared-lib`
- install this application with `python -m pip install --no-build-isolation -e .`
- run `python -m unittest discover -s tests -q` from `app-service`
""",
        encoding="utf-8",
    )
    (workspace / "pyproject.toml").write_text(
        """[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "multi-repo-app-fixture"
version = "0.1.0"

[tool.setuptools.packages.find]
where = ["src"]
""",
        encoding="utf-8",
    )
    (workspace / "src" / "main_app" / "__init__.py").write_text(
        """from shared_lib import shared_value


def combined_value() -> str:
    return f"main+{shared_value()}"
""",
        encoding="utf-8",
    )
    (workspace / "tests" / "test_multi_repo.py").write_text(
        """from pathlib import Path
import unittest

from main_app import combined_value


class MultiRepoTest(unittest.TestCase):
    def test_uses_sibling_repo_working_tree(self) -> None:
        self.assertEqual(combined_value(), "main+shared-working-tree")
        self.assertTrue(Path("../shared-lib/pyproject.toml").is_file())


if __name__ == "__main__":
    unittest.main()
""",
        encoding="utf-8",
    )
    (shared_repo / "pyproject.toml").write_text(
        """[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "multi-repo-shared-fixture"
version = "0.1.0"

[tool.setuptools.packages.find]
where = ["src"]
""",
        encoding="utf-8",
    )
    (shared_repo / "src" / "shared_lib" / "__init__.py").write_text(
        "def shared_value() -> str:\n    return 'shared-committed'\n",
        encoding="utf-8",
    )
    return workspace, shared_repo


def _assert_custom_multi_repo_profile(workspace: Path) -> None:
    config_path = workspace / ".cloud-agent" / "cloud-agent.json"
    assert config_path.is_file()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    transfer_id = config.get("default_transfer_up_profile")
    assert isinstance(transfer_id, str) and transfer_id
    transfer_profiles = config.get("transfer_up_profiles")
    assert isinstance(transfer_profiles, dict)
    profile = transfer_profiles.get(transfer_id)
    assert isinstance(profile, dict)

    local_transfer = _resolve_project_script_path(
        profile.get("local_transfer_script"), workspace
    )
    cloud_setup = _resolve_project_script_path(
        profile.get("cloud_setup_script"), workspace
    )
    assert local_transfer.is_file()
    assert cloud_setup.is_file()
    assert os.access(local_transfer, os.X_OK)
    assert os.access(cloud_setup, os.X_OK)

    transfer_text = local_transfer.read_text(encoding="utf-8")
    setup_text = cloud_setup.read_text(encoding="utf-8")
    assert "git" in transfer_text
    assert "shared-lib" in transfer_text
    assert "shared-lib" in setup_text


def _resolve_project_script_path(value: Any, workspace: Path) -> Path:
    if isinstance(value, list):
        for item in value:
            path = _resolve_project_script_path(item, workspace)
            if path.is_file():
                return path
        raise AssertionError(f"No script path exists in {value!r}")
    assert isinstance(value, str) and value.strip(), value
    raw = (
        value.replace("${env:WORKING_DIR}", str(workspace))
        .replace("${env:LOCAL_WORKSPACE_DIR}", str(workspace))
        .replace("$WORKING_DIR", str(workspace))
    )
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = workspace / path
    return path.resolve()


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


def _archive_matches_current_platform(path: Path) -> bool:
    name = path.name.lower()
    system = platform.system().lower()
    machine = platform.machine().lower()
    expected_platform = (
        "darwin"
        if system == "darwin"
        else "windows" if system == "windows" else "linux"
    )
    expected_arch = "arm64" if machine in {"arm64", "aarch64"} else "amd64"
    return f"-{expected_platform}-{expected_arch}" in name


def _bundle_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in ("CONFIG_DIR", "BUILTIN_PLUGINS", "PLUGIN_CACHE_DIR"):
        env.pop(key, None)
    return env


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


def _initialize_git_workspace(workspace: Path) -> None:
    _run(["git", "init"], cwd=workspace)
    _run(["git", "config", "user.email", "cloud-author@example.invalid"], cwd=workspace)
    _run(["git", "config", "user.name", "Cloud Author"], cwd=workspace)


def _commit_paths(workspace: Path, paths: list[str], message: str) -> None:
    _run(["git", "add", *paths], cwd=workspace)
    _run(["git", "commit", "-m", message], cwd=workspace)


def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(base_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 120
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise AssertionError(f"server exited early\n{output}")
        try:
            _json_request("GET", f"{base_url}/api/hello", None, timeout=2)
            return
        except Exception as exc:
            last_error = str(exc)
            time.sleep(0.5)
    raise AssertionError(f"server did not become ready: {last_error}")


def _wait_for_generated_hooks(workspace: Path, *, timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    hook_dir = workspace / ".cloud-agent"
    required = ["local-stage", "install-cloud", "validate-cloud"]
    while time.monotonic() < deadline:
        if all(
            (hook_dir / name).is_file() and os.access(hook_dir / name, os.X_OK)
            for name in required
        ):
            return
        time.sleep(1)
    found = (
        sorted(path.name for path in hook_dir.glob("*")) if hook_dir.exists() else []
    )
    raise AssertionError(f"timed out waiting for generated hooks; found={found}")


def _json_request(
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    *,
    timeout: int = 30,
) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"HTTP {exc.code} from {url}: {detail}") from exc
    return json.loads(body) if body else None


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    expect_success: bool = True,
    skip_on_failure: str | None = None,
    timeout: int | None = None,
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
        if skip_on_failure is not None:
            pytest.skip(f"{skip_on_failure}\n{result.stdout}")
        raise AssertionError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"{result.stdout}"
        )
    return result
