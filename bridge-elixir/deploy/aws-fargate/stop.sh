#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-fargate/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_tests_enabled
load_state

case "$PROFILE" in
  public-task)
    stack="${STACK_NAME}-public-task"
    if stack_exists "$stack"; then
      cluster="$(stack_output "$stack" ClusterName)"
      task_arns="$(aws_out ecs list-tasks --cluster "$cluster" --started-by "$STACK_NAME" --query 'taskArns[]' --output text || true)"
      for task_arn in $task_arns; do
        aws_out ecs stop-task --cluster "$cluster" --task "$task_arn" --reason "Crystal Lattice bridge stop" >/dev/null
      done
    fi
    ;;

  secure)
    delete_stack_if_exists "${STACK_NAME}-origin"
    ;;

  *)
    echo "Unsupported profile: $PROFILE" >&2
    exit 2
    ;;
esac