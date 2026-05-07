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
    "$SCRIPT_DIR/stop.sh" --profile public-task --stack-name "$STACK_NAME" --region "$REGION"
    delete_stack_if_exists "${STACK_NAME}-public-task"
    ;;

  secure)
    delete_stack_if_exists "${STACK_NAME}-origin"
    delete_stack_if_exists "${STACK_NAME}-edge"
    ;;

  *)
    echo "Unsupported profile: $PROFILE" >&2
    exit 2
    ;;
esac

rm -f "$(state_file)"