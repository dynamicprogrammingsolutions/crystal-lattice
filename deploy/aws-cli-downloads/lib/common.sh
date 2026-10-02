#!/usr/bin/env bash

set -euo pipefail

CLI_DOWNLOADS_DIR="${CLI_DOWNLOADS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "$CLI_DOWNLOADS_DIR/../.." && pwd)}"
TEMPLATE_FILE="$CLI_DOWNLOADS_DIR/downloads.yaml"

PROFILE="test"
REGION="${AWS_REGION:-us-east-1}"
STACK_NAME=""
HOSTED_ZONE_NAME=""
HOSTED_ZONE_ID=""
DOWNLOAD_DOMAIN=""
BUCKET_NAME_PREFIX=""
DOWNLOAD_PREFIX="crystal-lattice-cli"
JSON_OUTPUT=0

LOG_STEP_TOTAL=0
LOG_STEP_INDEX=0

# Set the total number of steps before the first log_step call so progress
# headers can show [n/total].
log_set_step_total() {
  LOG_STEP_TOTAL="$1"
}

# Print a numbered progress header for one phase of a script run.
log_step() {
  LOG_STEP_INDEX=$((LOG_STEP_INDEX + 1))
  if [ "$LOG_STEP_TOTAL" -gt 0 ]; then
    printf '[%d/%d] %s\n' "$LOG_STEP_INDEX" "$LOG_STEP_TOTAL" "$1"
  else
    printf '[%d] %s\n' "$LOG_STEP_INDEX" "$1"
  fi
}

# Print an indented detail line under the most recent log_step header.
log_detail() {
  printf '      %s\n' "$1"
}

usage_common() {
  cat <<'USAGE'
Common options:
  --profile test|prod
  --stack-name NAME
  --region REGION
  --hosted-zone-name NAME
  --hosted-zone-id ID
  --download-domain DOMAIN
  --bucket-name-prefix PREFIX
  --prefix PREFIX
  --json

Defaults:
  test stack:          crystal-lattice-cli-downloads-test
  test hosted zone:    dynamicprogrammingsolutions.com
  test domain:         download.crystallattice.dev.dynamicprogrammingsolutions.com
  test bucket prefix:  crystal-lattice-cli-downloads-test

  prod stack:          crystal-lattice-cli-downloads-prod
  prod hosted zone:    crystallattice.dev
  prod domain:         download.crystallattice.dev
  prod bucket prefix:  crystal-lattice-cli-downloads-prod

  region:              us-east-1
  prefix:              crystal-lattice-cli
USAGE
}

parse_common_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --profile) PROFILE="$2"; shift 2 ;;
      --stack-name) STACK_NAME="$2"; shift 2 ;;
      --region) REGION="$2"; shift 2 ;;
      --hosted-zone-name) HOSTED_ZONE_NAME="$2"; shift 2 ;;
      --hosted-zone-id) HOSTED_ZONE_ID="$2"; shift 2 ;;
      --download-domain) DOWNLOAD_DOMAIN="$2"; shift 2 ;;
      --bucket-name-prefix) BUCKET_NAME_PREFIX="$2"; shift 2 ;;
      --prefix) DOWNLOAD_PREFIX="$2"; shift 2 ;;
      --json) JSON_OUTPUT=1; shift ;;
      --help|-h) usage_common; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage_common >&2; exit 2 ;;
    esac
  done
  apply_profile_defaults
}

apply_profile_defaults() {
  case "$PROFILE" in
    prod)
      STACK_NAME="${STACK_NAME:-crystal-lattice-cli-downloads-prod}"
      HOSTED_ZONE_NAME="${HOSTED_ZONE_NAME:-crystallattice.dev}"
      DOWNLOAD_DOMAIN="${DOWNLOAD_DOMAIN:-download.crystallattice.dev}"
      BUCKET_NAME_PREFIX="${BUCKET_NAME_PREFIX:-crystal-lattice-cli-downloads-prod}"
      ;;
    test)
      STACK_NAME="${STACK_NAME:-crystal-lattice-cli-downloads-test}"
      HOSTED_ZONE_NAME="${HOSTED_ZONE_NAME:-dynamicprogrammingsolutions.com}"
      DOWNLOAD_DOMAIN="${DOWNLOAD_DOMAIN:-download.crystallattice.dev.dynamicprogrammingsolutions.com}"
      BUCKET_NAME_PREFIX="${BUCKET_NAME_PREFIX:-crystal-lattice-cli-downloads-test}"
      ;;
    *)
      echo "Unsupported profile: $PROFILE" >&2
      exit 2
      ;;
  esac
}

require_aws_deploy_enabled() {
  if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ]; then
    echo "Set ALLOW_AWS_DEPLOY=1 to create, update, sync, or delete AWS resources." >&2
    exit 2
  fi
}

aws_out() {
  aws --region "$REGION" "$@"
}

find_hosted_zone_id() {
  if [ -n "$HOSTED_ZONE_ID" ]; then
    HOSTED_ZONE_ID="${HOSTED_ZONE_ID#/hostedzone/}"
    return
  fi

  local zone_name="$HOSTED_ZONE_NAME"
  case "$zone_name" in
    *.) ;;
    *) zone_name="${zone_name}." ;;
  esac

  HOSTED_ZONE_ID="$(
    aws_out route53 list-hosted-zones-by-name \
      --dns-name "$zone_name" \
      --query "HostedZones[?Name=='${zone_name}' && Config.PrivateZone==\`false\`].Id | [0]" \
      --output text
  )"
  HOSTED_ZONE_ID="${HOSTED_ZONE_ID#/hostedzone/}"

  if [ -z "$HOSTED_ZONE_ID" ] || [ "$HOSTED_ZONE_ID" = "None" ]; then
    echo "Could not find public Route 53 hosted zone for $HOSTED_ZONE_NAME" >&2
    exit 1
  fi
}

stack_exists() {
  aws_out cloudformation describe-stacks --stack-name "$STACK_NAME" >/dev/null 2>&1
}

stack_output() {
  local key="$1"
  aws_out cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue | [0]" \
    --output text
}

downloads_base_url() {
  stack_output DownloadsBaseUrl
}

read_project_version() {
  python - <<'PY'
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
metadata = tomllib.loads(Path("application/python/pyproject.toml").read_text(encoding="utf-8"))
print(metadata["project"]["version"])
PY
}

normalize_version_tag() {
  case "$1" in
    crystal-lattice-cli-v*) printf '%s\n' "$1" ;;
    v*) printf 'crystal-lattice-cli-%s\n' "$1" ;;
    *) printf 'crystal-lattice-cli-v%s\n' "$1" ;;
  esac
}

archive_names_for_version() {
  local version="$1"
  cat <<EOF
crystal-lattice-python-runtime-v${version}-darwin-amd64.tar.gz
crystal-lattice-python-runtime-v${version}-darwin-arm64.tar.gz
crystal-lattice-python-runtime-v${version}-linux-amd64.tar.gz
crystal-lattice-python-runtime-v${version}-linux-arm64.tar.gz
crystal-lattice-python-runtime-v${version}-windows-amd64.zip
crystal-lattice-python-runtime-v${version}-windows-arm64.zip
EOF
}

content_type_for_path() {
  case "$1" in
    *.zip) printf '%s\n' "application/zip" ;;
    *.tar.gz) printf '%s\n' "application/gzip" ;;
    *.sh) printf '%s\n' "text/x-shellscript; charset=utf-8" ;;
    *.ps1) printf '%s\n' "text/plain; charset=utf-8" ;;
    *.txt) printf '%s\n' "text/plain; charset=utf-8" ;;
    *) printf '%s\n' "application/octet-stream" ;;
  esac
}

cache_control_for_path() {
  case "$1" in
    *.zip|*.tar.gz) printf '%s\n' "public, max-age=31536000, immutable" ;;
    install.sh|install.ps1|latest.txt) printf '%s\n' "public, max-age=60" ;;
    *) printf '%s\n' "public, max-age=300" ;;
  esac
}

invalidate_download_paths() {
  local distribution_id="$1"
  shift
  [ -n "$distribution_id" ] && [ "$distribution_id" != "None" ] || return 0
  [ "$#" -gt 0 ] || return 0
  aws_out cloudfront create-invalidation \
    --distribution-id "$distribution_id" \
    --paths "$@" >/dev/null
}

print_stack_outputs() {
  local bucket prefix base_url distribution cloudfront certificate hosted_zone domain
  bucket="$(stack_output DownloadsBucket)"
  prefix="$(stack_output DownloadsPrefix)"
  base_url="$(stack_output DownloadsBaseUrl)"
  distribution="$(stack_output DownloadsCloudFrontDistributionId)"
  cloudfront="$(stack_output DownloadsCloudFrontDomainName)"
  certificate="$(stack_output CertificateArn)"
  hosted_zone="$(stack_output HostedZoneId)"
  domain="$(stack_output DownloadDomainName)"

  if [ "$JSON_OUTPUT" -eq 1 ]; then
    printf '{"AWS_REGION":"%s","DOWNLOADS_BUCKET":"%s","DOWNLOADS_PREFIX":"%s","DOWNLOADS_BASE_URL":"%s","DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID":"%s","DOWNLOADS_CLOUDFRONT_DOMAIN":"%s","DOWNLOAD_DOMAIN":"%s","CERTIFICATE_ARN":"%s","HOSTED_ZONE_ID":"%s"}\n' \
      "$REGION" "$bucket" "$prefix" "$base_url" "$distribution" "$cloudfront" "$domain" "$certificate" "$hosted_zone"
  else
    echo "AWS_REGION=$REGION"
    echo "DOWNLOADS_BUCKET=$bucket"
    echo "DOWNLOADS_PREFIX=$prefix"
    echo "DOWNLOADS_BASE_URL=$base_url"
    echo "DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID=$distribution"
    echo "DOWNLOADS_CLOUDFRONT_DOMAIN=$cloudfront"
    echo "DOWNLOAD_DOMAIN=$domain"
    echo "CERTIFICATE_ARN=$certificate"
    echo "HOSTED_ZONE_ID=$hosted_zone"
  fi
}