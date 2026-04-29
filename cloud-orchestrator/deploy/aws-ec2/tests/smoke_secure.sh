#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

STACK_NAME="${AWS_STACK_NAME:-crystal-lattice-cloud-orchestrator-secure-test-$(date +%s)}"
REGION="${AWS_REGION:-us-east-1}"

if [ "${RUN_AWS_CLOUD_ORCHESTRATOR_TESTS:-}" != "1" ]; then
  echo "Set RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 to run AWS smoke tests." >&2
  exit 2
fi

cleanup() {
  "$SCRIPT_DIR/down.sh" --stack-name "$STACK_NAME" --region "$REGION" || true
}
trap cleanup EXIT

"$SCRIPT_DIR/build.sh" --stack-name "$STACK_NAME" --region "$REGION" >/dev/null
output="$("$SCRIPT_DIR/up.sh" --stack-name "$STACK_NAME" --region "$REGION" --json)"
orchestrator_url="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["orchestratorUrl"])' <<<"$output")"

if [ -z "$orchestrator_url" ]; then
  echo "AWS EC2 provisioning did not return an orchestrator URL." >&2
  exit 2
fi

wait_http_health "${orchestrator_url%/}/health"