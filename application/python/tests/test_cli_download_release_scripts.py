import json
import os
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RELEASE_SCRIPT = ROOT / "deploy" / "aws-cli-downloads" / "release.sh"
PROMOTE_SCRIPT = ROOT / "deploy" / "aws-cli-downloads" / "promote-github-release.sh"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release-crystal-lattice-cli.yml"
PUBLIC_CI_WORKFLOW = ROOT / ".github" / "workflows" / "public-ci.yml"
OIDC_TEMPLATE = ROOT / "deploy" / "aws-cli-downloads" / "github-oidc-role.yaml"
CONFIGURE_GITHUB_SCRIPT = (
    ROOT / "deploy" / "aws-cli-downloads" / "configure-github-actions-vars.sh"
)
BUMP_SCRIPT = ROOT / "scripts" / "bump_cli_version.py"
PACKAGE_JSON = ROOT / "package.json"
RELEASE_SHA = "a" * 40


def _write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_test_repo(tmp_path: Path, version: str = "9.8.7") -> Path:
    repo = tmp_path / "repo"
    pyproject = repo / "application" / "python" / "pyproject.toml"
    pyproject.parent.mkdir(parents=True)
    pyproject.write_text(
        f'[project]\nname = "crystal-lattice-cli"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    return repo


def _write_fake_release_commands(tmp_path: Path) -> tuple[Path, Path]:
    fake_bin = tmp_path / "fake-bin"
    command_log = tmp_path / "commands.log"
    fake_bin.mkdir()

    _write_executable(
        fake_bin / "git",
        f"""#!/usr/bin/env sh
printf 'git %s\\n' "$*" >> "{command_log}"
case "$1:$2" in
  status:--porcelain)
    [ "${{FAKE_GIT_DIRTY:-0}}" = "1" ] && printf '%s\\n' ' M dirty.txt'
    ;;
  branch:--show-current)
    printf '%s\\n' "${{FAKE_GIT_BRANCH:-main}}"
    ;;
  rev-parse:HEAD)
    printf '%s\\n' "{RELEASE_SHA}"
    ;;
  rev-parse:*)
    if [ "${{FAKE_LOCAL_TAG_EXISTS:-0}}" = "1" ]; then
      printf '%s\\n' "{RELEASE_SHA}"
    else
      exit 1
    fi
    ;;
  ls-remote:origin)
    printf '%s\\t%s\\n' "{RELEASE_SHA}" 'refs/heads/main'
    ;;
  ls-remote:*)
    if [ "${{FAKE_REMOTE_TAG_EXISTS:-0}}" = "1" ]; then
      printf '%s\\t%s\\n' "{RELEASE_SHA}" 'refs/tags/crystal-lattice-cli-v9.8.7'
    else
      exit 2
    fi
    ;;
  tag:*|push:*)
    ;;
  *)
    exit 1
    ;;
esac
""",
    )

    _write_executable(
        fake_bin / "aws",
        f"""#!/usr/bin/env sh
printf 'aws %s\\n' "$*" >> "{command_log}"
case "$*" in
  *"OutputKey=='DownloadsBucket'"*)
    printf '%s\\n' 'crystal-lattice-cli-downloads-test-874087778966'
    ;;
  *"OutputKey=='DownloadsPrefix'"*)
    printf '%s\\n' 'crystal-lattice-cli'
    ;;
  *"OutputKey=='DownloadsBaseUrl'"*)
    printf '%s\\n' 'https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli'
    ;;
  *"OutputKey=='DownloadsCloudFrontDistributionId'"*)
    printf '%s\\n' 'E2SBEYDBKC4Y7A'
    ;;
  *)
    printf '%s\\n' '{{}}'
    ;;
esac
""",
    )

    _write_executable(
        fake_bin / "gh",
        f"""#!/usr/bin/env sh
printf 'gh %s\\n' "$*" >> "{command_log}"
case "$1:$2" in
  variable:list)
    case "$*" in
      *AWS_REGION*) printf '%s\\n' 'us-east-1' ;;
      *CLI_DOWNLOADS_BUCKET*)
        if [ "${{FAKE_GH_PROFILE:-test}}" = "test" ]; then
          printf '%s\\n' 'crystal-lattice-cli-downloads-test-874087778966'
        else
          printf '%s\\n' 'crystal-lattice-cli-downloads-prod-874087778966'
        fi
        ;;
      *CLI_DOWNLOADS_PREFIX*) printf '%s\\n' 'crystal-lattice-cli' ;;
      *CLI_DOWNLOADS_BASE_URL*)
        if [ "${{FAKE_GH_PROFILE:-test}}" = "test" ]; then
          printf '%s\\n' 'https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli'
        else
          printf '%s\\n' 'https://download.crystallattice.dev/crystal-lattice-cli'
        fi
        ;;
      *CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID*)
        if [ "${{FAKE_GH_PROFILE:-test}}" = "test" ]; then
          printf '%s\\n' 'E2SBEYDBKC4Y7A'
        else
          printf '%s\\n' 'EJ5QPW5TUT5U9'
        fi
        ;;
    esac
    ;;
  secret:list)
    if [ "${{FAKE_GH_SECRET:-present}}" = "present" ]; then
      printf '%s\\n' 'CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME'
    fi
    ;;
  run:list)
    printf '%s\\n' '4242'
    ;;
  run:watch)
    [ "$3" = "4242" ] || exit 9
    if [ "${{FAKE_GH_WATCH_FAILURE:-0}}" = "1" ]; then
      exit 8
    fi
    ;;
  release:view)
    printf '%s\\n' 'https://github.example/releases/9.8.7'
    ;;
  *)
    exit 1
    ;;
esac
""",
    )
    return fake_bin, command_log


def _release_env(tmp_path: Path, *, github_profile: str = "test") -> dict[str, str]:
    repo = _write_test_repo(tmp_path)
    fake_bin, command_log = _write_fake_release_commands(tmp_path)
    # release.sh resolves ``python`` through PATH (read_project_version), so pin
    # the test runner's real interpreter directory first. Without this, pyenv
    # shim users fail with "pyenv: python: command not found" because the script
    # runs from a temporary cwd outside any .python-version scope.
    runner_bin = Path(sys.executable).parent
    return {
        **os.environ,
        "PATH": f"{runner_bin}{os.pathsep}{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "REPO_ROOT": str(repo),
        "FAKE_GH_PROFILE": github_profile,
        "COMMAND_LOG": str(command_log),
        "CLI_RELEASE_RUN_DISCOVERY_ATTEMPTS": "1",
        "CLI_RELEASE_RUN_DISCOVERY_INTERVAL_SECONDS": "0",
    }


def test_release_script_dry_run_prints_tag_and_watch_commands(tmp_path: Path) -> None:
    env = _release_env(tmp_path)

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--push-tag",
            "--watch",
            "--dry-run",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "[1/6] Resolving release version" in result.stdout
    assert "version=9.8.7 tag=crystal-lattice-cli-v9.8.7" in result.stdout
    assert "[6/6] Watching GitHub Actions release workflow" in result.stdout
    assert "tag pushed;" not in result.stdout
    assert f"git tag crystal-lattice-cli-v9.8.7 {RELEASE_SHA}" in result.stdout
    assert "gh run watch <run-id>" in result.stdout
    assert "gh release view crystal-lattice-cli-v9.8.7" in result.stdout


def test_release_script_rejects_profile_variable_mismatch(tmp_path: Path) -> None:
    env = _release_env(tmp_path, github_profile="prod")

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--dry-run",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "does not match profile test" in result.stderr
    assert "configure-github-actions-vars.sh" in result.stderr


def test_release_script_rejects_dirty_worktree(tmp_path: Path) -> None:
    env = {**_release_env(tmp_path), "FAKE_GIT_DIRTY": "1"}

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--dry-run",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Git worktree is dirty" in result.stderr


def test_release_script_rejects_missing_oidc_secret(tmp_path: Path) -> None:
    env = {**_release_env(tmp_path), "FAKE_GH_SECRET": "missing"}

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--dry-run",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME is not configured" in result.stderr


def test_release_script_rejects_existing_local_tag(tmp_path: Path) -> None:
    env = {**_release_env(tmp_path), "FAKE_LOCAL_TAG_EXISTS": "1"}

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--dry-run",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Tag already exists locally" in result.stderr


def test_release_script_rejects_existing_remote_tag(tmp_path: Path) -> None:
    env = {**_release_env(tmp_path), "FAKE_REMOTE_TAG_EXISTS": "1"}

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--dry-run",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Tag already exists on origin" in result.stderr


def test_release_script_watches_discovered_run_and_prints_release_url(
    tmp_path: Path,
) -> None:
    env = _release_env(tmp_path)
    command_log = Path(env["COMMAND_LOG"])

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--push-tag",
            "--watch",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Release workflow run ID: 4242" in result.stdout
    assert "GitHub Release: https://github.example/releases/9.8.7" in result.stdout
    commands = command_log.read_text(encoding="utf-8")
    assert "gh run watch 4242" in commands
    assert "--exit-status" in commands
    assert f"git tag crystal-lattice-cli-v9.8.7 {RELEASE_SHA}" in commands
    assert "git push origin crystal-lattice-cli-v9.8.7" in commands


def test_release_script_prints_step_progress(tmp_path: Path) -> None:
    env = _release_env(tmp_path)

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--push-tag",
            "--watch",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    stdout = result.stdout
    assert "[1/6] Resolving release version" in stdout
    assert "version=9.8.7 tag=crystal-lattice-cli-v9.8.7" in stdout
    assert "[2/6] Checking git release state" in stdout
    assert "worktree clean" in stdout
    assert (
        "tag crystal-lattice-cli-v9.8.7 is new (not present locally or on origin)"
        in stdout
    )
    assert "[3/6] Validating release commit" in stdout
    assert f"HEAD {RELEASE_SHA} matches origin/main" in stdout
    assert "[4/6] Validating GitHub download configuration (profile test)" in stdout
    assert "stack crystal-lattice-cli-downloads-test: found" in stdout
    assert "AWS_REGION: ok" in stdout
    assert "CLI_DOWNLOADS_BUCKET: ok" in stdout
    assert "secret CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME: present" in stdout
    assert "download base URL: " in stdout
    assert "[5/6] Creating and pushing release tag" in stdout
    assert f"$ git tag crystal-lattice-cli-v9.8.7 {RELEASE_SHA}" in stdout
    assert "$ git push origin crystal-lattice-cli-v9.8.7" in stdout
    assert "tag pushed; release-crystal-lattice-cli.yml workflow triggered" in stdout
    assert "[6/6] Watching GitHub Actions release workflow" in stdout
    assert "Next step: verify the download endpoint" in stdout
    # Run discovery heartbeats go to stderr because stdout is captured.
    assert "waiting for the tag-triggered run to appear (attempt 1/1)" in result.stderr


def test_release_script_propagates_watched_run_failure(tmp_path: Path) -> None:
    env = {**_release_env(tmp_path), "FAKE_GH_WATCH_FAILURE": "1"}

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
            "--push-tag",
            "--watch",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 8
    assert "Release workflow run ID: 4242" in result.stdout
    assert "GitHub Release:" not in result.stdout


def test_release_script_without_push_tag_validates_and_skips_tag(
    tmp_path: Path,
) -> None:
    """Gate mode: full validation without creating or pushing the tag.

    This is the mode behind ``npm run release:cli:gate``. ``--skip-tests``
    keeps the test fast; the local gate's real execution path is the same
    ``run_or_print`` branch the push-tag tests exercise.
    """
    env = _release_env(tmp_path)
    command_log = Path(env["COMMAND_LOG"])

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--skip-tests",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    stdout = result.stdout
    assert "[4/4] Validating GitHub download configuration (profile test)" in stdout
    assert "secret CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME: present" in stdout
    assert (
        "Tag not pushed. Pass --push-tag to create and push crystal-lattice-cli-v9.8.7."
        in stdout
    )
    # Nothing was triggered, so the post-publish smoke hint must not print.
    assert "Next step: verify the download endpoint" not in stdout
    commands = command_log.read_text(encoding="utf-8")
    assert "git tag crystal-lattice-cli-v9.8.7" not in commands
    assert "git push origin crystal-lattice-cli-v9.8.7" not in commands


def test_promote_script_dry_run_does_not_require_downloaded_assets(
    tmp_path: Path,
) -> None:
    repo = _write_test_repo(tmp_path)
    assets_dir = tmp_path / "assets"
    env = {**os.environ, "REPO_ROOT": str(repo)}

    result = subprocess.run(
        [
            "bash",
            str(PROMOTE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--keep-assets-dir",
            str(assets_dir),
            "--dry-run",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "gh release download crystal-lattice-cli-v9.8.7" in result.stdout
    assert "publish-assets.sh" in result.stdout
    assert "Promotion dry run completed" in result.stdout
    assert not list(assets_dir.iterdir())


def test_release_workflow_uses_single_writer_artifact_handoff() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "prepare-release:" not in workflow
    assert (
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    )
    assert (
        "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in workflow
    )
    assert "retention-days: 1" in workflow
    assert "compression-level: 0" in workflow
    assert workflow.count("contents: write") == 1
    assert "gh release create" in workflow
    assert "gh release upload" in workflow
    assert "gh release edit" in workflow
    assert "gh release download" in workflow
    assert workflow.count("environment: cli-release") == 2
    assert workflow.index("actions/download-artifact") < workflow.index(
        "gh release upload"
    )


def test_release_script_install_line_avoids_plugin_packages(tmp_path: Path) -> None:
    env = _release_env(tmp_path)

    result = subprocess.run(
        [
            "bash",
            str(RELEASE_SCRIPT),
            "--profile",
            "test",
            "--version",
            "9.8.7",
            "--dry-run",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    install_lines = [
        line for line in result.stdout.splitlines() if "pip install" in line
    ]
    assert install_lines == [
        "DRY RUN: python -m pip install -e core/python\\[dev\\] "
        "-e application/python openai"
    ]


def test_release_workflows_install_only_core_application_and_openai() -> None:
    release_workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    public_ci_workflow = PUBLIC_CI_WORKFLOW.read_text(encoding="utf-8")

    for workflow in (release_workflow, public_ci_workflow):
        assert '-e "plugins/openai_responses[dev]"' not in workflow
        assert "plugins/tool-compat-shared" not in workflow
        assert "plugins/mcp-shared" not in workflow
        assert "plugins/web-fetch-shared" not in workflow
        assert "-e application/python" in workflow
        assert "openai" in workflow


def test_release_oidc_configuration_restricts_environment_to_release_tags() -> None:
    template = OIDC_TEMPLATE.read_text(encoding="utf-8")
    configure_script = CONFIGURE_GITHUB_SCRIPT.read_text(encoding="utf-8")

    assert "environment:${GitHubEnvironment}" in template
    assert 'GITHUB_ENVIRONMENT="cli-release"' in configure_script
    assert 'GITHUB_TAG_PATTERN="crystal-lattice-cli-v*"' in configure_script
    assert '"tag|$GITHUB_TAG_PATTERN"' in configure_script


def _write_bump_repo(tmp_path: Path, version: str = "9.8.7") -> Path:
    repo = tmp_path / "bump-repo"
    pyproject = repo / "application" / "python" / "pyproject.toml"
    pyproject.parent.mkdir(parents=True)
    pyproject.write_text(
        f'[project]\nname = "crystal-lattice-cli"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    # The core status line deliberately shares the CLI version string so the
    # agent-core line guard is exercised on every bump.
    (repo / "README.md").write_text(
        f"- Core package: `agent-core` {version}\n"
        f"- Terminal CLI package: `crystal-lattice-cli` {version} "
        "(`crystal-lattice` command)\n",
        encoding="utf-8",
    )
    app_readme = repo / "application" / "python" / "README.md"
    app_readme.write_text(
        f"curl -fsSL https://example.invalid/install.sh | VERSION={version} bash\n"
        f"crystal-lattice-python-runtime-v{version}-darwin-arm64.tar.gz\n"
        f"crystal-lattice-python-runtime-v{version}0-linux-amd64.tar.gz\n"
        f"v1{version}-unrelated.tar.gz\n",
        encoding="utf-8",
    )
    deploy_readme = repo / "deploy" / "aws-cli-downloads" / "README.md"
    deploy_readme.parent.mkdir(parents=True, exist_ok=True)
    deploy_readme.write_text(
        f"deploy/aws-cli-downloads/release.sh --version {version}\n",
        encoding="utf-8",
    )
    return repo


def _run_bump_script(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUMP_SCRIPT), "--repo-root", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_bump_script_updates_pyproject_and_doc_references(tmp_path: Path) -> None:
    repo = _write_bump_repo(tmp_path)

    result = _run_bump_script(repo)

    assert result.returncode == 0, result.stderr
    assert "9.8.7 -> 9.8.8" in result.stdout
    pyproject = (repo / "application" / "python" / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'version = "9.8.8"' in pyproject

    root_readme = (repo / "README.md").read_text(encoding="utf-8")
    assert "- Terminal CLI package: `crystal-lattice-cli` 9.8.8" in root_readme
    # The independent agent-core version line is never rewritten.
    assert "- Core package: `agent-core` 9.8.7" in root_readme

    app_readme = (repo / "application" / "python" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "VERSION=9.8.8 bash" in app_readme
    assert "crystal-lattice-python-runtime-v9.8.8-darwin-arm64.tar.gz" in app_readme
    # Digit-guarded neighbors stay untouched.
    assert "crystal-lattice-python-runtime-v9.8.70-linux-amd64.tar.gz" in app_readme
    assert "v19.8.7-unrelated.tar.gz" in app_readme

    deploy_readme = (repo / "deploy" / "aws-cli-downloads" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "--version 9.8.8" in deploy_readme


def test_bump_script_supports_minor_and_major_segments(tmp_path: Path) -> None:
    repo = _write_bump_repo(tmp_path)

    minor = _run_bump_script(repo, "--bump", "minor")
    assert minor.returncode == 0, minor.stderr
    assert "9.8.7 -> 9.9.0" in minor.stdout

    major = _run_bump_script(repo, "--bump", "major")
    assert major.returncode == 0, major.stderr
    assert "9.9.0 -> 10.0.0" in major.stdout
    pyproject = (repo / "application" / "python" / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'version = "10.0.0"' in pyproject


def test_bump_script_rejects_missing_version_line(tmp_path: Path) -> None:
    repo = tmp_path / "empty-repo"
    pyproject = repo / "application" / "python" / "pyproject.toml"
    pyproject.parent.mkdir(parents=True)
    pyproject.write_text('[project]\nname = "crystal-lattice-cli"\n', encoding="utf-8")

    result = _run_bump_script(repo)

    assert result.returncode != 0
    assert "found 0" in result.stderr


def test_root_package_json_exposes_cli_release_scripts() -> None:
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    scripts = package["scripts"]

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
    assert (
        scripts["release:cli:version:bump-patch"]
        == "python scripts/bump_cli_version.py"
    )
