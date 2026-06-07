from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import warnings
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.docker]


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CHATGPT_CREDENTIALS = Path.home() / ".crystal" / "auth" / "chatgpt-auth.json"

STANDARD_TOOL_BUDGET = {"soft": 20, "hard": 45}
MULTI_REPO_TOOL_BUDGET = {"soft": 40, "hard": 80}
AUTHORING_REQUEST_TIMEOUT = {"soft": 900, "hard": 1800}
AUTHORING_NO_PROGRESS_TIMEOUT_SECONDS = int(
    os.environ.get("CLOUD_SCRIPT_AUTHOR_NO_PROGRESS_TIMEOUT", "900")
)
VALIDATE_CLOUD_TIMEOUT = {"soft": 900, "hard": 1800}


@dataclass(frozen=True)
class AuthoringTelemetry:
    scenario: str
    tool_call_count: int
    tool_calls_by_name: dict[str, int]
    docs_read: bool
    plugin_source_read: bool
    example_tests_read: bool
    syntax_check_attempted: bool
    fast_local_test_attempted: bool
    fast_local_harness_generated: bool
    validate_cloud_attempted: bool
    command_failure_count: int
    generated_files: list[str]


@dataclass
class LiveAuthoringTraceState:
    printed_first_user_message: bool = False
    printed_assistant_message_indexes: set[int] | None = None
    last_tool_calls_sent: int = -1
    last_tool_calls_completed: int = -1

    def __post_init__(self) -> None:
        if self.printed_assistant_message_indexes is None:
            self.printed_assistant_message_indexes = set()


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
    telemetry = _run_cloud_script_author(
        executable,
        scenario="standard",
        workspace=workspace,
        env=env,
        cloud_agent_plugin=cloud_agent_plugin,
        allowed_project_paths=[workspace],
        hard_tool_limit=STANDARD_TOOL_BUDGET["hard"],
    )
    _assert_authoring_telemetry(telemetry, STANDARD_TOOL_BUDGET)

    _assert_standard_hooks_exist(workspace)
    _use_existing_runtime_image_for_validation_if_available(workspace)

    validation_cache = tmp_path / "cloud-validation-cache"
    validation = _run_validate_cloud(
        executable,
        workspace=workspace,
        cache_dir=validation_cache,
        env=env,
    )
    assert "Cloud Validation Passed" in validation.stdout
    _assert_bundled_plugins_not_installed_to_runtime_cache(validation_cache)


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
    telemetry = _run_cloud_script_author(
        executable,
        scenario="multi-repo",
        workspace=workspace,
        env=env,
        cloud_agent_plugin=cloud_agent_plugin,
        allowed_project_paths=[workspace, shared_repo],
        prompt=(
            "Create cloud installation scripts for this project, including any "
            "project cloud-agent config needed for its checkout layout."
        ),
        wait_timeout_seconds=AUTHORING_REQUEST_TIMEOUT["hard"],
        soft_wait_timeout_seconds=AUTHORING_REQUEST_TIMEOUT["soft"],
        hard_tool_limit=MULTI_REPO_TOOL_BUDGET["hard"],
        require_fast_local_harness=True,
    )
    _assert_authoring_telemetry(
        telemetry,
        MULTI_REPO_TOOL_BUDGET,
        require_fast_local_harness=True,
    )

    _assert_standard_hooks_exist(workspace)
    _assert_custom_multi_repo_profile(workspace)
    _use_existing_runtime_image_for_validation_if_available(workspace)

    validation_cache = tmp_path / "multi-repo-cloud-validation-cache"
    validation = _run_validate_cloud(
        executable,
        workspace=workspace,
        cache_dir=validation_cache,
        env=env,
    )
    assert "Cloud Validation Passed" in validation.stdout
    _assert_bundled_plugins_not_installed_to_runtime_cache(validation_cache)


def _prepare_authoring_bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    if os.environ.get("RUN_CLOUD_SCRIPT_AUTHOR_BUNDLE_E2E") != "1":
        pytest.skip("RUN_CLOUD_SCRIPT_AUTHOR_BUNDLE_E2E != '1'")
    if shutil.which("docker") is None:
        pytest.skip("Docker is not available")

    _ensure_authoring_auth_available()

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
    executable = _bundle_executable(bundle_dir)
    layout = json.loads(
        _run([str(executable), "--runtime-layout-json"], cwd=tmp_path).stdout
    )
    builtin_plugins = Path(layout["env_overrides"]["BUILTIN_PLUGINS"])
    cloud_agent_plugin = builtin_plugins / "cloud-agent-app"
    guide_path = cloud_agent_plugin / "docs" / "cloud-script-authoring.md"
    assert guide_path.is_file()
    _assert_bundled_authoring_guide_has_container_profile_contract(guide_path)
    return executable, builtin_plugins, cloud_agent_plugin


def _authoring_env(
    tmp_path: Path, workspace: Path, builtin_plugins: Path
) -> dict[str, str]:
    return {
        **_bundle_env(),
        **_docker_env(),
        "HOME": str(tmp_path / "home"),
        "BUILTIN_PLUGINS": str(builtin_plugins),
        "CONFIG_DIR": str(workspace / ".crystal"),
        "PLUGIN_CACHE_DIR": str(workspace / ".crystal" / ".plugin_cache"),
        "WORKING_DIR": str(workspace),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "test-gemini-key"),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", "test-tavily-key"),
        "FIREWORKS_API_KEY": os.environ.get("FIREWORKS_API_KEY", "test-fireworks-key"),
        "ZAI_API_KEY": os.environ.get("ZAI_API_KEY", "test-zai-key"),
        "CLOUD_ORCHESTRATOR_URL": "http://cloud-orchestrator.invalid",
        "CLOUD_ORCHESTRATOR_TOKEN": "test-cloud-token",
    }


def _ensure_authoring_auth_available() -> None:
    credentials_path = _chatgpt_credentials_path_from_env()
    if credentials_path is not None:
        if not credentials_path.is_file():
            raise AssertionError(
                f"CHATGPT_CREDENTIALS is not a file: {credentials_path}"
            )
        return
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set and CHATGPT_CREDENTIALS not set")


def _chatgpt_credentials_path_from_env() -> Path | None:
    raw = os.environ.get("CHATGPT_CREDENTIALS")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser().resolve()
    if DEFAULT_CHATGPT_CREDENTIALS.is_file():
        return DEFAULT_CHATGPT_CREDENTIALS.resolve()
    return None


def _authoring_auth_overrides() -> dict[str, str]:
    credentials_path = _chatgpt_credentials_path_from_env()
    if credentials_path is None:
        return {}
    if not credentials_path.is_file():
        raise AssertionError(f"CHATGPT_CREDENTIALS is not a file: {credentials_path}")
    return {
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
    }


def _assert_bundled_authoring_guide_has_container_profile_contract(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    normalized = " ".join(text.split()).lower()
    for required in (
        "container_profiles",
        "default_container_profile",
        "dockerfile mode",
        "build_assets",
        "cache_mounts",
        "mounts",
        "hard project boundary",
        "cannot use project files implicitly",
        "runtime workspace mount",
        "copy the default dockerfile",
        "from cloud-agent-runtime as project-runtime",
    ):
        assert required in normalized, f"{required!r} missing from {path}"


def _run_cloud_script_author(
    executable: Path,
    *,
    scenario: str,
    workspace: Path,
    env: dict[str, str],
    cloud_agent_plugin: Path,
    allowed_project_paths: list[Path],
    hard_tool_limit: int,
    prompt: str = "Create cloud installation scripts for this project.",
    wait_timeout_seconds: int = AUTHORING_REQUEST_TIMEOUT["hard"],
    soft_wait_timeout_seconds: int = AUTHORING_REQUEST_TIMEOUT["soft"],
    require_fast_local_harness: bool = False,
) -> AuthoringTelemetry:
    port = _reserve_port()
    session_id = ""
    events: list[dict[str, Any]] = []
    server_env = {
        **env,
        "PATH": f"{executable.parent}{os.pathsep}{env.get('PATH') or os.environ.get('PATH', '')}",
    }
    _prepare_authoring_config(executable, workspace, env=server_env)
    server_log_path = workspace / ".cloud-agent-authoring-server.log"
    server_log = server_log_path.open("w", encoding="utf-8")
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
        env=server_env,
        stdout=server_log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        _write_authoring_diagnostic(
            workspace,
            {
                "type": "server_started",
                "scenario": scenario,
                "pid": server.pid,
                "port": port,
                "server_log": str(server_log_path),
            },
        )
        _wait_for_server(base_url, server, server_log_path=server_log_path)
        created = _json_request(
            "POST",
            f"{base_url}/sessions",
            {"agent_id": "cloud-script-author"},
        )
        session_id = created["session"]["session_id"]
        default_model = "gpt-5.4" if scenario == "multi-repo" else "gpt-5.4-mini"
        model = os.environ.get("CLOUD_SCRIPT_AUTHOR_TEST_MODEL") or default_model
        auth_overrides = _authoring_auth_overrides()
        _write_authoring_diagnostic(
            workspace,
            {
                "type": "request_starting",
                "scenario": scenario,
                "session_id": session_id,
                "model": model,
                "auth_mode": auth_overrides.get("auth_mode") or "default",
            },
        )
        response = _json_request(
            "POST",
            f"{base_url}/sessions/{session_id}/send_message",
            {
                "message": {
                    "role": "user",
                    "content": prompt,
                },
                "config_overrides": {
                    **auth_overrides,
                    "model": model,
                    "reasoning_effort": "high",
                    "timeout": 600,
                    "working_directory": str(workspace),
                    "allowed_paths": [
                        *(str(path) for path in allowed_project_paths),
                        str(cloud_agent_plugin),
                        str(workspace / ".crystal" / "cloud-agent" / "profiles"),
                    ],
                    "max_output_chars": 20000,
                },
            },
        )
        request_id = response["request_id"]
        _write_authoring_diagnostic(
            workspace,
            {
                "type": "request_started",
                "scenario": scenario,
                "session_id": session_id,
                "request_id": request_id,
            },
        )
        events = _wait_for_request_events(
            base_url,
            request_id,
            workspace=workspace,
            session_id=session_id,
            timeout_seconds=wait_timeout_seconds,
            soft_timeout_seconds=soft_wait_timeout_seconds,
            hard_tool_limit=hard_tool_limit,
            require_fast_local_harness=require_fast_local_harness,
        )
        _wait_for_generated_hooks(workspace, timeout_seconds=wait_timeout_seconds)
    finally:
        server.terminate()
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=20)
        server_log.close()
    return _collect_authoring_telemetry(
        scenario=scenario,
        workspace=workspace,
        session_id=session_id,
        events=events,
    )


def _prepare_authoring_config(
    executable: Path, workspace: Path, *, env: dict[str, str]
) -> None:
    auth_overrides = _authoring_auth_overrides()
    if not auth_overrides:
        return

    layout = json.loads(
        _run([str(executable), "--runtime-layout-json"], cwd=workspace, env=env).stdout
    )
    default_config_template = Path(layout["bundle_paths"]["default_config_template"])
    config_dir = workspace / ".crystal"
    if config_dir.exists():
        shutil.rmtree(config_dir)
    shutil.copytree(
        default_config_template,
        config_dir,
        ignore=shutil.ignore_patterns("auth", ".plugin_cache", "__pycache__"),
    )

    config_path = config_dir / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    providers = config.get("providers")
    assert isinstance(providers, dict)
    openai = providers.get("openai")
    assert isinstance(openai, dict)
    openai.update(auth_overrides)
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")


def _assert_standard_hooks_exist(workspace: Path) -> None:
    for name in ("local-stage", "install-cloud", "validate-cloud"):
        path = workspace / ".cloud-agent" / name
        assert path.is_file(), name
        assert os.access(path, os.X_OK), name


def _run_validate_cloud(
    executable: Path, *, workspace: Path, cache_dir: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    print("[validate-cloud] starting", flush=True)
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
        timeout=VALIDATE_CLOUD_TIMEOUT["hard"],
        soft_timeout=VALIDATE_CLOUD_TIMEOUT["soft"],
    )


def _assert_bundled_plugins_not_installed_to_runtime_cache(cache_dir: Path) -> None:
    plugin_cache = cache_dir / "plugin_cache" / "plugins"
    if not plugin_cache.exists():
        return
    installed_names = sorted(
        path.name for path in plugin_cache.iterdir() if path.is_dir()
    )
    assert installed_names == []


def _use_existing_runtime_image_for_validation_if_available(workspace: Path) -> None:
    source_image = "cloud-agent-runtime:latest"
    test_image = "cloud-script-author-validation-runtime:latest"
    inspect = _run(
        ["docker", "image", "inspect", source_image],
        cwd=workspace,
        expect_success=False,
    )
    if inspect.returncode != 0:
        return
    image_env = _docker_image_env(source_image, cwd=workspace)
    if image_env.get("BUILTIN_PLUGINS") != (
        "/opt/ai-agent-platform/cloud-runtime-plugin-bundle/bundled_plugins"
    ):
        return
    _run(["docker", "tag", source_image, test_image], cwd=workspace)

    config_path = workspace / ".cloud-agent" / "cloud-agent.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
    else:
        config = {}
    profiles = config.get("container_profiles")
    if not isinstance(profiles, dict):
        profiles = {}
    profiles["authoring-test-runtime"] = {
        "label": "Authoring test runtime",
        "image": test_image,
    }
    config["container_profiles"] = profiles
    config["default_container_profile"] = "authoring-test-runtime"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")


def _docker_image_env(image: str, *, cwd: Path) -> dict[str, str]:
    result = _run(
        ["docker", "image", "inspect", image, "--format", "{{json .Config.Env}}"],
        cwd=cwd,
        expect_success=False,
    )
    if result.returncode != 0:
        return {}
    try:
        values = json.loads(result.stdout)
    except Exception:
        return {}
    if not isinstance(values, list):
        return {}
    env: dict[str, str] = {}
    for value in values:
        if not isinstance(value, str) or "=" not in value:
            continue
        key, raw = value.split("=", 1)
        env[key] = raw
    return env


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
    assert "shared-lib" in setup_text or "manifest" in setup_text


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


def _bundle_executable(bundle_dir: Path) -> Path:
    candidates = (
        [bundle_dir / "crystal-lattice.exe", bundle_dir / "bin" / "crystal-lattice.exe"]
        if os.name == "nt"
        else [bundle_dir / "crystal-lattice", bundle_dir / "bin" / "crystal-lattice"]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise AssertionError(f"bundle executable not found under {bundle_dir}")


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


def _wait_for_server(
    base_url: str, process: subprocess.Popen[str], *, server_log_path: Path
) -> None:
    deadline = time.monotonic() + 120
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = _read_text_tail(server_log_path, max_chars=20_000)
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
    while time.monotonic() < deadline:
        if _hooks_generated(workspace):
            return
        time.sleep(1)
    found = (
        sorted(path.name for path in hook_dir.glob("*")) if hook_dir.exists() else []
    )
    raise AssertionError(f"timed out waiting for generated hooks; found={found}")


def _hooks_generated(workspace: Path) -> bool:
    hook_dir = workspace / ".cloud-agent"
    required = ["local-stage", "install-cloud", "validate-cloud"]
    return all(
        (hook_dir / name).is_file() and os.access(hook_dir / name, os.X_OK)
        for name in required
    )


def _wait_for_request_events(
    base_url: str,
    request_id: str,
    *,
    workspace: Path,
    session_id: str,
    timeout_seconds: int,
    soft_timeout_seconds: int,
    hard_tool_limit: int,
    require_fast_local_harness: bool,
) -> list[dict[str, Any]]:
    started_at = time.monotonic()
    deadline = started_at + timeout_seconds
    soft_deadline = started_at + soft_timeout_seconds
    no_progress_timeout = AUTHORING_NO_PROGRESS_TIMEOUT_SECONDS
    last_progress_at = started_at
    last_signature: dict[str, Any] = {}
    warned_soft_timeout = False
    collected: list[dict[str, Any]] = []
    trace_state = LiveAuthoringTraceState()
    while time.monotonic() < deadline:
        now = time.monotonic()
        if not warned_soft_timeout and now >= soft_deadline:
            warned_soft_timeout = True
            warnings.warn(
                "cloud-script-author request exceeded soft timeout "
                f"{soft_timeout_seconds}s; continuing until hard timeout "
                f"{timeout_seconds}s",
                stacklevel=2,
            )
        try:
            payload = _json_request(
                "GET",
                f"{base_url}/events?request_id={request_id}&limit=80",
                None,
                timeout=30,
            )
        except TimeoutError:
            _write_authoring_diagnostic(
                workspace,
                {
                    "type": "events_poll_timeout",
                    "request_id": request_id,
                    "elapsed_seconds": round(time.monotonic() - started_at, 3),
                    "session": _session_summary(workspace, session_id),
                },
            )
            time.sleep(1)
            continue
        collected = payload.get("events") or []
        _emit_live_authoring_trace(
            workspace=workspace,
            session_id=session_id,
            events=collected,
            state=trace_state,
        )
        signature = _authoring_progress_signature(
            workspace=workspace,
            session_id=session_id,
            events=collected,
        )
        if signature != last_signature:
            last_signature = signature
            last_progress_at = now
        _write_authoring_diagnostic(
            workspace,
            {
                "type": "events_poll",
                "request_id": request_id,
                "elapsed_seconds": round(now - started_at, 3),
                "seconds_since_progress": round(now - last_progress_at, 3),
                **signature,
            },
        )
        if any(event.get("type") == "request_completed" for event in collected):
            return collected
        error_events = [event for event in collected if event.get("type") == "error"]
        if error_events:
            raise AssertionError(
                "request failed: "
                f"{error_events[-1]}\n"
                f"diagnostics={_diagnostics_path(workspace)}\n"
                f"session={_session_summary(workspace, session_id)}"
            )
        tool_count = _tool_count_from_events(collected)
        if tool_count > hard_tool_limit:
            raise AssertionError(
                f"request exceeded hard tool limit {hard_tool_limit}; "
                f"observed {tool_count} tool calls\n"
                f"diagnostics={_diagnostics_path(workspace)}\n"
                f"session={_session_summary(workspace, session_id)}"
            )
        if _authoring_progress_is_sufficient(
            workspace=workspace,
            session_id=session_id,
            events=collected,
            require_fast_local_harness=require_fast_local_harness,
        ):
            return collected
        if now - last_progress_at >= no_progress_timeout:
            raise AssertionError(
                "cloud-script-author request made no observable progress for "
                f"{no_progress_timeout}s\n"
                f"request_id={request_id}\n"
                f"diagnostics={_diagnostics_path(workspace)}\n"
                f"session={_session_summary(workspace, session_id)}"
            )
        time.sleep(1)
    raise AssertionError(
        f"timed out waiting for request {request_id}: {collected}\n"
        f"diagnostics={_diagnostics_path(workspace)}\n"
        f"session={_session_summary(workspace, session_id)}"
    )


def _diagnostics_path(workspace: Path) -> Path:
    return workspace / ".cloud-agent-authoring-diagnostics.jsonl"


def _write_authoring_diagnostic(workspace: Path, payload: dict[str, Any]) -> None:
    path = _diagnostics_path(workspace)
    record = {
        "timestamp": time.time(),
        **payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _authoring_progress_signature(
    *, workspace: Path, session_id: str, events: list[dict[str, Any]]
) -> dict[str, Any]:
    event_types = [
        event.get("type") for event in events if isinstance(event.get("type"), str)
    ]
    session = _session_summary(workspace, session_id)
    generated = _generated_cloud_agent_files(workspace)
    return {
        "event_count": len(events),
        "last_event_type": event_types[-1] if event_types else None,
        "event_types_tail": event_types[-8:],
        "message_count": session.get("message_count"),
        "last_message_role": session.get("last_message_role"),
        "last_message_tool": session.get("last_message_tool"),
        "last_message_preview": session.get("last_message_preview"),
        "generated_files": generated,
    }


def _session_summary(workspace: Path, session_id: str) -> dict[str, Any]:
    if not session_id:
        return {"session_id": session_id, "message_count": 0}
    session_path = workspace / ".crystal" / "sessions" / f"{session_id}.json"
    if not session_path.is_file():
        return {"session_id": session_id, "missing": True, "message_count": 0}
    try:
        payload = json.loads(session_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"session_id": session_id, "error": str(exc), "message_count": 0}
    messages = payload.get("messages") if isinstance(payload, dict) else None
    if not isinstance(messages, list) or not messages:
        return {"session_id": session_id, "message_count": 0}
    last = messages[-1] if isinstance(messages[-1], dict) else {}
    metadata = last.get("metadata") if isinstance(last.get("metadata"), dict) else {}
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "last_message_role": last.get("role"),
        "last_message_tool": metadata.get("tool_name"),
        "last_message_preview": str(last.get("content") or "")
        .replace("\n", " ")[:400],
    }


def _read_text_tail(path: Path, *, max_chars: int) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-max_chars:]


def _emit_live_authoring_trace(
    *,
    workspace: Path,
    session_id: str,
    events: list[dict[str, Any]],
    state: LiveAuthoringTraceState,
) -> None:
    messages = _load_session_messages(workspace, session_id)
    first_user = _first_user_message(messages)
    if first_user is not None and not state.printed_first_user_message:
        _print_trace_block("user", first_user)
        state.printed_first_user_message = True

    for index, message in enumerate(messages):
        if index in state.printed_assistant_message_indexes:
            continue
        if not _is_traceable_assistant_message(message):
            continue
        reasoning = _message_reasoning(message)
        content = _message_content_text(message)
        if reasoning:
            _print_trace_block("assistant reasoning", reasoning)
        if content:
            _print_trace_block("assistant", content)
        if reasoning or content:
            state.printed_assistant_message_indexes.add(index)

    tool_calls_sent, tool_calls_completed = _tool_progress_from_events(events)
    if (
        tool_calls_sent != state.last_tool_calls_sent
        or tool_calls_completed != state.last_tool_calls_completed
    ):
        print(
            "[authoring][tools] "
            f"sent={tool_calls_sent} completed={tool_calls_completed}",
            flush=True,
        )
        state.last_tool_calls_sent = tool_calls_sent
        state.last_tool_calls_completed = tool_calls_completed


def _print_trace_block(label: str, text: str) -> None:
    normalized = text.strip()
    if not normalized:
        return
    print(f"[authoring][{label}]", flush=True)
    print(normalized, flush=True)
    print("", flush=True)


def _first_user_message(messages: list[dict[str, Any]]) -> str | None:
    for message in messages:
        if message.get("role") != "user":
            continue
        content = _message_content_text(message)
        if content:
            return content
    return None


def _is_traceable_assistant_message(message: dict[str, Any]) -> bool:
    if message.get("role") != "assistant":
        return False
    metadata = message.get("metadata")
    if isinstance(metadata, dict) and isinstance(metadata.get("tool_name"), str):
        return False
    return bool(_message_reasoning(message) or _message_content_text(message))


def _message_reasoning(message: dict[str, Any]) -> str:
    metadata = message.get("metadata")
    if isinstance(metadata, dict):
        reasoning = metadata.get("reasoning")
        if isinstance(reasoning, str):
            return reasoning.strip()
    direct_reasoning = message.get("reasoning")
    return direct_reasoning.strip() if isinstance(direct_reasoning, str) else ""


def _message_content_text(message: dict[str, Any]) -> str:
    chunks: list[str] = []
    _append_message_content_chunks(chunks, message.get("content"))
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def _append_message_content_chunks(chunks: list[str], value: Any) -> None:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            chunks.append(stripped)
        return
    if isinstance(value, list):
        for item in value:
            _append_message_content_chunks(chunks, item)
        return
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            stripped = text.strip()
            if stripped:
                chunks.append(stripped)
            return
        content = value.get("content")
        if content is not None:
            _append_message_content_chunks(chunks, content)


def _tool_progress_from_events(events: list[dict[str, Any]]) -> tuple[int, int]:
    tool_result_ids: set[str] = set()
    tool_call_ids: set[str] = set()
    for event in events:
        if event.get("type") == "tool_results":
            messages = event.get("messages")
            if isinstance(messages, list):
                for message in messages:
                    metadata = (
                        message.get("metadata") if isinstance(message, dict) else None
                    )
                    tool_call_id = (
                        metadata.get("tool_call_id")
                        if isinstance(metadata, dict)
                        else None
                    )
                    if isinstance(tool_call_id, str) and tool_call_id:
                        tool_result_ids.add(tool_call_id)
        elif event.get("type") == "tool_calls":
            calls = event.get("tool_calls")
            if isinstance(calls, list):
                for call in calls:
                    call_id = call.get("id") if isinstance(call, dict) else None
                    if isinstance(call_id, str) and call_id:
                        tool_call_ids.add(call_id)
    return len(tool_call_ids), len(tool_result_ids)


def _tool_count_from_events(events: list[dict[str, Any]]) -> int:
    tool_calls_sent, tool_calls_completed = _tool_progress_from_events(events)
    return tool_calls_completed or tool_calls_sent


def _authoring_progress_is_sufficient(
    *,
    workspace: Path,
    session_id: str,
    events: list[dict[str, Any]],
    require_fast_local_harness: bool,
) -> bool:
    if not _hooks_generated(workspace):
        return False
    try:
        telemetry = _collect_authoring_telemetry(
            scenario="progress",
            workspace=workspace,
            session_id=session_id,
            events=events,
        )
    except AssertionError:
        return False
    if not telemetry.docs_read:
        return False
    if not (telemetry.syntax_check_attempted or telemetry.fast_local_test_attempted):
        return False
    if require_fast_local_harness and not (
        telemetry.fast_local_harness_generated or telemetry.fast_local_test_attempted
    ):
        return False
    return True


def _collect_authoring_telemetry(
    *,
    scenario: str,
    workspace: Path,
    session_id: str,
    events: list[dict[str, Any]],
) -> AuthoringTelemetry:
    messages = _load_session_messages(workspace, session_id)
    generated_files = _generated_cloud_agent_files(workspace)
    text = "\n".join(_telemetry_text_chunks(messages, events, generated_files))
    text_lower = text.lower()
    commands_text = "\n".join(_shell_commands([*messages, *events])).lower()
    tool_calls = Counter(_tool_call_names(messages))
    command_failure_count = sum(
        1
        for chunk in _telemetry_text_chunks(messages, events, [])
        if "exit code:" in chunk.lower() and "exit code: 0" not in chunk.lower()
    )
    fast_local_harness_generated = any(
        "test" in path.lower() and "validate-cloud" not in path.lower()
        for path in generated_files
    )
    fast_local_test_attempted = any(
        marker in commands_text
        for marker in (
            ".cloud-agent/test",
            "test-hooks-local",
            "pytest",
            "unittest",
            "bash -n",
            "python -m json.tool",
        )
    )
    return AuthoringTelemetry(
        scenario=scenario,
        tool_call_count=sum(tool_calls.values()),
        tool_calls_by_name=dict(sorted(tool_calls.items())),
        docs_read="cloud-script-authoring.md" in text_lower,
        plugin_source_read=(
            "cloud-agent-app/src" in text_lower
            or "src/cloud_agent_app" in text_lower
            or "cloud_agent_app/cloud_agent" in text_lower
        ),
        example_tests_read=(
            "test_cloud_agent_app_plugin.py" in text_lower
            or "test_cloud_validation_command_docker.py" in text_lower
        ),
        syntax_check_attempted=(
            "bash -n" in commands_text or "python -m json.tool" in commands_text
        ),
        fast_local_test_attempted=fast_local_test_attempted,
        fast_local_harness_generated=fast_local_harness_generated,
        validate_cloud_attempted="validate-cloud" in commands_text,
        command_failure_count=command_failure_count,
        generated_files=generated_files,
    )


def _assert_authoring_telemetry(
    telemetry: AuthoringTelemetry,
    budget: dict[str, int],
    *,
    require_fast_local_harness: bool = False,
) -> None:
    diagnostics = _format_authoring_telemetry(telemetry)
    assert telemetry.docs_read, diagnostics
    assert telemetry.tool_call_count <= budget["hard"], diagnostics
    if telemetry.tool_call_count > budget["soft"]:
        warnings.warn(
            f"cloud-script-author {telemetry.scenario} exceeded soft tool budget: "
            f"{telemetry.tool_call_count} > {budget['soft']}\n{diagnostics}",
            stacklevel=2,
        )
    assert (
        telemetry.syntax_check_attempted or telemetry.fast_local_test_attempted
    ), diagnostics
    if require_fast_local_harness:
        assert (
            telemetry.fast_local_harness_generated
            or telemetry.fast_local_test_attempted
        ), diagnostics


def _format_authoring_telemetry(telemetry: AuthoringTelemetry) -> str:
    return (
        f"scenario={telemetry.scenario}\n"
        f"tool_call_count={telemetry.tool_call_count}\n"
        f"tool_calls_by_name={telemetry.tool_calls_by_name}\n"
        f"docs_read={telemetry.docs_read}\n"
        f"plugin_source_read={telemetry.plugin_source_read}\n"
        f"example_tests_read={telemetry.example_tests_read}\n"
        f"syntax_check_attempted={telemetry.syntax_check_attempted}\n"
        f"fast_local_test_attempted={telemetry.fast_local_test_attempted}\n"
        f"fast_local_harness_generated={telemetry.fast_local_harness_generated}\n"
        f"validate_cloud_attempted={telemetry.validate_cloud_attempted}\n"
        f"command_failure_count={telemetry.command_failure_count}\n"
        f"generated_files={telemetry.generated_files}"
    )


def _load_session_messages(workspace: Path, session_id: str) -> list[dict[str, Any]]:
    session_path = workspace / ".crystal" / "sessions" / f"{session_id}.json"
    assert session_path.is_file(), session_path
    payload = json.loads(session_path.read_text(encoding="utf-8"))
    messages = payload.get("messages") if isinstance(payload, dict) else None
    return messages if isinstance(messages, list) else []


def _generated_cloud_agent_files(workspace: Path) -> list[str]:
    hook_dir = workspace / ".cloud-agent"
    if not hook_dir.exists():
        return []
    return sorted(
        str(path.relative_to(workspace))
        for path in hook_dir.rglob("*")
        if path.is_file()
    )


def _tool_call_names(messages: list[dict[str, Any]]) -> list[str]:
    tool_result_names: list[str] = []
    assistant_call_names: list[str] = []
    for message in messages:
        metadata = message.get("metadata")
        if isinstance(metadata, dict):
            tool_name = metadata.get("tool_name")
            if isinstance(tool_name, str) and tool_name:
                tool_result_names.append(tool_name)
        for call in message.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            function = call.get("function")
            if isinstance(function, dict):
                name = function.get("name")
                if isinstance(name, str) and name:
                    assistant_call_names.append(name)
    return tool_result_names or assistant_call_names


def _shell_commands(items: list[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for item in items:
        metadata = item.get("metadata")
        if isinstance(metadata, dict):
            display = metadata.get("display")
            if isinstance(display, dict):
                content = display.get("content")
                if isinstance(content, str):
                    commands.extend(_commands_from_display_content(content))
        messages = item.get("messages")
        if isinstance(messages, list):
            commands.extend(
                _shell_commands(
                    [message for message in messages if isinstance(message, dict)]
                )
            )
        for call in item.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            function = call.get("function")
            if not isinstance(function, dict):
                continue
            arguments = function.get("arguments")
            if isinstance(arguments, str):
                try:
                    parsed = json.loads(arguments)
                except Exception:
                    parsed = {}
                command = parsed.get("command") if isinstance(parsed, dict) else None
                if isinstance(command, str) and command:
                    commands.append(command)
    return commands


def _commands_from_display_content(content: str) -> list[str]:
    commands: list[str] = []
    for line in content.splitlines():
        if line.startswith("Command: "):
            commands.append(line[len("Command: ") :])
    return commands


def _telemetry_text_chunks(
    messages: list[dict[str, Any]],
    events: list[dict[str, Any]],
    generated_files: list[str],
) -> list[str]:
    chunks = list(generated_files)
    for item in [*messages, *events]:
        _append_text_chunks(chunks, item)
    return chunks


def _append_text_chunks(chunks: list[str], value: Any) -> None:
    if isinstance(value, str):
        chunks.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            _append_text_chunks(chunks, item)
    elif isinstance(value, list):
        for item in value:
            _append_text_chunks(chunks, item)


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
    soft_timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    if soft_timeout is not None:
        result = _run_with_soft_timeout(
            command,
            cwd=cwd,
            env=env,
            timeout=timeout,
            soft_timeout=soft_timeout,
        )
    else:
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


def _run_with_soft_timeout(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None,
    timeout: int | None,
    soft_timeout: int,
) -> subprocess.CompletedProcess[str]:
    started_at = time.monotonic()
    hard_timeout = timeout
    warned_soft_timeout = False
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as output:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            env={**os.environ, **(env or {})},
            text=True,
            stdout=output,
            stderr=subprocess.STDOUT,
        )
        while process.poll() is None:
            elapsed = time.monotonic() - started_at
            if not warned_soft_timeout and elapsed >= soft_timeout:
                warned_soft_timeout = True
                warnings.warn(
                    "command exceeded soft timeout "
                    f"{soft_timeout}s; continuing until hard timeout "
                    f"{hard_timeout}s: {' '.join(command)}",
                    stacklevel=2,
                )
            if hard_timeout is not None and elapsed >= hard_timeout:
                process.kill()
                process.wait(timeout=20)
                output.seek(0)
                stdout = output.read()
                raise AssertionError(
                    "Command exceeded hard timeout "
                    f"{hard_timeout}s: {' '.join(command)}\n{stdout}"
                )
            time.sleep(1)
        output.seek(0)
        stdout = output.read()
    return subprocess.CompletedProcess(command, process.returncode, stdout, None)
