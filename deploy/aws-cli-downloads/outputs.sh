#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"

if ! stack_exists; then
  echo "CloudFormation stack does not exist: $STACK_NAME" >&2
  exit 1
fi

print_stack_outputs