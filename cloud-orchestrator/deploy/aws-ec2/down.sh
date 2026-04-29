#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_tests_enabled
load_state
delete_stack_if_exists "$STACK_NAME"
if [ -n "${SOURCE_BUCKET:-}" ] && [ -n "${ORCHESTRATOR_IMAGE_KEY:-}" ]; then
  aws_out s3 rm "s3://${SOURCE_BUCKET}/${ORCHESTRATOR_IMAGE_KEY}" >/dev/null 2>&1 || true
fi
if [ -n "${SOURCE_BUCKET:-}" ] && [ -n "${RUNTIME_IMAGE_KEY:-}" ]; then
  aws_out s3 rm "s3://${SOURCE_BUCKET}/${RUNTIME_IMAGE_KEY}" >/dev/null 2>&1 || true
fi
rm -f "$(state_file)"