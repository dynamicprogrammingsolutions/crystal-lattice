#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

ASSETS_DIR="$REPO_ROOT/dist/crystal-lattice-python-runtime"
VERSION=""
BUCKET_OVERRIDE=""
PREFIX_OVERRIDE=""
BASE_URL=""
DISTRIBUTION_OVERRIDE=""
DRY_RUN=0
SKIP_INSTALLER=0

usage() {
  cat <<'USAGE'
Publish existing release assets to a configured CLI download stack.

Usage:
  ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/publish-assets.sh [common options] [options]

Options:
  --assets-dir DIR             Directory containing release archives.
  --version VERSION            Version without tag prefix. Defaults to pyproject version.
  --bucket BUCKET              Upload bucket, bypassing stack output lookup.
  --prefix PREFIX              Upload prefix, bypassing stack output lookup.
  --base-url URL               Download base URL for generated installer.
  --distribution-id ID         CloudFront distribution ID, bypassing stack output lookup.
  --skip-installer             Do not upload install.sh or install.ps1.
  --dry-run                    Print AWS commands without mutating resources.
  --help, -h                   Show this help.
USAGE
  usage_common
}

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --assets-dir) ASSETS_DIR="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --bucket) BUCKET_OVERRIDE="$2"; shift 2 ;;
    --prefix) PREFIX_OVERRIDE="$2"; shift 2 ;;
    --base-url) BASE_URL="$2"; shift 2 ;;
    --distribution-id) DISTRIBUTION_OVERRIDE="$2"; shift 2 ;;
    --skip-installer) SKIP_INSTALLER=1; shift ;;
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

if [ -n "$BUCKET_OVERRIDE" ]; then
  [ -n "$BASE_URL" ] || {
    echo "--base-url is required when using --bucket without stack output lookup" >&2
    exit 1
  }
  bucket="$BUCKET_OVERRIDE"
  prefix="${PREFIX_OVERRIDE:-$DOWNLOAD_PREFIX}"
  distribution="$DISTRIBUTION_OVERRIDE"
elif ! stack_exists; then
  echo "CloudFormation stack does not exist: $STACK_NAME" >&2
  exit 1
else
  bucket="$(stack_output DownloadsBucket)"
  prefix="$(stack_output DownloadsPrefix)"
  distribution="$(stack_output DownloadsCloudFrontDistributionId)"
  BASE_URL="${BASE_URL:-$(stack_output DownloadsBaseUrl)}"
fi

VERSION="${VERSION:-$(cd "$REPO_ROOT" && read_project_version)}"
ASSETS_DIR="$(cd "$ASSETS_DIR" && pwd)"

missing=0
while IFS= read -r name; do
  if [ ! -f "$ASSETS_DIR/$name" ]; then
    echo "Missing release asset: $ASSETS_DIR/$name" >&2
    missing=1
  fi
done < <(archive_names_for_version "$VERSION")
[ "$missing" -eq 0 ] || exit 1

run_or_print() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

paths=()
if [ "$SKIP_INSTALLER" -eq 0 ]; then
  installer_args=(--profile "$PROFILE" --stack-name "$STACK_NAME" --region "$REGION" --latest-version "$VERSION")
  installer_args+=(--bucket "$bucket" --prefix "$prefix" --base-url "$BASE_URL")
  if [ -n "$distribution" ] && [ "$distribution" != "None" ]; then
    installer_args+=(--distribution-id "$distribution")
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    installer_args+=(--dry-run)
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    "$SCRIPT_DIR/upload-installer.sh" "${installer_args[@]}"
  else
    ALLOW_AWS_DEPLOY=1 "$SCRIPT_DIR/upload-installer.sh" "${installer_args[@]}"
  fi
fi

while IFS= read -r name; do
  source="$ASSETS_DIR/$name"
  run_or_print aws --region "$REGION" s3 cp "$source" "s3://${bucket}/${prefix}/${name}" \
    --content-type "$(content_type_for_path "$name")" \
    --cache-control "$(cache_control_for_path "$name")"
  paths+=("/${prefix}/${name}")
done < <(archive_names_for_version "$VERSION")

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
normalize_version_tag "$VERSION" > "$tmp_dir/latest.txt"
run_or_print aws --region "$REGION" s3 cp "$tmp_dir/latest.txt" "s3://${bucket}/${prefix}/latest.txt" \
  --content-type "$(content_type_for_path latest.txt)" \
  --cache-control "$(cache_control_for_path latest.txt)"
paths+=("/${prefix}/latest.txt")

if [ -z "$distribution" ] || [ "$distribution" = "None" ]; then
  :
elif [ "$DRY_RUN" -eq 1 ]; then
  printf 'DRY RUN:'
  printf ' %q' aws --region "$REGION" cloudfront create-invalidation --distribution-id "$distribution" --paths "${paths[@]}"
  printf '\n'
else
  invalidate_download_paths "$distribution" "${paths[@]}"
fi

echo "Published Crystal Lattice CLI $VERSION to $BASE_URL"