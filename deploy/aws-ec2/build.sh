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

if [ "$BUILD_METHOD" != "codebuild" ]; then
  echo "Unsupported builder: $BUILD_METHOD. Combined EC2 builds use --builder codebuild." >&2
  exit 2
fi

bridge_out="$(ALLOW_AWS_DEPLOY=1 "$REPO_ROOT/bridge-elixir/deploy/aws-ec2/build.sh" \
  --profile "$PROFILE" \
  --stack-name "${STACK_NAME}-bridge" \
  --region "$REGION" \
  --image-tag "$IMAGE_TAG" \
  --docker-platform "$DOCKER_PLATFORM" \
  --cpu-architecture "$CPU_ARCHITECTURE" \
  --builder "$BUILD_METHOD" \
  --json)"

orchestrator_out="$(ALLOW_AWS_DEPLOY=1 "$REPO_ROOT/cloud-orchestrator/deploy/aws-ec2/build.sh" \
  --profile "$PROFILE" \
  --stack-name "${STACK_NAME}-orchestrator" \
  --region "$REGION" \
  --image-tag "$IMAGE_TAG" \
  --docker-platform "$DOCKER_PLATFORM" \
  --cpu-architecture "$CPU_ARCHITECTURE" \
  --builder "$BUILD_METHOD" \
  --json)"

BRIDGE_IMAGE_URI="$(python3 -c 'import json,sys; lines=[l for l in sys.stdin.read().splitlines() if l.strip().startswith("{")]; print(json.loads(lines[-1])["bridgeImageUri"])' <<<"$bridge_out")"
ORCHESTRATOR_IMAGE_URI="$(python3 -c 'import json,sys; lines=[l for l in sys.stdin.read().splitlines() if l.strip().startswith("{")]; print(json.loads(lines[-1])["orchestratorImageUri"])' <<<"$orchestrator_out")"
RUNTIME_IMAGE_URI="$(python3 -c 'import json,sys; lines=[l for l in sys.stdin.read().splitlines() if l.strip().startswith("{")]; print(json.loads(lines[-1])["runtimeImageUri"])' <<<"$orchestrator_out")"
save_state

if [ "$JSON_OUTPUT" -eq 1 ]; then
  printf '{"bridgeImageUri":"%s","orchestratorImageUri":"%s","runtimeImageUri":"%s","stackName":"%s","region":"%s","builder":"%s"}\n' \
    "$BRIDGE_IMAGE_URI" "$ORCHESTRATOR_IMAGE_URI" "$RUNTIME_IMAGE_URI" "$STACK_NAME" "$REGION" "$BUILD_METHOD"
else
  echo "BridgeImageUri=$BRIDGE_IMAGE_URI"
  echo "OrchestratorImageUri=$ORCHESTRATOR_IMAGE_URI"
  echo "RuntimeImageUri=$RUNTIME_IMAGE_URI"
  echo "Builder=$BUILD_METHOD"
fi