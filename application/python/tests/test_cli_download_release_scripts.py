import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RELEASE_SCRIPT = ROOT / "deploy" / "aws-cli-downloads" / "release.sh"
PROMOTE_SCRIPT = (
    ROOT / "deploy" / "aws-cli-downloads" / "promote-github-release.sh"
)
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release-crystal-lattice-cli.yml"
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
    return {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
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


def test_release_workflow_uses_draft_release_instead_of_actions_artifacts() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "actions/upload-artifact" not in workflow
    assert "actions/download-artifact" not in workflow
    assert "gh release create" in workflow
    assert "gh release upload" in workflow
    assert "gh release edit" in workflow
    assert "gh release download" in workflow