#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_tests_enabled
assert_supported_profile
load_state
parse_common_args "$@"
ensure_source_bucket
ensure_artifact_keys
ensure_platform_default

if [ "$BUILD_METHOD" != "codebuild" ]; then
  echo "Unsupported builder: $BUILD_METHOD. EC2 deploy builds now use --builder codebuild." >&2
  exit 2
fi

ensure_ecr_repository "$ORCHESTRATOR_ECR_REPOSITORY"
ensure_ecr_repository "$RUNTIME_ECR_REPOSITORY"
upload_source_bundle

builder_stack="$(builder_stack_name)"
deploy_stack "$builder_stack" "$SCRIPT_DIR/builder.yaml" \
  StackName="$STACK_NAME" \
  SourceBucket="$SOURCE_BUCKET" \
  SourceBundleKey="$SOURCE_BUNDLE_KEY" \
  OrchestratorRepository="$ORCHESTRATOR_ECR_REPOSITORY" \
  RuntimeRepository="$RUNTIME_ECR_REPOSITORY" \
  ImageTag="$IMAGE_TAG" \
  DockerPlatform="$DOCKER_PLATFORM"

project_name="$(stack_output "$builder_stack" BuildProjectName)"
build_id="$(aws_out codebuild start-build --project-name "$project_name" --query 'build.id' --output text)"

deadline=$((SECONDS + 3600))
status=""
while [ "$SECONDS" -lt "$deadline" ]; do
  status="$(aws_out codebuild batch-get-builds --ids "$build_id" --query 'builds[0].buildStatus' --output text)"
  case "$status" in
    SUCCEEDED)
      break
      ;;
    FAILED|FAULT|STOPPED|TIMED_OUT)
      aws_out codebuild batch-get-builds --ids "$build_id" --query 'builds[0].logs.deepLink' --output text >&2 || true
      echo "CodeBuild failed with status $status" >&2
      exit 1
      ;;
  esac
  sleep 15
done

if [ "$status" != "SUCCEEDED" ]; then
  echo "Timed out waiting for CodeBuild build $build_id" >&2
  exit 1
fi

ORCHESTRATOR_IMAGE_URI="$(ecr_uri_for "$ORCHESTRATOR_ECR_REPOSITORY" "$IMAGE_TAG")"
RUNTIME_IMAGE_URI="$(ecr_uri_for "$RUNTIME_ECR_REPOSITORY" "$IMAGE_TAG")"
save_state

if [ "$JSON_OUTPUT" -eq 1 ]; then
  printf '{"sourceBucket":"%s","sourceBundleKey":"%s","orchestratorImageUri":"%s","runtimeImageUri":"%s","dockerPlatform":"%s","cpuArchitecture":"%s","instanceType":"%s","builder":"%s","stackName":"%s","region":"%s"}\n' \
    "$SOURCE_BUCKET" "$SOURCE_BUNDLE_KEY" "$ORCHESTRATOR_IMAGE_URI" "$RUNTIME_IMAGE_URI" "$DOCKER_PLATFORM" "$CPU_ARCHITECTURE" "$INSTANCE_TYPE" "$BUILD_METHOD" "$STACK_NAME" "$REGION"
else
  echo "SourceBucket=$SOURCE_BUCKET"
  echo "SourceBundleKey=$SOURCE_BUNDLE_KEY"
  echo "OrchestratorImageUri=$ORCHESTRATOR_IMAGE_URI"
  echo "RuntimeImageUri=$RUNTIME_IMAGE_URI"
  echo "DockerPlatform=$DOCKER_PLATFORM"
  echo "CpuArchitecture=$CPU_ARCHITECTURE"
  echo "InstanceType=$INSTANCE_TYPE"
  echo "Builder=$BUILD_METHOD"
fi