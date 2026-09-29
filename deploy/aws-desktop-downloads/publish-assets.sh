#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$REPO_ROOT/deploy/aws-cli-downloads/lib/common.sh"

ASSETS_DIR=""
VERSION=""
SOURCE_COMMIT=""
BUCKET=""
PREFIX="crystal-lattice-desktop"
BASE_URL=""
DISTRIBUTION_ID=""
DRY_RUN=0

usage() {
  cat <<'USAGE'
Publish a verified Crystal Lattice Desktop candidate to the shared download CDN.

Usage:
  ALLOW_AWS_DEPLOY=1 deploy/aws-desktop-downloads/publish-assets.sh [options]

Options:
  --assets-dir DIR             Candidate directory containing exactly four verified files.
  --version VERSION            Marketing version, for example 0.9.0.
  --source-commit SHA          Exact source commit recorded in release metadata.
  --bucket BUCKET              Existing private downloads bucket.
  --prefix PREFIX              Desktop S3/URL prefix. Default: crystal-lattice-desktop.
  --base-url URL               Public desktop base URL.
  --distribution-id ID         Existing CloudFront distribution.
  --region REGION              AWS region. Default: AWS_REGION or us-east-1.
  --dry-run                    Validate and print AWS commands without changing AWS.
  --help, -h                   Show this help.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --assets-dir) ASSETS_DIR="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --source-commit) SOURCE_COMMIT="$2"; shift 2 ;;
    --bucket) BUCKET="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --base-url) BASE_URL="$2"; shift 2 ;;
    --distribution-id) DISTRIBUTION_ID="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

: "${ASSETS_DIR:?--assets-dir is required}"
: "${VERSION:?--version is required}"
: "${SOURCE_COMMIT:?--source-commit is required}"
: "${BUCKET:?--bucket is required}"
: "${BASE_URL:?--base-url is required}"
: "${DISTRIBUTION_ID:?--distribution-id is required}"

if [ "$DRY_RUN" -eq 0 ]; then
  require_aws_deploy_enabled
fi

ASSETS_DIR="$(cd "$ASSETS_DIR" && pwd)"
python3 \
  "$REPO_ROOT/desktop/crystal-lattice-control-desktop-rn/scripts/verify_desktop_release_candidate.py" \
  "$ASSETS_DIR" \
  --commit "$SOURCE_COMMIT" \
  --version "$VERSION"

dmg="Crystal-Lattice-Desktop-v${VERSION}-universal.dmg"
checksum="${dmg}.sha256"
metadata="Crystal-Lattice-Desktop-v${VERSION}-release-metadata.json"
notarization="Crystal-Lattice-Desktop-v${VERSION}-notarization.json"

run_or_print() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

if [ "$DRY_RUN" -eq 0 ]; then
  for name in "$dmg" "$checksum" "$metadata" "$notarization"; do
    error_file="$(mktemp)"
    if aws --region "$REGION" s3api head-object \
      --bucket "$BUCKET" \
      --key "${PREFIX}/${name}" \
      >/dev/null 2>"$error_file"; then
      rm -f "$error_file"
      echo "Refusing to overwrite immutable desktop release object: ${PREFIX}/${name}" >&2
      exit 1
    elif ! grep -Eq '(404|Not Found)' "$error_file"; then
      cat "$error_file" >&2
      rm -f "$error_file"
      exit 1
    fi
    rm -f "$error_file"
  done
fi

upload() {
  local source="$1"
  local destination_name="$2"
  run_or_print aws --region "$REGION" s3 cp "$source" \
    "s3://${BUCKET}/${PREFIX}/${destination_name}" \
    --content-type "$(content_type_for_path "$destination_name")" \
    --cache-control "$(cache_control_for_path "$destination_name")"
}

upload "$ASSETS_DIR/$dmg" "$dmg"
upload "$ASSETS_DIR/$checksum" "$checksum"
upload "$ASSETS_DIR/release-metadata.json" "$metadata"
upload "$ASSETS_DIR/notarization.json" "$notarization"

marker_directory="$(mktemp -d)"
trap 'rm -rf "$marker_directory"' EXIT
printf 'crystal-lattice-desktop-v%s\n' "$VERSION" > "$marker_directory/latest.txt"
run_or_print aws --region "$REGION" s3 cp "$marker_directory/latest.txt" \
  "s3://${BUCKET}/${PREFIX}/latest.txt" \
  --content-type "$(content_type_for_path latest.txt)" \
  --cache-control "$(cache_control_for_path latest.txt)"

paths=(
  "/${PREFIX}/${dmg}"
  "/${PREFIX}/${checksum}"
  "/${PREFIX}/${metadata}"
  "/${PREFIX}/${notarization}"
  "/${PREFIX}/latest.txt"
)
if [ "$DRY_RUN" -eq 1 ]; then
  run_or_print aws --region "$REGION" cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "${paths[@]}"
else
  invalidate_download_paths "$DISTRIBUTION_ID" "${paths[@]}"
fi

echo "Published Crystal Lattice Desktop ${VERSION}: ${BASE_URL}/${dmg}"