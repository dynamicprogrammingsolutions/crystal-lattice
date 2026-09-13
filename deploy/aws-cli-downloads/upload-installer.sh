#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

BASE_URL=""
BUCKET_OVERRIDE=""
PREFIX_OVERRIDE=""
DISTRIBUTION_OVERRIDE=""
LATEST_VERSION=""
DRY_RUN=0
PRINT_ONLY=0

usage() {
  cat <<'USAGE'
Generate and upload a domain-specific install.sh for a CLI download stack.

Usage:
  ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/upload-installer.sh [common options] [options]

Options:
  --base-url URL               Override stack output DownloadsBaseUrl.
  --bucket BUCKET              Upload bucket, bypassing stack output lookup.
  --prefix PREFIX              Upload prefix, bypassing stack output lookup.
  --distribution-id ID         CloudFront distribution ID, bypassing stack output lookup.
  --latest-version VERSION     Also upload latest.txt for this version.
  --print                      Print generated installer to stdout.
  --dry-run                    Print AWS commands without mutating resources.
  --help, -h                   Show this help.
USAGE
  usage_common
}

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --base-url) BASE_URL="$2"; shift 2 ;;
    --bucket) BUCKET_OVERRIDE="$2"; shift 2 ;;
    --prefix) PREFIX_OVERRIDE="$2"; shift 2 ;;
    --distribution-id) DISTRIBUTION_OVERRIDE="$2"; shift 2 ;;
    --latest-version) LATEST_VERSION="$2"; shift 2 ;;
    --print) PRINT_ONLY=1; shift ;;
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
if [ "$DRY_RUN" -eq 0 ] && [ "$PRINT_ONLY" -eq 0 ]; then
  require_aws_deploy_enabled
fi

if [ -z "$BASE_URL" ]; then
  if [ -n "$BUCKET_OVERRIDE" ]; then
    echo "--base-url is required when using --bucket without stack output lookup" >&2
    exit 1
  fi
  if ! stack_exists; then
    echo "CloudFormation stack does not exist and --base-url was not provided: $STACK_NAME" >&2
    exit 1
  fi
  BASE_URL="$(downloads_base_url)"
fi

generate_installer() {
  python - "$BASE_URL" "$REPO_ROOT/application/python/scripts/install.sh" <<'PY'
from pathlib import Path
import re
import sys

base_url = sys.argv[1]
source = Path(sys.argv[2])
text = source.read_text(encoding="utf-8")
text = re.sub(
    r'^DEFAULT_DOWNLOAD_BASE_URL="[^"]*"$',
    f'DEFAULT_DOWNLOAD_BASE_URL="{base_url}"',
    text,
    count=1,
    flags=re.MULTILINE,
)
if base_url not in text:
    raise SystemExit("generated installer does not contain requested base URL")
print(text, end="")
PY
}

if [ "$PRINT_ONLY" -eq 1 ]; then
  generate_installer
  exit 0
fi

if [ -n "$BUCKET_OVERRIDE" ]; then
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
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
installer="$tmp_dir/install.sh"
generate_installer > "$installer"
bash -n "$installer"

run_or_print() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

run_or_print aws --region "$REGION" s3 cp "$installer" "s3://${bucket}/${prefix}/install.sh" \
  --content-type "$(content_type_for_path install.sh)" \
  --cache-control "$(cache_control_for_path install.sh)"

paths=("/${prefix}/install.sh")

if [ -n "$LATEST_VERSION" ]; then
  tag="$(normalize_version_tag "$LATEST_VERSION")"
  printf '%s\n' "$tag" > "$tmp_dir/latest.txt"
  run_or_print aws --region "$REGION" s3 cp "$tmp_dir/latest.txt" "s3://${bucket}/${prefix}/latest.txt" \
    --content-type "$(content_type_for_path latest.txt)" \
    --cache-control "$(cache_control_for_path latest.txt)"
  paths+=("/${prefix}/latest.txt")
fi

if [ -z "$distribution" ] || [ "$distribution" = "None" ]; then
  :
elif [ "$DRY_RUN" -eq 1 ]; then
  printf 'DRY RUN:'
  printf ' %q' aws --region "$REGION" cloudfront create-invalidation --distribution-id "$distribution" --paths "${paths[@]}"
  printf '\n'
else
  invalidate_download_paths "$distribution" "${paths[@]}"
fi

echo "Uploaded installer for $BASE_URL"