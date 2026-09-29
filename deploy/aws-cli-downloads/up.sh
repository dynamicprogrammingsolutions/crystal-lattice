#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

UPLOAD_INSTALLER=1
LATEST_VERSION=""

usage() {
  cat <<'USAGE'
Create or update CLI download infrastructure and upload the domain-specific installer.

Usage:
  ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/up.sh [common options] [options]

Options:
  --skip-installer-upload      Only deploy infrastructure.
  --latest-version VERSION     Also upload latest.txt for this version.
  --help, -h                   Show this help.
USAGE
  usage_common
}

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --skip-installer-upload) UPLOAD_INSTALLER=0; shift ;;
    --latest-version) LATEST_VERSION="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) args+=("$1"); shift ;;
  esac
done

if [ "${#args[@]}" -gt 0 ]; then
  parse_common_args "${args[@]}"
else
  parse_common_args
fi
require_aws_deploy_enabled
find_hosted_zone_id

aws_out cloudformation validate-template --template-body "file://$TEMPLATE_FILE" >/dev/null

aws_out cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --parameter-overrides \
    HostedZoneId="$HOSTED_ZONE_ID" \
    DownloadDomainName="$DOWNLOAD_DOMAIN" \
    BucketNamePrefix="$BUCKET_NAME_PREFIX" \
    DownloadPrefix="$DOWNLOAD_PREFIX" \
    DesktopDownloadPrefix="$DESKTOP_DOWNLOAD_PREFIX" \
  --tags \
    Project=crystal-lattice \
    Component=cli-downloads \
    Profile="$PROFILE" \
    StackName="$STACK_NAME"

if [ "$UPLOAD_INSTALLER" -eq 1 ]; then
  installer_args=(--profile "$PROFILE" --stack-name "$STACK_NAME" --region "$REGION")
  if [ -n "$LATEST_VERSION" ]; then
    installer_args+=(--latest-version "$LATEST_VERSION")
  fi
  ALLOW_AWS_DEPLOY=1 "$SCRIPT_DIR/upload-installer.sh" "${installer_args[@]}"
fi

print_stack_outputs