#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
load_state

echo "StackName=${STACK_NAME}"
echo "Region=${REGION}"
echo "CloudOrchestratorUrl=${CLOUD_ORCHESTRATOR_URL:-}"
if stack_exists "$STACK_NAME"; then
  aws_out cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text
fi