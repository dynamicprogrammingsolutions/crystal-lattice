#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_deploy_enabled

if ! stack_exists; then
  echo "CloudFormation stack does not exist: $STACK_NAME"
  exit 0
fi

bucket="$(stack_output DownloadsBucket)"

if [ -n "$bucket" ] && [ "$bucket" != "None" ]; then
  aws_out s3 rm "s3://${bucket}" --recursive || true
fi

aws_out cloudformation delete-stack --stack-name "$STACK_NAME"
aws_out cloudformation wait stack-delete-complete --stack-name "$STACK_NAME"

echo "Deleted stack $STACK_NAME. Stack-managed DNS records were removed."