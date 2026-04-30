#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
STACK_NAME="${AWS_STACK_NAME:-crystal-lattice-bridge-restart-test-$(date +%s)}"
REGION="${AWS_REGION:-us-east-1}"
KEEP_ON_FAILURE="${KEEP_ON_FAILURE:-0}"

cleanup() {
  if [ "$KEEP_ON_FAILURE" != "1" ]; then
    "$SCRIPT_DIR/down.sh" --profile secure --stack-name "$STACK_NAME" --region "$REGION" || true
  fi
}
trap cleanup EXIT

if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ] && [ "${RUN_AWS_BRIDGE_TESTS:-}" != "1" ]; then
  echo "Set ALLOW_AWS_DEPLOY=1 to run AWS restart smoke tests." >&2
  exit 2
fi

cd "$REPO_ROOT/packages/frontend-sdk"

RUN_BRIDGE_E2E_INTEGRATION=1 \
RUN_AWS_BRIDGE_TESTS=1 \
ALLOW_AWS_DEPLOY=1 \
BRIDGE_E2E_MODE=aws-secure \
AWS_REGION="$REGION" \
AWS_STACK_NAME="$STACK_NAME" \
npm test -- src/integration/__tests__/bridge.e2e.integration.test.ts \
  -t "reconnects and resumes after the bridge restarts"