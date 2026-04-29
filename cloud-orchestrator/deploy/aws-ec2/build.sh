#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_tests_enabled
load_state
ensure_source_bucket
ensure_artifact_keys
ensure_platform_default

tmp_dir="$(mktemp -d -t cloud-orchestrator-images.XXXXXX)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

case "$BUILD_METHOD" in
  local)
    docker build --platform "$DOCKER_PLATFORM" -t cloud-agent-runtime:aws-e2e "$ORCHESTRATOR_DIR/runtime/python" >&2
    docker save cloud-agent-runtime:aws-e2e | gzip >"$tmp_dir/cloud-agent-runtime-image.tar.gz"

    docker build --platform "$DOCKER_PLATFORM" -t cloud-orchestrator:aws-e2e "$ORCHESTRATOR_DIR" >&2
    docker save cloud-orchestrator:aws-e2e | gzip >"$tmp_dir/cloud-orchestrator-image.tar.gz"

    aws_out s3 cp "$tmp_dir/cloud-agent-runtime-image.tar.gz" "s3://${SOURCE_BUCKET}/${RUNTIME_IMAGE_KEY}" >/dev/null
    aws_out s3 cp "$tmp_dir/cloud-orchestrator-image.tar.gz" "s3://${SOURCE_BUCKET}/${ORCHESTRATOR_IMAGE_KEY}" >/dev/null
    ;;

  ec2)
    upload_source_bundle
    builder_stack="${STACK_NAME}-builder"
    builder_created=0
    cleanup_builder() {
      if [ "$builder_created" -eq 1 ]; then
        delete_stack_if_exists "$builder_stack" || true
      fi
    }
    trap cleanup_builder EXIT
    deploy_stack "$builder_stack" "$SCRIPT_DIR/builder.yaml" \
      StackName="$STACK_NAME" \
      SourceBucket="$SOURCE_BUCKET" \
      SourceBundleKey="$SOURCE_BUNDLE_KEY" \
      OrchestratorImageKey="$ORCHESTRATOR_IMAGE_KEY" \
      RuntimeImageKey="$RUNTIME_IMAGE_KEY" \
      InstanceType="$BUILDER_INSTANCE_TYPE" \
      CpuArchitecture="$CPU_ARCHITECTURE"
    builder_created=1

    builder_instance_id="$(stack_output "$builder_stack" BuilderInstanceId)"
    ssm_params="$tmp_dir/build-command.json"
    python3 - "$ssm_params" "$SOURCE_BUCKET" "$SOURCE_BUNDLE_KEY" "$RUNTIME_IMAGE_KEY" "$ORCHESTRATOR_IMAGE_KEY" "$REGION" "$DOCKER_PLATFORM" <<'PY'
import json
import sys

path, bucket, source_key, runtime_key, orchestrator_key, region, platform = sys.argv[1:8]
commands = [
    "set -euxo pipefail",
    "dnf install -y docker awscli tar gzip",
    "systemctl enable --now docker",
    "rm -rf /opt/cloud-orchestrator && mkdir -p /opt/cloud-orchestrator /tmp/cloud-orchestrator-build",
    f"aws s3 cp s3://{bucket}/{source_key} /tmp/cloud-orchestrator-source.tar.gz --region {region}",
    "tar -xzf /tmp/cloud-orchestrator-source.tar.gz -C /opt/cloud-orchestrator",
    f"docker build --platform {platform} -t cloud-agent-runtime:aws-e2e /opt/cloud-orchestrator/runtime/python",
    "docker save cloud-agent-runtime:aws-e2e | gzip > /tmp/cloud-orchestrator-build/cloud-agent-runtime-image.tar.gz",
    f"docker build --platform {platform} -t cloud-orchestrator:aws-e2e /opt/cloud-orchestrator",
    "docker save cloud-orchestrator:aws-e2e | gzip > /tmp/cloud-orchestrator-build/cloud-orchestrator-image.tar.gz",
    f"aws s3 cp /tmp/cloud-orchestrator-build/cloud-agent-runtime-image.tar.gz s3://{bucket}/{runtime_key} --region {region}",
    f"aws s3 cp /tmp/cloud-orchestrator-build/cloud-orchestrator-image.tar.gz s3://{bucket}/{orchestrator_key} --region {region}",
]
with open(path, "w", encoding="utf-8") as f:
    json.dump({"commands": commands}, f)
PY
    command_id="$(aws_out ssm send-command \
      --instance-ids "$builder_instance_id" \
      --document-name AWS-RunShellScript \
      --parameters "file://$ssm_params" \
      --timeout-seconds 3600 \
      --query Command.CommandId \
      --output text)"
    wait_ssm_command "$command_id" "$builder_instance_id" 3600
    status="$(aws_out ssm get-command-invocation --command-id "$command_id" --instance-id "$builder_instance_id" --query Status --output text)"
    if [ "$status" != "Success" ]; then
      aws_out ssm get-command-invocation --command-id "$command_id" --instance-id "$builder_instance_id" --query StandardErrorContent --output text >&2 || true
      exit 1
    fi
    delete_stack_if_exists "$builder_stack"
    builder_created=0
    trap cleanup EXIT
    ;;

  *)
    echo "Unsupported builder: $BUILD_METHOD" >&2
    exit 2
    ;;
esac

save_state

if [ "$JSON_OUTPUT" -eq 1 ]; then
  printf '{"sourceBucket":"%s","orchestratorImageKey":"%s","runtimeImageKey":"%s","dockerPlatform":"%s","cpuArchitecture":"%s","instanceType":"%s","builder":"%s","stackName":"%s","region":"%s"}\n' \
    "$SOURCE_BUCKET" "$ORCHESTRATOR_IMAGE_KEY" "$RUNTIME_IMAGE_KEY" "$DOCKER_PLATFORM" "$CPU_ARCHITECTURE" "$INSTANCE_TYPE" "$BUILD_METHOD" "$STACK_NAME" "$REGION"
else
  echo "SourceBucket=$SOURCE_BUCKET"
  echo "OrchestratorImageKey=$ORCHESTRATOR_IMAGE_KEY"
  echo "RuntimeImageKey=$RUNTIME_IMAGE_KEY"
  echo "DockerPlatform=$DOCKER_PLATFORM"
  echo "CpuArchitecture=$CPU_ARCHITECTURE"
  echo "InstanceType=$INSTANCE_TYPE"
  echo "Builder=$BUILD_METHOD"
fi