#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-fargate/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
load_state

case "$PROFILE" in
  public-task)
    stack="${STACK_NAME}-public-task"
    if ! stack_exists "$stack"; then
      echo "public-task stack not found: $stack"
      exit 1
    fi
    cluster="$(stack_output "$stack" ClusterName)"
    aws_out ecs list-tasks --cluster "$cluster" --started-by "$STACK_NAME"
    ;;

  secure)
    edge="${STACK_NAME}-edge"
    origin="${STACK_NAME}-origin"
    echo "Edge stack: $edge"
    stack_exists "$edge" && aws_out cloudformation describe-stacks --stack-name "$edge" --query 'Stacks[0].StackStatus' --output text || echo "missing"
    echo "Origin stack: $origin"
    stack_exists "$origin" && aws_out cloudformation describe-stacks --stack-name "$origin" --query 'Stacks[0].StackStatus' --output text || echo "missing"
    if stack_exists "$edge"; then
      echo "BridgeWebSocketUrl=$(stack_output "$edge" BridgeWebSocketUrl)"
    fi
    ;;

  *)
    echo "Unsupported profile: $PROFILE" >&2
    exit 2
    ;;
esac