#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

REPO="dynamicprogrammingsolutions/crystal-lattice"
VERSION=""
PUSH_TAG=0
WATCH=0
DRY_RUN=0
ALLOW_DIRTY=0
SKIP_TESTS=0
WORKFLOW_NAME="release-crystal-lattice-cli.yml"
RUN_DISCOVERY_ATTEMPTS="${CLI_RELEASE_RUN_DISCOVERY_ATTEMPTS:-24}"
RUN_DISCOVERY_INTERVAL_SECONDS="${CLI_RELEASE_RUN_DISCOVERY_INTERVAL_SECONDS:-5}"

usage() {
  cat <<'USAGE'
Orchestrate a Crystal Lattice CLI release through GitHub Actions.

This script validates local release state, optionally creates/pushes the release
tag, watches the GitHub matrix workflow, and prints or runs download smoke tests.
It does not build the official platform artifacts locally.

Usage:
  deploy/aws-cli-downloads/release.sh [common options] [options]

Options:
  --repo OWNER/REPO            GitHub repository. Default: dynamicprogrammingsolutions/crystal-lattice.
  --version VERSION            Version without tag prefix. Defaults to pyproject version.
  --push-tag                   Create and push crystal-lattice-cli-v<VERSION>.
  --watch                      Watch the GitHub Actions run after pushing the tag.
  --allow-dirty                Allow a dirty git worktree.
  --skip-tests                 Skip local fast tests.
  --dry-run                    Print commands without mutating git/GitHub.
  --help, -h                   Show this help.
USAGE
  usage_common
}

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --push-tag) PUSH_TAG=1; shift ;;
    --watch) WATCH=1; shift ;;
    --allow-dirty) ALLOW_DIRTY=1; shift ;;
    --skip-tests) SKIP_TESTS=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) args+=("$1"); shift ;;
  esac
done

if [ "${#args[@]}" -gt 0 ]; then
  parse_common_args "${args[@]}"
else
  parse_common_args
fi
cd "$REPO_ROOT"

project_version="$(read_project_version)"
VERSION="${VERSION:-$project_version}"
if [ "$VERSION" != "$project_version" ]; then
  echo "Requested version $VERSION does not match application/python/pyproject.toml version $project_version" >&2
  exit 1
fi

tag="$(normalize_version_tag "$VERSION")"

if [ "$ALLOW_DIRTY" -ne 1 ] && [ -n "$(git status --porcelain)" ]; then
  echo "Git worktree is dirty. Commit/stash changes or pass --allow-dirty." >&2
  exit 1
fi

if git rev-parse "$tag" >/dev/null 2>&1; then
  echo "Tag already exists locally: $tag" >&2
  exit 1
fi

if git ls-remote --exit-code --tags origin "$tag" >/dev/null 2>&1; then
  echo "Tag already exists on origin: $tag" >&2
  exit 1
fi

run_or_print() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

read_github_variable() {
  local name="$1"
  gh variable list \
    --repo "$REPO" \
    --json name,value \
    --jq ".[] | select(.name == \"$name\") | .value" |
    head -n 1
}

validate_github_download_config() {
  if ! stack_exists; then
    echo "Download stack does not exist for profile $PROFILE: $STACK_NAME" >&2
    exit 1
  fi

  local expected_region expected_bucket expected_prefix expected_base_url
  local expected_distribution secret_name
  expected_region="$REGION"
  expected_bucket="$(stack_output DownloadsBucket)"
  expected_prefix="$(stack_output DownloadsPrefix)"
  expected_base_url="$(stack_output DownloadsBaseUrl)"
  expected_distribution="$(stack_output DownloadsCloudFrontDistributionId)"

  local mismatches=0
  local name expected actual
  while IFS='|' read -r name expected; do
    actual="$(read_github_variable "$name")"
    if [ "$actual" != "$expected" ]; then
      echo "GitHub variable $name does not match profile $PROFILE." >&2
      echo "  expected: $expected" >&2
      echo "  actual:   ${actual:-<unset>}" >&2
      mismatches=1
    fi
  done <<EOF
AWS_REGION|$expected_region
CLI_DOWNLOADS_BUCKET|$expected_bucket
CLI_DOWNLOADS_PREFIX|$expected_prefix
CLI_DOWNLOADS_BASE_URL|$expected_base_url
CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID|$expected_distribution
EOF

  [ "$mismatches" -eq 0 ] || {
    echo "Run configure-github-actions-vars.sh for profile $PROFILE before releasing." >&2
    exit 1
  }

  secret_name="$(
    gh secret list \
      --repo "$REPO" \
      --json name \
      --jq '.[] | select(.name == "CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME") | .name' |
      head -n 1
  )"
  if [ "$secret_name" != "CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME" ]; then
    echo "GitHub secret CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME is not configured." >&2
    exit 1
  fi
}

validate_release_commit() {
  local branch release_sha remote_main_sha
  branch="$(git branch --show-current)"
  if [ "$branch" != "main" ]; then
    echo "Release tags must be created from main; current branch is ${branch:-<detached>}." >&2
    exit 1
  fi

  release_sha="$(git rev-parse HEAD)"
  remote_main_sha="$(
    git ls-remote origin refs/heads/main |
      awk 'NR == 1 {print $1}'
  )"
  if [ -z "$remote_main_sha" ]; then
    echo "Could not resolve origin/main." >&2
    exit 1
  fi
  if [ "$release_sha" != "$remote_main_sha" ]; then
    echo "Release commit must exactly match origin/main." >&2
    echo "  local HEAD:  $release_sha" >&2
    echo "  origin/main: $remote_main_sha" >&2
    exit 1
  fi
  printf '%s\n' "$release_sha"
}

find_release_run_id() {
  local release_sha="$1"
  local attempt run_id
  attempt=1
  while [ "$attempt" -le "$RUN_DISCOVERY_ATTEMPTS" ]; do
    run_id="$(
      gh run list \
        --repo "$REPO" \
        --workflow "$WORKFLOW_NAME" \
        --event push \
        --commit "$release_sha" \
        --limit 10 \
        --json databaseId,headBranch \
        --jq ".[] | select(.headBranch == \"$tag\") | .databaseId" |
        head -n 1
    )"
    if [ -n "$run_id" ]; then
      printf '%s\n' "$run_id"
      return 0
    fi
    sleep "$RUN_DISCOVERY_INTERVAL_SECONDS"
    attempt=$((attempt + 1))
  done
  echo "Timed out waiting for the tag-triggered release workflow for $tag ($release_sha)." >&2
  return 1
}

release_sha="$(validate_release_commit)"
validate_github_download_config

if [ "$SKIP_TESTS" -eq 0 ]; then
  run_or_print python -m pip install -e "core/python[dev]" -e application/python -e "plugins/openai_responses[dev]"
  run_or_print pytest core/python/tests -q -m "not integration"
  run_or_print pytest application/python/tests -q -m "not integration and not docker"
fi

echo "Release tag: $tag"
echo "Download profile: $PROFILE"
if stack_exists; then
  echo "Download base URL: $(downloads_base_url)"
else
  echo "Download stack not found locally: $STACK_NAME"
fi

if [ "$PUSH_TAG" -eq 1 ]; then
  run_or_print git tag "$tag" "$release_sha"
  run_or_print git push origin "$tag"
else
  echo "Tag not pushed. Pass --push-tag to create and push $tag."
fi

if [ "$WATCH" -eq 1 ]; then
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRY RUN: discover tag-triggered run for $tag at $release_sha"
    echo "DRY RUN: gh run watch <run-id> --repo $REPO --exit-status"
    echo "DRY RUN: gh release view $tag --repo $REPO --json url --jq .url"
  else
    echo "Waiting for GitHub Actions to register the release workflow..."
    run_id="$(find_release_run_id "$release_sha")"
    echo "Release workflow run ID: $run_id"
    gh run watch "$run_id" --repo "$REPO" --exit-status
    release_url="$(
      gh release view "$tag" --repo "$REPO" --json url --jq '.url'
    )"
    echo "GitHub Release: $release_url"
  fi
fi

echo "After the workflow publishes, run:"
printf '  %q %q %q %q %q\n' "$SCRIPT_DIR/smoke.sh" --profile "$PROFILE" --version "$VERSION"