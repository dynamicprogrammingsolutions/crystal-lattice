#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_SITES_DIR="$SCRIPT_DIR"
# shellcheck source=deploy/aws-static-sites/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_deploy_enabled

if ! stack_exists; then
  echo "CloudFormation stack does not exist: $STACK_NAME"
  exit 0
fi

landing_bucket="$(stack_output LandingBucket)"
docs_bucket="$(stack_output DocsBucket)"

if [ -n "$landing_bucket" ] && [ "$landing_bucket" != "None" ]; then
  aws_out s3 rm "s3://${landing_bucket}" --recursive || true
fi
if [ -n "$docs_bucket" ] && [ "$docs_bucket" != "None" ]; then
  aws_out s3 rm "s3://${docs_bucket}" --recursive || true
fi

aws_out cloudformation delete-stack --stack-name "$STACK_NAME"
aws_out cloudformation wait stack-delete-complete --stack-name "$STACK_NAME"

echo "Deleted stack $STACK_NAME. Stack-managed testing DNS records were removed."