#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

STACK_NAME="${AWS_STACK_NAME:-crystal-lattice-cloud-orchestrator-secure-test-$(date +%s)}"
REGION="${AWS_REGION:-us-east-1}"

if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ] && [ "${RUN_AWS_CLOUD_ORCHESTRATOR_TESTS:-}" != "1" ]; then
  echo "Set ALLOW_AWS_DEPLOY=1 to run AWS smoke tests." >&2
  exit 2
fi

cleanup() {
  ALLOW_AWS_DEPLOY=1 "$SCRIPT_DIR/down.sh" --profile secure --stack-name "$STACK_NAME" --region "$REGION" || true
}
trap cleanup EXIT

output="$(ALLOW_AWS_DEPLOY=1 "$SCRIPT_DIR/up.sh" --profile secure --stack-name "$STACK_NAME" --region "$REGION" --json)"
orchestrator_url="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["orchestratorUrl"])' <<<"$output")"

if [ -z "$orchestrator_url" ]; then
  echo "AWS EC2 provisioning did not return an orchestrator URL." >&2
  exit 2
fi

wait_http_health "${orchestrator_url%/}/health"