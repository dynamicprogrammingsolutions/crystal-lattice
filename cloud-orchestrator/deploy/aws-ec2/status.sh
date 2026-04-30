#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
load_state
parse_common_args "$@"

echo "StackName=${STACK_NAME}"
echo "Profile=${PROFILE}"
echo "Region=${REGION}"
echo "CloudOrchestratorUrl=${CLOUD_ORCHESTRATOR_URL:-}"
echo "EdgeStatus=$(stack_exists "$(edge_stack_name)" && aws_out cloudformation describe-stacks --stack-name "$(edge_stack_name)" --query 'Stacks[0].StackStatus' --output text || echo missing)"
echo "OriginStatus=$(stack_exists "$(origin_stack_name)" && aws_out cloudformation describe-stacks --stack-name "$(origin_stack_name)" --query 'Stacks[0].StackStatus' --output text || echo missing)"
echo "BuilderStatus=$(stack_exists "$(builder_stack_name)" && aws_out cloudformation describe-stacks --stack-name "$(builder_stack_name)" --query 'Stacks[0].StackStatus' --output text || echo missing)"