#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-install-lab/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_deploy_enabled

if ! stack_exists; then
  echo "CloudFormation stack does not exist: $STACK_NAME"
  exit 0
fi

aws_out cloudformation delete-stack --stack-name "$STACK_NAME"
aws_out cloudformation wait stack-delete-complete --stack-name "$STACK_NAME"

echo "Deleted CLI install lab stack: $STACK_NAME"