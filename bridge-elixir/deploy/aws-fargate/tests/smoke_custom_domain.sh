#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRIDGE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STACK_NAME="${AWS_STACK_NAME:-crystal-lattice-bridge-domain-test-$(date +%s)}"
REGION="${AWS_REGION:-us-east-1}"
KEEP_ON_FAILURE="${KEEP_ON_FAILURE:-0}"

if [ -z "${BRIDGE_DOMAIN:-}" ] || [ -z "${AWS_HOSTED_ZONE_ID:-}" ]; then
  echo "BRIDGE_DOMAIN and AWS_HOSTED_ZONE_ID are required." >&2
  exit 2
fi

cleanup() {
  if [ "$KEEP_ON_FAILURE" != "1" ]; then
    "$SCRIPT_DIR/down.sh" --profile secure --stack-name "$STACK_NAME" --region "$REGION" || true
  fi
}
trap cleanup EXIT

if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ] && [ "${RUN_AWS_BRIDGE_TESTS:-}" != "1" ]; then
  echo "Set ALLOW_AWS_DEPLOY=1 to run AWS smoke tests." >&2
  exit 2
fi

output="$("$SCRIPT_DIR/up.sh" \
  --profile secure \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --domain "$BRIDGE_DOMAIN" \
  --hosted-zone-id "$AWS_HOSTED_ZONE_ID" \
  --json)"
bridge_url="$(python3 -c 'import json,sys; lines=[line for line in sys.stdin.read().splitlines() if line.strip().startswith("{")]; print(json.loads(lines[-1])["bridgeWebSocketUrl"])' <<<"$output")"

BRIDGE_URL="$bridge_url" python3 "$BRIDGE_DIR/test_docker.py"