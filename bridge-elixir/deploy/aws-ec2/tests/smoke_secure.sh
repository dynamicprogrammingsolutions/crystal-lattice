#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

STACK_NAME="${AWS_STACK_NAME:-crystal-lattice-bridge-ec2-secure-test-$(date +%s)}"
REGION="${AWS_REGION:-us-east-1}"

if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ] && [ "${RUN_AWS_BRIDGE_TESTS:-}" != "1" ]; then
  echo "Set ALLOW_AWS_DEPLOY=1 to run AWS smoke tests." >&2
  exit 2
fi

cleanup() {
  ALLOW_AWS_DEPLOY=1 "$SCRIPT_DIR/down.sh" --profile secure --stack-name "$STACK_NAME" --region "$REGION" || true
}
trap cleanup EXIT

output="$(ALLOW_AWS_DEPLOY=1 "$SCRIPT_DIR/up.sh" --profile secure --stack-name "$STACK_NAME" --region "$REGION" --json)"
bridge_http_url="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["bridgeHttpUrl"])' <<<"$output")"
wait_http_health "$bridge_http_url"