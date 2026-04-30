#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_deploy_enabled
assert_supported_profile
load_state
parse_common_args "$@"

delete_stack_if_exists "$(origin_stack_name)"
delete_stack_if_exists "$(edge_stack_name)"

rm -f "$(state_file)"