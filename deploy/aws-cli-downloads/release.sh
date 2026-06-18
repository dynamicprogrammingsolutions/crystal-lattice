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
  run_or_print git tag "$tag"
  run_or_print git push origin "$tag"
else
  echo "Tag not pushed. Pass --push-tag to create and push $tag."
fi

if [ "$WATCH" -eq 1 ]; then
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRY RUN: gh run list --repo $REPO --workflow release-crystal-lattice-cli.yml --limit 5"
    echo "DRY RUN: gh run watch --repo $REPO"
  else
    echo "Waiting briefly for GitHub Actions to register the release workflow..."
    sleep 10
    gh run list --repo "$REPO" --workflow release-crystal-lattice-cli.yml --limit 5
    gh run watch --repo "$REPO"
  fi
fi

echo "After the workflow publishes, run:"
printf '  %q %q %q %q %q\n' "$SCRIPT_DIR/smoke.sh" --profile "$PROFILE" --version "$VERSION"