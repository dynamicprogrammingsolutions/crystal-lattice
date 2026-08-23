#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

REPO="dynamicprogrammingsolutions/crystal-lattice"
VERSION=""
DRY_RUN=0
KEEP_ASSETS_DIR=""

usage() {
  cat <<'USAGE'
Promote existing GitHub Release assets to a CLI download stack.

Usage:
  ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh [common options] [options]

Options:
  --repo OWNER/REPO            GitHub repository. Default: dynamicprogrammingsolutions/crystal-lattice.
  --version VERSION            Version without tag prefix. Defaults to pyproject version.
  --keep-assets-dir DIR        Keep downloaded assets in DIR.
  --dry-run                    Print commands without mutating AWS.
  --help, -h                   Show this help.
USAGE
  usage_common
}

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --keep-assets-dir) KEEP_ASSETS_DIR="$2"; shift 2 ;;
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
if [ "$DRY_RUN" -eq 0 ]; then
  require_aws_deploy_enabled
fi

VERSION="${VERSION:-$(cd "$REPO_ROOT" && read_project_version)}"
tag="$(normalize_version_tag "$VERSION")"
work_dir="${KEEP_ASSETS_DIR:-$(mktemp -d)}"
mkdir -p "$work_dir"
if [ -z "$KEEP_ASSETS_DIR" ]; then
  trap 'rm -rf "$work_dir"' EXIT
fi

if [ "$DRY_RUN" -eq 1 ]; then
  printf 'DRY RUN:'
  printf ' %q' gh release download "$tag" --repo "$REPO" --dir "$work_dir" --pattern "crystal-lattice-python-runtime-v${VERSION}-*"
  printf '\n'
  printf 'DRY RUN: ALLOW_AWS_DEPLOY=1'
  printf ' %q' "$SCRIPT_DIR/publish-assets.sh" \
    --profile "$PROFILE" \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --assets-dir "$work_dir" \
    --version "$VERSION"
  printf '\n'
  echo "Promotion dry run completed for $tag to profile $PROFILE."
  exit 0
fi

gh release download "$tag" --repo "$REPO" --dir "$work_dir" --pattern "crystal-lattice-python-runtime-v${VERSION}-*"

ALLOW_AWS_DEPLOY=1 "$SCRIPT_DIR/publish-assets.sh" \
  --profile "$PROFILE" \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --assets-dir "$work_dir" \
  --version "$VERSION"

echo "Promoted $tag to profile $PROFILE."
