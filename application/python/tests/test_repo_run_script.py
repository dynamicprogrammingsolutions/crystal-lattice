import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
REPO_RUN_SCRIPT = ROOT / "scripts" / "repo_run.py"
PACKAGE_JSON = ROOT / "package.json"
TASKS_JSON = ROOT / ".vscode" / "tasks.json"

REPO_RUN_PREFIX = "python scripts/repo_run.py "

WRAPPED_SCRIPTS = {
    "test:core",
    "test:core:unit",
    "test:application",
    "test:application:unit",
    "test:examples",
    "test:cli:source-install",
    "test:cli:archive",
    "test:cli:default-install",
    "test:core:integration",
    "test:application:integration",
    "test:ollama",
    "test:api:examples",
    "test:api:application",
    "test:api:openrouter",
    "test:api:openai",
    "test:api:fireworks",
    "test:api:zai",
    "test:plugins:openrouter",
    "test:plugins:openai-responses",
    "test:plugins:openai-responses:integration",
    "test:plugins:reference",
    "test:plugins:kimi",
    "test:plugins:claude",
    "test:plugins:web-fetch-shared",
    "test:plugins:tool-compat-shared",
    "test:ios:embedded-providers:bundle",
    "test:ios:embedded-providers:bundle:api",
    "test:ios:embedded-providers:detox:api",
    "test:ios:embedded-providers:detox:chatgpt",
    "lint",
    "lint:fix",
    "format",
    "typecheck",
    "docs:serve",
    "docs:build",
    "install:all",
    "install:core",
    "install:app",
    "install:plugins",
    "install:cli:dev",
    "install:cli:archive",
    "build:cli:archive",
    "build:cli:optimized",
    "release:cli",
    "release:cli:plan",
    "release:cli:gate",
    "release:cli:smoke",
    "roadmap:release:status",
    "roadmap:release:push",
    "roadmap:release:push:write",
    "roadmap:release:pull",
    "roadmap:release:pull:write",
    "roadmap:product:status",
    "roadmap:product:push",
    "roadmap:product:push:write",
    "roadmap:product:pull",
    "roadmap:product:pull:write",
}


def _load_scripts() -> dict[str, str]:
    return json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))["scripts"]


def _env_without_virtual_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}


def _run_repo_run(repo_root, *args, env=None):
    command = [sys.executable, str(REPO_RUN_SCRIPT)]
    if repo_root is not None:
        command += ["--repo-root", str(repo_root)]
    command += list(args)
    return subprocess.run(command, capture_output=True, text=True, env=env, timeout=60)


def _create_fake_venv(repo_root: Path) -> Path:
    scripts_dir = repo_root / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    scripts_dir.mkdir(parents=True)
    python_name = "python.exe" if os.name == "nt" else "python"
    (scripts_dir / python_name).touch()
    return scripts_dir


def test_repo_run_passes_through_active_venv(tmp_path):
    active_venv = tmp_path / "active-venv"
    env = _env_without_virtual_env()
    env["VIRTUAL_ENV"] = str(active_venv)

    result = _run_repo_run(
        None,
        sys.executable,
        "-c",
        "import os; print(os.environ.get('VIRTUAL_ENV'))",
        env=env,
    )

    assert result.returncode == 0
    assert str(active_venv) in result.stdout


def test_repo_run_uses_repo_venv_without_activation(tmp_path):
    scripts_dir = _create_fake_venv(tmp_path)
    env = _env_without_virtual_env()
    code = (
        "import os; "
        "print(os.environ.get('VIRTUAL_ENV')); "
        "print(os.environ['PATH'].split(os.pathsep)[0])"
    )

    result = _run_repo_run(tmp_path, sys.executable, "-c", code, env=env)

    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert lines[0] == str(tmp_path / ".venv")
    assert lines[1] == str(scripts_dir)


@pytest.mark.skipif(os.name == "nt", reason="POSIX stub executable")
def test_repo_run_resolves_tool_from_venv_scripts_dir(tmp_path):
    scripts_dir = _create_fake_venv(tmp_path)
    stub = scripts_dir / "stub-tool"
    stub.write_text(
        '#!/usr/bin/env sh\necho stub-ran "$VIRTUAL_ENV"\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)
    env = _env_without_virtual_env()

    result = _run_repo_run(tmp_path, "stub-tool", env=env)

    assert result.returncode == 0
    assert "stub-ran" in result.stdout
    assert str(tmp_path / ".venv") in result.stdout


def test_repo_run_fails_without_venv(tmp_path):
    env = _env_without_virtual_env()

    result = _run_repo_run(tmp_path, sys.executable, "-c", "print('ran')", env=env)

    assert result.returncode != 0
    assert "install:venv" in result.stderr
    assert "ran" not in result.stdout


def test_repo_run_reports_incomplete_venv(tmp_path):
    (tmp_path / ".venv").mkdir()
    env = _env_without_virtual_env()

    result = _run_repo_run(tmp_path, sys.executable, "-c", "print('ran')", env=env)

    assert result.returncode != 0
    assert "missing a Python executable" in result.stderr
    assert "install:venv" in result.stderr


def test_repo_run_reports_missing_command(tmp_path):
    _create_fake_venv(tmp_path)
    env = _env_without_virtual_env()

    result = _run_repo_run(tmp_path, "definitely-missing-tool-xyz", env=env)

    assert result.returncode == 127
    assert "command not found" in result.stderr


def test_python_tooling_scripts_run_through_repo_run():
    scripts = _load_scripts()

    for name in WRAPPED_SCRIPTS:
        assert "repo_run.py" in scripts[name], name

    using_repo_run = {
        name for name, command in scripts.items() if "repo_run.py" in command
    }
    assert using_repo_run == WRAPPED_SCRIPTS

    # Most wrapped scripts invoke the wrapper directly; the docs scripts cd into
    # docs_site first and reference the wrapper relative to that directory.
    directly_wrapped = WRAPPED_SCRIPTS - {"docs:serve", "docs:build"}
    for name in directly_wrapped:
        assert scripts[name].startswith(REPO_RUN_PREFIX), name

    assert (
        scripts["docs:serve"]
        == "cd docs_site && python ../scripts/repo_run.py mkdocs serve"
    )
    assert (
        scripts["docs:build"]
        == "cd docs_site && python ../scripts/repo_run.py mkdocs build"
    )


def test_ios_embedded_provider_bundle_build_targets_mobile_prepare():
    scripts = _load_scripts()

    assert scripts["build:ios:embedded-providers:bundle"] == (
        "npm --prefix mobile/crystal-lattice-control-rn run ios:prepare-python"
    )


def test_server_scripts_run_installed_commands_without_repo_run():
    scripts = _load_scripts()

    assert (
        scripts["server"]
        == "crystal-lattice --server --console --enable-bonjour --enable-bridge"
    )
    assert scripts["server:basic"] == "crystal-lattice --server --console"
    assert scripts["server:echo"] == "crystal-lattice --server --console --config-local"
    assert (
        scripts["server:dev"]
        == "crystal-lattice-cli-dev --console --server --enable-bridge --enable-bonjour --port 57889"
    )
    assert scripts["server:cloud-test"] == "bash .crystal/cloud-test.sh"
    assert "run:dev-local" not in scripts


def test_cli_distribution_scripts_use_the_isolated_runner():
    scripts = _load_scripts()

    assert (
        scripts["test:cli:source-install"] == "python scripts/repo_run.py python "
        "application/python/scripts/run_distribution_smoke.py source-install"
    )
    assert (
        scripts["test:cli:archive"] == "python scripts/repo_run.py python "
        "application/python/scripts/run_distribution_smoke.py archive"
    )
    assert (
        scripts["test:cli:default-install"] == "python scripts/repo_run.py python "
        "application/python/scripts/run_distribution_smoke.py default-install"
    )


def test_cli_build_and_install_scripts_are_scoped_and_do_not_use_nox():
    scripts = _load_scripts()

    assert scripts["build:cli:archive"] == (
        "python scripts/repo_run.py python "
        "application/python/scripts/build_runtime_archive.py"
    )
    assert scripts["build:cli:optimized"] == (
        "python scripts/repo_run.py python "
        "application/python/scripts/build_optimized_archive.py"
    )
    assert scripts["install:cli:archive"] == (
        "python scripts/repo_run.py python "
        "application/python/scripts/install_current_archive.py"
    )
    assert scripts["install:cli:dev"] == (
        "python scripts/repo_run.py python application/python/scripts/install_dev.py"
    )
    assert {
        "build:bundle",
        "build:optimized",
        "install:prod:local",
        "install:dev:local",
    }.isdisjoint(scripts)
    assert all("nox" not in command for command in scripts.values())


def test_release_scripts_run_local_gate_through_repo_run():
    scripts = _load_scripts()

    assert (
        scripts["release:cli"]
        == "python scripts/repo_run.py bash deploy/aws-cli-downloads/release.sh"
        " --profile prod --push-tag --watch"
    )
    assert (
        scripts["release:cli:plan"]
        == "python scripts/repo_run.py bash deploy/aws-cli-downloads/release.sh"
        " --profile prod --dry-run"
    )
    assert (
        scripts["release:cli:gate"]
        == "python scripts/repo_run.py bash deploy/aws-cli-downloads/release.sh"
        " --profile prod"
    )
    assert (
        scripts["release:cli:smoke"]
        == "python scripts/repo_run.py bash deploy/aws-cli-downloads/smoke.sh"
        " --profile prod"
    )


def test_plugin_suite_scripts_run_through_repo_run():
    scripts = _load_scripts()

    assert (
        scripts["test:plugins:kimi"]
        == "python scripts/repo_run.py pytest plugins/kimi-tools/tests -q"
    )
    assert (
        scripts["test:plugins:claude"]
        == "python scripts/repo_run.py pytest plugins/claude-tools/tests -q"
    )
    assert (
        scripts["test:plugins:web-fetch-shared"]
        == "python scripts/repo_run.py pytest plugins/web-fetch-shared/tests -q"
    )
    assert (
        scripts["test:plugins:tool-compat-shared"]
        == "python scripts/repo_run.py pytest plugins/tool-compat-shared/tests -q"
    )
    assert (
        scripts["test:plugins:openai-responses:integration"]
        == "python scripts/repo_run.py pytest plugins/openai_responses/tests"
        ' -m "integration and not api and not slow_integration'
        ' and not manual_integration" -q'
    )
    assert (
        scripts["install:plugins"] == "python scripts/repo_run.py python -m pip install"
        ' -e "plugins/kimi-tools[dev]" -e "plugins/claude-tools[dev]"'
        " && python scripts/repo_run.py python -m pip install"
        ' -e "plugins/tool-compat-shared[dev]" -e "plugins/web-fetch-shared[dev]"'
        ' -e "plugins/openai_responses[dev]"'
    )


def test_environment_independent_scripts_stay_unwrapped():
    scripts = _load_scripts()

    assert scripts["install:venv"] == "python -m venv .venv"
    assert scripts["docs:examples"] == "python scripts/generate_examples_md.py"
    assert (
        scripts["release:cli:version:bump-patch"]
        == "python application/python/scripts/bump_version.py"
    )
    assert scripts["roadmap:release:generate"] == "python roadmaps/generate.py release"
    assert (
        scripts["roadmap:release:check"]
        == "python roadmaps/generate.py --check release"
    )
    assert (
        scripts["roadmap:release:test"]
        == "python -m unittest discover -s roadmaps/tests -p 'test_*.py'"
    )


def test_vscode_tasks_reference_valid_scripts():
    tasks = json.loads(TASKS_JSON.read_text(encoding="utf-8"))["tasks"]
    scripts = _load_scripts()

    labels = [task["label"] for task in tasks]
    assert len(labels) == len(set(labels))

    for task in tasks:
        assert task["type"] == "npm", task["label"]
        assert task["script"] in scripts, task["label"]

    dev_server_tasks = [task for task in tasks if task["script"] == "server:dev"]
    assert len(dev_server_tasks) == 1
    assert dev_server_tasks[0]["label"] == "Server: Dev"
